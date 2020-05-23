# Pysh

Pysh is a library for running external commands from a Python program,
with the usual concision and clarity that Python achieves in other domains.

The problem Pysh aims to solve is:

* Python is in general excellent for writing code that cleanly says
  what one means to say, without a bunch of excess ceremony or
  boilerplate.

* Yet when it comes to invoking external programs, passing
  command-line arguments, and consuming their output or wiring them up
  in pipelines, the usual Python code for it feels verbose and complex
  compared to a shell script.

  As a result, even in 2020 many of us continue to routinely write
  shell scripts.

* Pysh seeks to match the concision and power of the shell, in its
  domain -- while keeping all the clarity and robustness that's
  possible to achieve in a modern programming language like Python.


## Installing

The library is [`pysh-lib`](https://pypi.org/project/pysh-lib/) on
PyPI.  You can install it with a command like:
```
$ pip install --user pysh-lib
```

Pysh supports Python 3.6+.


## Usage

Simple commands are simple:

    from pysh import check_cmd, try_cmd

    check_cmd('gpg --decrypt --output {} {}', cleartext_path, cryptotext_path)

    if not try_cmd('git diff-index --quiet HEAD'):
        raise RuntimeError("worktree not clean")

    repo_root = slurp_cmd('git rev-parse --show-toplevel')
    # "slurp" strips trailing newlines, just like shell `$(...)`

### Writing command lines

Command lines offer a `format`-like minilanguage, powered by
`pysh.shwords`.  The format string is automatically split to form the
command's list of arguments, providing shell-script-like
convenience...  but the interpolated data never affects the split,
avoiding classic shell-script bugs.

    from pysh import shwords, check_cmd

    shwords('rm -rf {tmpdir}/{userdoc}', tmpdir='/tmp', userdoc='1 .. 2')
    # -> ['rm', '-rf', '/tmp/1 .. 2']

    check_cmd('rm -rf {tmpdir}/{userdoc}', tmpdir='/tmp', userdoc='1 .. 2')
    # removes `/tmp/1 .. 2` -- not `/tmp/1`, `..`, and `2`

A format-minilanguage extension `{...!@}` substitutes in a whole list:

    check_cmd('grep -C2 TODO -- {!@}', files)

Each function taking a command line also has a twin, named with `_f`,
that opts into f-string-like behavior:

    from pysh import check_cmd, check_cmd_f

    check_cmd_f('{compiler} {cflags!@} -c {source_file} -o {object_file}')

    # equivalent to:
    check_cmd('{} {!@} -c {} -o {}',
              compiler, cflags, source_file, object_file)

### Pipelines

Pipelines are composed with the `|` operator.  Each stage (or
"filter") in the pipeline can be an external command, or Python code.

Most often pipelines are built from the filters offered in the
`pysh.cmd` module.  You can consume the output with `pysh.slurp`:

    import pysh
    from pysh import cmd

    hello = pysh.slurp(cmd.echo(b'hello world')
                       | cmd.run('tr h H'))
    # -> b'Hello world'

Or iterate through it:

    for commit_id in (cmd.run('git rev-list -n10 -- {!@}', files)
                      | cmd.splitlines()):
        # ... gets last 10 commits touching `files`

You can also write filters directly, using the `@pysh.filter`
decorator.  See examples in the `example/` tree.  This is also the same
API that all the filters in `pysh.cmd` are built on, so there are many
examples there.


## Examples

For some small demos, on real scripts originally written in Bash, see
the [`example/`](example/) directory.

The implementation, in `pysh/`, also contains many small examples in
the form of unit tests.  To run the unit tests (as well as tests of
the `example/` demos), simply run [pytest]:
```
$ pytest -q
............                                                             [100%]
12 passed in 0.39 seconds
```

[pytest]: https://docs.pytest.org/


## Further ambitions: Pysh, a new shell

Pysh works great today for writing full scripts.  One strength of the
shell which Pysh does not currently match is that it can be the same
language you use for everyday interactive commands -- which means you
can build up a script from commands you run at the interactive prompt,
and conversely you can take fragments of a script and more or less
copy-paste them to your shell prompt to run them ad hoc.

In the future we hope to extend Pysh to provide an interactive shell
too.  A design sketch for this can be found in
[`doc/shell-design.md`](doc/shell-design.md):

> Pysh is a new shell that scales smoothly from everyday interactive
> commands as short as `ls` through 300-character "one-liners" as
> conveniently as Bash, and up through many-KLoC programs with the
> robustness of a modern programming language.

See [`doc/shell-design.md`](doc/shell-design.md) for many more details
on design and (hypothetical!) implementation.

The core of this hypothetical new shell is Python: it runs by
transforming to Python bytecode, and its syntax for scripts is Python
with certain extensions.

The name "Pysh" stems from this vision.

In any case Pysh will always support being used as a pure Python
library, as it does today.


## Contributing

If this challenge sounds interesting or important to you, please try
the `pysh` library, read the full-blown-shell [design doc](doc/shell-design.md),
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
