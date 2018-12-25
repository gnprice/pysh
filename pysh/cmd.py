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
# input none
@pysh.output(type='stream')
@pysh.argument()
@pysh.argument(n='*')
def run(output, fmt, *args):
    cmd = shwords(fmt, *args)
    # Compare subprocess.run and Popen.communicate, in cpython:Lib/subprocess.py.
    with subprocess.Popen(
            cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE) as proc:
        # This mirrors what Popen.communicate does, except with a `.read()`
        # expanded to pipeline chunks.
        for chunk in chunks(proc.stdout):
            output.write(chunk)
        proc.stdout.close()
        retcode = proc.wait()
        if retcode:
            raise subprocess.CalledProcessError(retcode, cmd)


def test_pipeline():
    from . import cmd

    pipeline = cmd.cat(b'/etc/shells') | cmd.split(lines=True)
    #        = sh { cat /etc/shells | split -l }
    assert list(pipeline) \
        == open('/etc/shells', 'rb').read().rstrip(b"\n").split(b"\n")


def test_run():
    from . import cmd
    # (Commits in this repo's history.)
    assert list(cmd.run('git log --abbrev=9 --format={} {}', '%p', '9cdfc6d46')
                | cmd.split(lines=True)) \
        == [b'a515d0250', b'c90596c89', b'']
