'''
Demo usage:
  python3.7 -c 'import pysh.cmd; pysh.cmd.test_pipeline()'
OR
  py.test pysh/cmd.py

'''

import io


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


def test_pipeline():
    from pprint import pprint

    from . import cmd

    pipeline = list(
        cmd.cat(b'/etc/shells') | cmd.split(lines=True)
        # sh { cat /etc/shells | split -l }
    )
    assert pipeline == open('/etc/shells', 'rb').read().rstrip(b"\n").split(b"\n")
