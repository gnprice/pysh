'''
Usage:
  py.test pysh/cmd.py

'''

import io
import subprocess

from pysh.words import shwords


class pysh:
    # Absurd hack to get the same names `pysh.filter` etc. below
    # as in normal pysh-using code.
    from .filters import filter, input, output, argument, option


def chunks(f: io.BufferedReader):
    '''Generator for the contents of `f`, yielding once per underlying read.'''
    chunk = f.read1()
    while chunk:
        yield chunk
        chunk = f.read1()


@pysh.filter
@pysh.input(type='stream', required=False)
@pysh.output(type='stream', required=False)
def devnull(input, output):
    if output is not None:
        output.close()

    if input is not None:
        for _ in chunks(input):
            pass


@pysh.filter
# input none
@pysh.output(type='stream')
@pysh.argument(n='*', type=bytes)
def echo(output, *words):
    output.write(b' '.join(words) + b'\n')


@pysh.filter
# input none
@pysh.output(type='stream')
@pysh.argument(n='*', type='filename')
def cat(output, *filenames):
    for filename in filenames:
        with open(filename, 'rb') as f:
            for chunk in chunks(f):
                output.write(chunk)


@pysh.filter
@pysh.input(type='stream')
@pysh.output(type='iter')
@pysh.option('-l', '--lines', type=bool)
def split(input, *, lines=False):
    delimiter = b'\n' if lines else None
    fragment = b''
    for chunk in chunks(input):
        assert chunk
        pieces = chunk.split(delimiter)
        if len(pieces) == 1:
            fragment += pieces[0]
        else:
            yield fragment + pieces[0]
            yield from pieces[1:-1]
            fragment = pieces[-1]
    if fragment:
        yield fragment


@pysh.filter
@pysh.input(type='stream')
@pysh.output(type='bytes')
def read(input):
    # Bash deletes trailing newlines from output in `$(...)`.
    # See manual, 3.5.4 Command Substitution.
    return input.read().rstrip(b'\n')


@pysh.filter
@pysh.input(type='stream', required=False)
@pysh.output(type='stream')
@pysh.argument()
@pysh.argument(n='*')
def run(input, output, fmt, *args):
    cmd = shwords(fmt, *args)
    if input is None:
        # Simplify in the case where no interleaved I/O is necessary.
        # Compare subprocess.run and Popen.communicate, in cpython:Lib/subprocess.py.
        with subprocess.Popen(
                cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE) as proc:
            # This mirrors what Popen.communicate does, except with a `.read()`
            # expanded to pipeline chunks.
            for chunk in chunks(proc.stdout):
                output.write(chunk)
            proc.stdout.close()
            retcode = proc.wait()
    else:
        with subprocess.Popen(
                cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE) as proc:
            # TODO this just exhausts our input, then starts passing it on.
            inbuf = input.read()
            outbuf, _ = proc.communicate(inbuf)
            output.write(outbuf)
            retcode = proc.returncode
    if retcode:
        raise subprocess.CalledProcessError(retcode, cmd)


# TODO -- Features needed for translating everyday shell scripts without bloat.
#  [x] CLI parsing (use Click)
#  [x] pipelines, with split
#  [x] shwords
#  [x] run
#  [x] read
#  [x] shwords for lists: `{!@}`
#  [x] `run` accept input
#  [x] `echo` builtin: `echo "$foo" | ...`
#  [ ] `join` inverse of `split` (as `echo` is to `read`)
#  [ ] redirect `2>/dev/null` and `2>&`; perhaps e.g.
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


def test_pipeline():
    from . import cmd

    assert list(
        cmd.cat(b'/etc/shells') | cmd.split(lines=True)
        # sh { cat /etc/shells | split -l }
    ) == open('/etc/shells', 'rb').read().rstrip(b"\n").split(b"\n")

    assert (
        (cmd.run('git rev-parse {}', 'dbccdbe6f~2') | cmd.read())()
        # sh { git rev-parse ${commitish} | read }
    ) == b'91a20bf6b4a72f1f84b2f57cf38b3f771dd35fda'

    # Input and output optional; check nothing blows up.
    cmd.devnull()()


def test_echo():
    from . import cmd
    assert (
        (cmd.echo(b'hello', b'world') | cmd.read())()
    ) == b'hello world'


def test_run():
    from . import cmd

    # (Commits in this repo's history.)
    assert list(cmd.run('git log --abbrev=9 --format={} {}', '%p', '9cdfc6d46')
                | cmd.split(lines=True)) \
        == [b'a515d0250', b'c90596c89', b'']

    assert (
        (cmd.echo(b'hello') | cmd.run('tr h H') | cmd.read())()
        # sh { echo hello | tr h H | read }
    ) == b'Hello'

    assert (
        (cmd.run('git log --oneline --reverse')
         | cmd.run('grep -m1 {}', 'yield')
         | cmd.run('perl -lane {}', 'print $F[0]')
         | cmd.read())()
    ) == b'91a20bf6b'
