Pysh is a library for running external commands from a Python program,
with the usual concision and clarity that Python achieves in other domains.

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
    # removes `/tmp/1 .. 2`... not `/tmp/1`, `..`, and `2`

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
decorator.  See examples in the `example/` tree; this is also the same
API that all the filters in `pysh.cmd` are built on, so there are many
examples there.

