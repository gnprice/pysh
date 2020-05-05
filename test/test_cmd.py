import io
import os
import subprocess
from typing import List

import pytest

import pysh
from pysh import cmd


def test_pipeline():
    assert list(
        cmd.cat(b'/etc/shells') | cmd.splitlines()
        # sh { cat /etc/shells | split -l }
    ) == open('/etc/shells', 'rb').read().rstrip(b"\n").split(b"\n")

    assert (
        pysh.slurp(cmd.run('git rev-parse {}', 'dbccdbe6f~2'))
        # sh { git rev-parse ${commitish} | slurp }
    ) == b'91a20bf6b4a72f1f84b2f57cf38b3f771dd35fda'

    # Input and output optional; check nothing blows up.
    cmd.devnull()()


def test_echo():
    assert (
        pysh.slurp(cmd.echo(b'hello', b'world'))
    ) == b'hello world'


def test_decode():
    world = '\N{WORLD MAP}'.encode()
    assert pysh.slurp(
        cmd.echo(b'hello', world) | cmd.decode() | cmd.encode()
    ) == b'hello ' + world


def test_splitlines():
    def echo_splitlines(s: str) -> List[str]:
        return [item.decode() for item in
                (cmd.echo(s.encode(), ln=False)
                 | cmd.splitlines())]

    def check_splitlines(s: str, l: List[str]) -> None:
        chopped = s[:-1] if s.endswith('\n') else s
        assert echo_splitlines(s) == chopped.split('\n') == l

    check_splitlines('1', ['1'])
    check_splitlines('1\n', ['1'])
    check_splitlines('1\n\n', ['1', ''])
    check_splitlines('\n1\n\n2\n', ['', '1', '', '2'])


def test_splitlines_chunks():
    '''Manipulate chunk boundaries in `splitlines` input.'''

    class WriteChunks:
        def __init__(self, ss: List[str]) -> None:
            self.bs = [s.encode() for s in reversed(ss)]

        def read1(self, size: int = -1) -> bytes:
            if self.bs:
                return self.bs.pop()
            return b''

    def resplit(ss: List[str]) -> List[str]:
        return [item.decode() for item in
                cmd.splitlines().thunk(WriteChunks(ss), None)]

    def check_resplit(ss: List[str]) -> None:
        assert resplit(ss) == resplit([''.join(ss)])

    check_resplit(['\n', '\n'])
    check_resplit(['1', '\n'])
    check_resplit(['1', '\n', '\n'])
    check_resplit(['1\n', '\n'])
    check_resplit(['1', '\n\n'])
    check_resplit(['1', '\n', '2'])
    check_resplit(['1', '\n2'])
    check_resplit(['1\n', '2'])


def test_run():
    # (Commits in this repo's history.)
    assert list(cmd.run('git log --abbrev=9 --format={} {}', '%p', '9cdfc6d46')
                | cmd.splitlines()) \
        == [b'a515d0250', b'c90596c89', b'']

    assert (
        pysh.slurp(cmd.echo(b'hello') | cmd.run('tr h H'))
        # sh { echo hello | tr h H | slurp }
    ) == b'Hello'

    assert pysh.slurp(
        cmd.run('git log --oneline --reverse --abbrev=9')
        | cmd.run('grep -m1 {}', 'yield')
        | cmd.run('perl -lane {}', 'print $F[0]')
    ) == b'91a20bf6b'


def test_run_input_file():
    readfd, writefd = os.pipe()
    os.write(writefd, b'abc')
    os.close(writefd)
    buf = io.BytesIO()
    with os.fdopen(readfd) as f:
        cmd.run('perl -lpe print').thunk(f, buf)
    assert bytes(buf.getbuffer()) == b'abc\nabc\n'


def test_run_check():
    with pytest.raises(subprocess.CalledProcessError):
        pysh.slurp(cmd.run('false'))

    assert pysh.slurp(cmd.run('false', _check=False)) == b''


def test_run_stderr(capfd):
    # On `capfd`, see pytest docs:
    #   http://doc.pytest.org/en/latest/capture.html#accessing-captured-output-from-a-test-function

    assert list(
        cmd.run('sh -c {}', 'echo a; echo ERR >&2; echo b')
        | cmd.splitlines()
    ) == [b'a', b'b']
    assert capfd.readouterr() == ('', 'ERR\n')

    assert list(
        cmd.run('sh -c {}', 'echo a; echo ERR >&2; echo b',
                _stderr=subprocess.DEVNULL)
        | cmd.splitlines()
    ) == [b'a', b'b']
    assert capfd.readouterr() == ('', '')

    assert list(
        cmd.run('sh -c {}', 'echo a; echo ERR >&2; echo b',
                _stderr=subprocess.STDOUT)
        | cmd.splitlines()
    ) == [b'a', b'ERR', b'b']
    assert capfd.readouterr() == ('', '')
