# Pysh

This repo contains exploratory work motivated by the following
challenge:

* Python is in general excellent for writing code that cleanly says
  what one means to say, without a bunch of excess ceremony or
  boilerplate.

* Yet when it comes to invoking external programs, passing
  command-line arguments, and consuming their output or wiring them up
  in pipelines, the usual Python code for it feels verbose and complex
  compared to a shell script... let alone a "one-liner" one might type
  at an interactive shell prompt.

  As a result, even in 2019 many of us continue to routinely write
  those one-liners, as well as longer shell scripts.

* Can we get the concision and power of the shell, in its domain --
  while keeping all the clarity and robustness that's possible to
  achieve in a modern programming language like Python?


## Pysh, the design sketch of a new shell

One thread of this work is in `design.md`.  This is a speculative
design sketch for an attempt to meet our challenge across its full
range, including everyday interactive use:

> Pysh is a new shell that scales smoothly from everyday interactive
> commands as short as `ls` through 300-character "one-liners" as
> conveniently as Bash, and up through many-KLoC programs with the
> robustness of a modern programming language.

See `design.md` for many more details on design and (hypothetical!)
implementation.

The core of this hypothetical new shell is Python: it runs by
transforming to Python bytecode, and its syntax for scripts is Python
with certain extensions.

The name "Pysh" stems from this vision.


## `pysh`, the Python library

A related thread of the work is an experimental -- but working! --
Python library that aims to meet our challenge for pure Python
scripts, as far as that's possible.

Most of the ideas needed for this, and even most of the code, will
also be required for a full-blown Pysh shell; so this also serves as a
way to experiment on that design.

The `pysh` library works today, though there are further features that
would be useful and interesting to add.  For a small demo, on a real
script originally written in Bash, see the `example/` directory.

The implementation, in `src/`, also contains many small examples in
the form of unit tests.  To run the unit tests (as well as tests of
the `example/` demo), simply run [pytest]:
```
$ pytest -q
............                                                             [100%]
12 passed in 0.39 seconds
```

[pytest]: https://docs.pytest.org/


### Setup

To run the tests, you'll need
* Python 3.7+
* `pytest`
* `click`
* (possibly something I've forgotten)

You might use something like `pip3 install --user`, or set up a
virtualenv.  Automating the latter would be nice; PRs welcome.