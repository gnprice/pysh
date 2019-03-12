'''
Thin wrappers around `subprocess`, mainly adding `shwords`.
'''

import subprocess
from typing import Optional

from .words import shwords


def check_cmd(fmt, *args,
              _stdin=None, _stdout=None, _stderr=None,
              _cwd=None, _timeout=None,
              **kwargs) -> None:
    '''
    Just like `subprocess.check_call`, but with `shwords`.

    The named keyword arguments are passed through, with `stdin=_stdin` etc.
    All other arguments are passed to `shwords`.
    '''
    subprocess.check_call(
        shwords(fmt, *args, **kwargs),
        stdin=_stdin,
        stdout=_stdout,
        stderr=_stderr,
        cwd=_cwd,
        timeout=_timeout,
    )


def try_cmd(fmt, *args, **kwargs) -> bool:
    '''
    Just like `check_cmd`, but returns success/failure rather than raise.
    '''
    try:
        check_cmd(fmt, *args, **kwargs)
    except subprocess.CalledProcessError:
        return False
    return True


def slurp_cmd(fmt, *args,
              _stdin=None, _stderr=None,
              _cwd=None, _timeout=None,
              **kwargs) -> str:
    '''
    Run the command and capture output, stripping any trailing newlines.

    Stripping trailing newlines is the same behavior as `$(...)` has
    in Bash.  It fits nicely with conventional semantics for Unix CLI tools.

    See also `pysh.filters.slurp`.
    '''
    # For reference on `$(...)` see Bash manual, 3.5.4 Command Substitution.
    raw_output = subprocess.check_output(
        shwords(fmt, *args, **kwargs),
        stdin=_stdin,
        stderr=_stderr,
        cwd=_cwd,
        timeout=_timeout,
    )
    return raw_output.rstrip(b'\n')


def try_slurp_cmd(fmt, *args, **kwargs) -> Optional[str]:
    '''
    Just like `slurp_cmd`, but on failure returns None rather than raise.
    '''
    try:
        return slurp_cmd(fmt, *args, **kwargs)
    except subprocess.CalledProcessError:
        return None
