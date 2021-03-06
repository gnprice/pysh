'''
Usage:
  py.test pysh/cmd.py

'''

import codecs
import io
import subprocess

from pysh.words import shwords


class pysh:
    # Absurd hack to get the same names `pysh.filter` etc. below
    # as in normal pysh-using code.
    from .filters import filter, input, output, argument, option
    from .filters import slurp


def chunks(f: io.BufferedReader):
    '''Generator for the contents of `f`, yielding once per underlying read.'''
    # py36: Before Python 3.7, io.BufferedReader.read1 requires a size
    #   argument.  Just pass explicitly the default from 3.7+.
    chunk = f.read1(8192)
    while chunk:
        yield chunk
        chunk = f.read1(8192)


def chunks_text(f: io.TextIOBase):
    # Awkwardly seem to lack read1().  Use readline() because many
    # writers will write a line at a time... and use a max size, too.
    chunk = f.readline(8192)
    while chunk:
        yield chunk
        chunk = f.readline(8192)


@pysh.filter
@pysh.input(type='stream', required=False)
@pysh.output(type='stream', required=False)
def devnull(input, output):
    '''
    Ignore any input, and provide nothing as output.

    This corresponds to a shell redirection from or to ``/dev/null``.
    In particular:

    * a shell command like ``… </dev/null`` corresponds to a Pysh
      pipeline ``cmd.devnull() | …``;
    * a shell command like ``… >/dev/null`` corresponds to a Pysh
      pipeline ``… | cmd.devnull()``.
    '''
    if output is not None:
        output.close()

    if input is not None:
        for _ in chunks(input):
            pass


@pysh.filter
# input none
@pysh.output(type='stream')
@pysh.argument(n='*', type=bytes)
@pysh.option(' /-n', type=bool)
def echo(output, *words, ln=True):
    '''
    Write the given *words* to the output.

    The words are separated by blanks ``b' '``.  If *ln* is true (the
    default), a newline ``b'\\n'`` follows at the end.

    This corresponds to the Unix command ``echo``, with ``ln=False``
    corresponding to ``echo -n``.

    For example:

    >>> pysh.to_stdout( cmd.echo(b'hello', b'world') )
    hello world
    '''
    output.write(b' '.join(words)
                 + (b'\n' if ln else b''))


@pysh.filter
# input none
@pysh.output(type='stream')
@pysh.argument(n='*', type='filename')
def cat(output, *filenames):
    '''
    Read each of the given files in turn, and output their contents.

    This is very similar to the Unix command ``cat``, but with fewer
    features:

    * The filenames are never interpreted as options; they're simply
      filenames.
    * The filename ``-``, or an empty list of filenames, are not
      special; instead of reading from stdin, they cause reading from
      a file named ``-``, and an empty output, respectively.
    '''
    for filename in filenames:
        with open(filename, 'rb') as f:
            for chunk in chunks(f):
                output.write(chunk)


@pysh.filter
@pysh.input(type='stream')
@pysh.output(type='tstream')
def decode(input, output):
    # TODO tests
    for chunk in codecs.iterdecode(chunks(input), 'utf-8'):
        output.write(chunk)


@pysh.filter
@pysh.input(type='tstream')
@pysh.output(type='stream')
def encode(input, output):
    # TODO tests
    for chunk in codecs.iterencode(chunks_text(input), 'utf-8'):
        output.write(chunk)


@pysh.filter
@pysh.input(type='stream')
@pysh.output(type='iter')
def splitlines(input):
    '''
    Split the input stream into an iterator of lines.

    The meaning of "line" follows the standard Unix convention:

    * Each newline byte (``b'\\n'``) terminates a line.
    * If there are any bytes after the last newline, they
      form one last line.

    This is also the same behavior as Python's :meth:`bytes.splitlines`,
    except that only ``b'\\n'`` counts as a newline: ``b'\\r'`` is
    treated the same as any other byte.
    '''
    # Future feature: options like delim=b'\0'
    delimiter = b'\n'
    fragment = b''
    for chunk in chunks(input):
        assert chunk
        pieces = chunk.split(delimiter)
        assert pieces
        # There are `len(pieces) - 1` newlines in `chunk`.
        if len(pieces) == 1:
            fragment += pieces[0]
        else:
            yield fragment + pieces[0]
            yield from pieces[1:-1]
            fragment = pieces[-1]
    if fragment:
        yield fragment


