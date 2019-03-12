'''
Thin wrappers around `subprocess`, mainly adding `shwords`.
'''

import subprocess

from .words import shwords


def check_cmd(fmt, *args,
              _stdin=None, _stdout=None, _stderr=None,
              _cwd=None, _timeout=None,
              **kwargs):
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
