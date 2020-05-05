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


## `pysh`, the Python library

One thread of this work is an experimental -- but working! --
Python library that aims to meet our challenge for pure Python
scripts, as far as that's possible.

Most of the ideas needed for this, and even most of the code, will
also be required for a full-blown Pysh shell like the design discussed
below; so this also serves as a way to experiment on that design.

The `pysh` library works today, though there are further features that
would be useful and interesting to add.  For some small demos, on real
scripts originally written in Bash, see the [`example/`](example/)
directory.

The implementation, in `pysh/`, also contains many small examples in
the form of unit tests.  To run the unit tests (as well as tests of
the `example/` demos), simply run [pytest]:
```
$ pytest -q
............                                                             [100%]
12 passed in 0.39 seconds
```

[pytest]: https://docs.pytest.org/


### Usage

See detailed usage and examples in [`pysh/README.md`](pysh/README.md).


### Installing

The library is [`pysh-lib`](https://pypi.org/project/pysh-lib/) on
PyPI.  You can install it with a command like:
```
$ pip install --user pysh-lib
```

Pysh requires Python 3.6+.


## Pysh, the design sketch of a new shell

Another thread of this work is in [`design.md`](design.md).  This is a
speculative design sketch for an attempt to meet our challenge across
its full range, including everyday interactive use:

> Pysh is a new shell that scales smoothly from everyday interactive
> commands as short as `ls` through 300-character "one-liners" as
> conveniently as Bash, and up through many-KLoC programs with the
> robustness of a modern programming language.

See [`design.md`](design.md) for many more details on design and
(hypothetical!) implementation.

The core of this hypothetical new shell is Python: it runs by
transforming to Python bytecode, and its syntax for scripts is Python
with certain extensions.

The name "Pysh" stems from this vision.


## Trying it and contributing

If this challenge sounds interesting or important to you, please try
the `pysh` library, read the full-blown-shell [design doc](design.md),
and send us your feedback!

We're especially interested in hearing about your experience trying to
use `pysh` in scripts.  Take a look at the demo scripts in
[`example/`](example/); then look at some script of your own, or an
interesting small piece of one, and try converting it to use `pysh`.
* How does it compare to the original?
* What patterns are awkward to express in `pysh`?
* What patterns do you not see a good way to express?

Let us know in a GitHub issue, or send mail to Greg Price at
gnprice-at-gmail.com.

Remember this is experimental software: expect to find bugs, and
expect the API to change with future development.

When you do find a bug, or especially if there are roadblocks or rough
edges that get in the way of you even trying it, please let us know --
either an issue or a PR is very welcome.
