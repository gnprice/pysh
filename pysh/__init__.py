
# Utilities for running external commands.
from .words import shwords
from .filters import slurp
from .subprocess import check_cmd, slurp_cmd, try_cmd, try_slurp_cmd

# Decorators for "shell builtins".
from .filters import filter, input, output, argument, option