def has_fileno(f: io.IOBase) -> bool:
    try:
        f.fileno()
        return True
    except io.UnsupportedOperation:
        return False


@pysh.filter
@pysh.input(type='stream', required=False)
@pysh.output(type='stream')
@pysh.argument()
@pysh.argument(n='*')
def run(input, output, fmt, *args, _check=True, _stderr=None):
    '''
    Run the given external command, as a pipeline filter.

    Like any filter, the return value of ``cmd.run()`` only has an
    effect when a pipeline containing it is run by a function like
    `.slurp()` or `.to_stdout()`.  When run:

    * The given *fmt* and *\*args* are interpreted by `.shwords()` to
      produce a command line.

    * The command line is executed (using :class:`subprocess.Popen`),
      with stdin and stdout connected to the filter's input and output
      in the pipeline.  Input is optional.

    * The external command's stderr can be controlled with *_stderr*,
      using values `None`, :data:`pysh.DEVNULL`, or `pysh.STDOUT`.

    * If *_check* is true (the default), an exception is raised on
      failure just like `.check_cmd()`.  Otherwise, the
      external command's return code is ignored.

    **NOTE**: In the current implementation, the input may be read
    completely into a buffer before any of it is passed to the
    external command.  This is just fine for lots of scripts, but will
    be fixed before Pysh 1.0.  If you have a use case where this
    matters, please file an issue, to help prioritize fixing it.
    '''

    cmd = shwords(fmt, *args)

    assert input is None or isinstance(input, io.IOBase)
    assert isinstance(output, io.IOBase)

    stdin = (subprocess.DEVNULL if input is None
             else input if has_fileno(input)
             else subprocess.PIPE)
    stdout = (output if has_fileno(output)
              else subprocess.PIPE)

    # Compare subprocess.run and Popen.communicate, in cpython:Lib/subprocess.py.
    proc = subprocess.Popen(
            cmd,
            stdin=stdin,
            stdout=stdout,
            stderr=_stderr,
    )
    if input is None:
        # Simplify in the case where no interleaved I/O is necessary.
        # This mirrors what Popen.communicate does, except with a `.read()`
        # expanded to pipeline chunks.
        if stdout == subprocess.PIPE:
            for chunk in chunks(proc.stdout):
                output.write(chunk)
            proc.stdout.close()
        proc.wait()
    else:
        # TODO this just exhausts our input, then starts passing it on.
        #
        # This won't do for a full solution; but it's plenty for replacing
        # lots of shell scripts, where the data handled in pipes is not too
        # many kilobytes.
        inbuf = input.read() if stdin == subprocess.PIPE else None
        outbuf, _ = proc.communicate(inbuf)
        if stdout == subprocess.PIPE:
            output.write(outbuf)

    if _check:
        retcode = proc.returncode
        if retcode:
            raise subprocess.CalledProcessError(retcode, cmd)


# TODO -- Features needed for translating everyday shell scripts without bloat.
#  [x] CLI parsing (use Click)
#  [x] pipelines, with split
#  [x] shwords
#  [x] run
#  [x] slurp
#  [x] shwords for lists: `{!@}`
#  [x] `run` accept input
#  [x] `echo` builtin: `echo "$foo" | ...`
#  [ ] `join` inverse of `split`
#  [x] redirect `2>/dev/null` and `2>&`; perhaps e.g.
#      `cmd.run(..., _stderr=cmd.DEVNULL)` (and let other kwargs
#      go to shwords)?
#  [ ] globs (check if stdlib glob is enough)
#
# Nice to have:
#  [ ] async
#  [ ] maybe some sugar for functions like this:
#        run() { lxc-attach -n "$CONTAINER_NAME" -- "$@"; }
#      Already not too hard to write with `shwords` and `{!@}`, though.
#  [ ] test operators? -f -d -r -x, maybe a few more
