'''
Thin wrappers around `subprocess`, mainly adding `shwords`.

The basic `check_cmd` is a small convenience helper, just composing
`shwords` with `subprocess.check_call`.

Similarly, `check_cmd_f` behaves like `shwords_f` composed with
`subprocess.check_call`: it processes the command format-string much
like an f-string.

The `try_cmd` variant provides more appropriate semantics when the
command's failure is an expected condition, by returning a `bool`
for success/failure rather than raising an exception on failure.
Similarly `try_cmd_f`.

The `slurp_cmd` function and the rest of its family run a command
for its output, with `subprocess.check_output`, and strip trailing
newlines.  This matches the behavior of `$(...)` in Bash and fits
nicely with conventional semantics for Unix CLI tools.

The behavior of `slurp_cmd_f`, `try_slurp_cmd`, and
`try_slurp_cmd_f` relate to `slurp_cmd` in the same way as
`check_cmd_f`, `try_cmd`, and `try_cmd_f` do to `check_cmd`.

In short, these functions fill the following table:

    check_cmd      try_cmd
    check_cmd_f    try_cmd_f

    slurp_cmd      try_slurp_cmd
    slurp_cmd_f    try_slurp_cmd_f
'''

import subprocess
from typing import Optional

from .words import caller_namespace, shwords


# Has the same meaning for stdout/stderr arguments of these
# functions, and of cmd.run, as for subprocess.Popen.
DEVNULL = subprocess.DEVNULL

# Has the same meaning for stderr arguments of these functions,
# and of cmd.run, as for subprocess.Popen.
STDOUT = subprocess.STDOUT

# Would be easy to add this if useful, but I don't see a case
# where it would make sense to pass:
# PIPE = subprocess.PIPE


# There's some code duplication in these *_f functions, especially
# try_cmd_f and try_slurp_cmd_f.  Would be nice to refactor that
# away... but not if it makes the code significantly more complex to
# understand, and that seems hard to avoid.


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


def check_cmd_f(fmt, **kwargs) -> None:
    '''
    Just like `check_cmd`, but with `shwords_f` instead of `shwords`.

    This means `fmt` is processed much like an f-string, with access
    to the caller's locals.  See `shwords_f` for details.

    Also, unlike `check_cmd` all keyword arguments are passed straight
    through to `subprocess.check_call`.
    '''
    subprocess.check_call(
        shwords(fmt, **caller_namespace()),
        **kwargs,
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


def try_cmd_f(fmt, **kwargs) -> bool:
    '''
    Just like `check_cmd_f`, but returns success/failure rather than raise.
    '''
    try:
        subprocess.check_call(
            shwords(fmt, **caller_namespace()),
            **kwargs,
        )
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


def slurp_cmd_f(fmt, **kwargs) -> str:
    '''
    Just like `slurp_cmd`, but with `shwords_f` instead of `shwords`.

    Also, like `check_cmd_f` in contrast to `check_cmd`, all keyword
    arguments are passed straight through to `subprocess.check_output`.
    '''
    raw_output = subprocess.check_output(
        shwords(fmt, **caller_namespace()),
        **kwargs,
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


def try_slurp_cmd_f(fmt, **kwargs) -> Optional[str]:
    '''
    Just like `slurp_cmd_f`, but on failure returns None rather than raise.
    '''
    try:
        raw_output = subprocess.check_output(
            shwords(fmt, **caller_namespace()),
            **kwargs,
        )
        return raw_output.rstrip(b'\n')
    except subprocess.CalledProcessError:
        return None
