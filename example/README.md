# Demos of `pysh` on example scripts

The files in this directory are for demonstrating how scripts using
`pysh` currently look, and for exploring what features are important.

They come in threes:

* `foo.orig`: A Bash script, originally written somewhere else to do
  some useful task unrelated to Pysh.

* `foo`: A port of `foo.orig` as a Python script using the `pysh`
  library.

* `test_foo.py` (usually): Tests for `foo`.

As we make changes to `pysh`, we update the demo scripts to match
changes in the API.  The tests help make sure the scripts remain
accurate as demos.

When `pysh` is serving a given script's use case well, the Python
version is only as much code as the Bash version or slightly more,
and each part of it is at least as easy to read.  When the Python
version is significantly longer, or the bits that do classic shell
tasks like invoking CLIs and setting up pipelines are more cumbersome
or complicated, that's an area where there's more to do.
