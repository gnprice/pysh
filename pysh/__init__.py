
# Utilities for running external commands.
from .words import shwords
from .filters import slurp
from .subprocess import (
    check_cmd, check_cmd_f, slurp_cmd, slurp_cmd_f,
    try_cmd, try_cmd_f, try_slurp_cmd, try_slurp_cmd_f,
)

# Decorators for "shell builtins".
from .filters import filter, input, output, argument, option

