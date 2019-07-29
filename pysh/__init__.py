
# TODO better organize to reflect style `pysh.foo` vs `from pysh import foo`

# Utilities for running external commands.
from .words import shwords  # style: from pysh import shwords
from .filters import slurp  # style: pysh.slurp
from .subprocess import (  # style: from pysh import ...
    check_cmd, check_cmd_f, slurp_cmd, slurp_cmd_f,
    try_cmd, try_cmd_f, try_slurp_cmd, try_slurp_cmd_f,
)

# Decorators for "shell builtins".
from .filters import filter, input, output, argument, option  # style: pysh....

# No `from .cmd import ...`; instead, style: from pysh import cmd
