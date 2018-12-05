# Pysh

## Status

This is a sketch of a design of a possible prototype.  We consider it
an open problem whether a point exists in the design space that meets
the described constraints.

Parts of this document may take the authoritative tone of a
specification or a reference manual.  These should be read as you
would read a work of science fiction.


## Goals / Principles

Pysh is a new shell that scales smoothly from everyday interactive
commands as short as `ls` through 300-character "one-liners" as
conveniently as Bash, and up through many-KLoC programs with the
robustness of a modern programming language.

Principles include:

* The syntax is regular enough to make it easily predictable whether a
  given fragment of a command will provide a literal string,
  substitute a variable's value, or execute code.
* Simple commands are simple: `ls -l src/*.c` requires as little
  ceremony as in Bash.
* ...


Design choices include:

* The shell's execution model is Python, working with Python objects:
  a Pysh variable can hold a dict mapping strings to lists, and a Pysh
  function can return a list of strings, just like Python variables
  and functions.
* A Pysh command can embed fragments of code in a variant of Python,
  called Shython; and conversely, a Shython expression can embed Pysh.
* ...


## Shython

Shython is based on Python 3.7, with its syntax extended in a small
number of ways.

 * The big one: in addition to all the usual forms from Python, a
   Shython expression may be a *Pysh escape*, written `sh { ... }`
   where the braces enclose a Pysh term.  When this expression is
   evaluated, the Pysh term is executed and its output returned, much
   like `subprocess.check_output()`.

   *(Rough.)* More generally, a Pysh escape may have the form
   `sh(**kwds) { ... }`; the plain `sh { ... }` form is equivalent to
   `sh() { ... }`.  The accepted keyword arguments are similar to
   those accepted by `subprocess`: e.g. `stderr`, `timeout`, `check`.

 * Small but important: in addition to the usual indentation-based
   syntax for closing a block (for control flow, function definition,
   etc.), a block may be closed with a keyword `end`, placed
   syntactically like a statement in the block.
   
   Combined with Python's existing use of semicolon `;` as an
   alternative to a newline for separating statements, this makes the
   full range of Python's semantics available in a one-liner, which is
   important in interactive use.
   
   `... | py -l { try: ...; end; except: ... }`

   *(Ideally these would be pure "syntax extensions" in the sense that
   every syntactically-valid Python program parses as a Shython
   program with the exact same meaning.  The `sh { ... }` should meet
   that, but `end` doesn't.  Maybe double-semicolon `;;` instead?)*

   *(For a `try` block in particular, maybe even the `end` should be
   optional?  Unlike with `if/if/else` where either `if` could go
   without an `else`, where there's a `try` there must be a coming
   `except` or `finally`, so `except` closing a `try` block is
   unambiguous.)*

Shython is implemented by a modified version of CPython's parser,
generating bytecode to run on the unmodified CPython interpreter.
Shython programs where no Shython-specific syntax appears produce
exactly the same bytecode as by CPython.

*(Or maybe something ends up requiring us to make some changes to the
actual runtime part.  But holding the line on that would have a lot of
value, in being able to successfully reuse Python libraries in a
Pysh/Shython script.)*


## Pysh

### High-level structure

A Pysh program is made up of *commands*.  These are composed via a
variety of control-flow and data-flow constructs, for which the atomic
unit is a *simple command*.

Simple commands, in turn, are built out of *expressions*.  To execute
a simple command, the expressions are evaluated and their values used
to construct a list of strings.  This list is used as the name and
arguments of a program to run, or a shell function or builtin.


### Expressions

*(Correspond roughly to Bash "words".)*

An *expression* ultimately corresponds to a Shython (or Python)
expression, and is used to produce a list of strings.

The concrete syntax of Pysh expressions is optimized for
zero to low overhead in the simple cases ubiquitous in shell use --
`git` is a string literal, and `$file` a variable reference -- and
understandable structure in complex cases.

Expressions have the following forms:

* A *literal*, e.g. `ls`: a string consisting only of a certain set
  of characters (at least `[a-zA-Z0-9./_-]`; excluding at least
  `[][~$* \t\n'\\]`; ?? others) can be written as itself, with no
  quoting.  An arbitrary string can be written by backslash-escaping
  characters otherwise disallowed.
  * Non-alphanumeric characters may be backslash-escaped even if
    otherwise allowed, just as in Perl regexes.

* A *quoted literal*, e.g. `'hello world'`: a string enclosed in
  quotes may contain a wider range of characters without
  backslash-escaping -- notably, spaces.
  * *(?? Haven't formed a strong view yet on which of many design
    choices to take here.  This is a convenience feature whose one
    really important function, with word-splitting out of the picture,
    is to not have to type backslashes before spaces all the time; so
    lots of possible choices will work fine.)*

* A *variable reference*, e.g. `$file`: a dollar sign `$` followed by
  an identifier means a reference to the named variable.

* A *command substitution*, e.g. `$(git grep -l TODO)`: the delimiters
  `$(...)` enclose a Pysh command.  This expression is equivalent to
  the Shython expression `sh { ... }` enclosing the same command.

* A *Shython substitution*, e.g. `${foo[bar+1]}`: the delimiters
  `${...}` enclose a Shython expression.
  
  This takes the place of Bash's array references; arithmetic
  expressions; and most or all of the fancy ["parameter
  expansions"][bashman-3.5.3].

* A *glob pattern*, e.g. `src/*.[ch]`: evaluates to the list of
  matching filenames etc.

* A *tilde expression*, e.g. `~greg/foo`.  *()*

* *(?likely)* a *brace list*, e.g. `foo/bar/{baz,quux}`

*(First main gap: basic string concat like `dir/$file`.  Can always
handle with Shython substitution, and F-strings help a lot:
`${f'dir/{file}'}`.  But that example is still 7 extra characters, 3
total layers of delimiters.)*

*(Second main gap: further basic string handling like
`build/${file%.c}.o`.  Python is weak at this:
`${f'build/{file[-2]}.o'}` is much less clear.  Short of other
assistance in the language, I'd probably go back to a lot of stuff
like `$(echo $file | sed 's/\.c$//')`.  Tempted to give Shython some
special syntax for e.g. regexes.)*

[bashman-3.5.3]: https://www.gnu.org/software/bash/manual/bash.html#Shell-Parameter-Expansion


### Commands

#### Simple Commands

*(Or "command"?  Not yet clear what's the clearest way to draw the
concepts. ... Possibly "command line"?  Below I kind of want a name
for element 0 of the arglist after expansions; the Bash manual calls
that "the command itself".)*

A Pysh *simple command* is a sequence of expressions, written
separated by whitespace.

Each expression must evaluate to a list of strings, or to a value
convertible to a list of strings through one of a handful of defined
conversions:
 * A string `s` is converted to `[s]`.
 * An int `n` is converted to `[str(n)]`.
 * A value `x` which has a `__shell__` method is converted to
   `x.__shell__()`.

When a simple command is executed:
 * Each expression is evaluated, and its result converted to a list of
   strings.
 * The resulting lists are concatenated.
 * The combined list is executed in the usual fashion: element 0 is a
   program to be executed, or a shell builtin or shell function, and
   the full list is its arguments.


#### Shython Commands

A *Shython command* can appear in all the same syntactic contexts as a
simple command.  It takes the form `py [OPTS] { ... }`, where the
braces enclose a Shython block.

In general, with details varying depending on the options passed: when
this command is run, the enclosed block is executed one or more times.
It may produce values to be printed to its standard output; it may
receive its standard input as one or more local variables like `_`.

When run, a block may *produce* zero or more values in any one of the
following ways:
 * If the block consists of a single expression (and contains no
   `yield` expression), then it produces that expression's value.
 * Otherwise, the block behaves like the body of a Python function
   definition:
   * If it contains no `yield` expression, then `return` produces the
     returned value, and finishing without `return` produces `None`.
   * If it does contain a `yield`, then each `yield` produces the
     yielded value.

When a value produced by the block is printed to the command's output,
it is converted to a string as follows:
 * A string is used unmodified.
 * `None` converts to empty output (much like at a Python REPL.)
 * An int or float is converted with `str(...)`.
 * Any other value is an error.

   *(This probably needs to be more complicated... but your average
   `str` or `repr` is of little use if printed for a human and less
   than none in a pipeline, so I wouldn't want the rule to be one of
   those like it is at the REPL.  And of course you can always apply
   whatever conversion you want explicitly.)*

Execution happens as follows:

 * With no options, the block is executed once.

   If the command's stdin comes from a redirection or pipe, then the
   complete input is provided as a string in the local `_`.
   Otherwise, stdin is not read from.

   *(I don't love this rule; it feels liable to surprises.  But I also
   don't want every nontrivial Pysh script to pick up `apt`'s
   surprising behavior of eating its input even when
   noninteractive...)*

 * With `-l`/`--lines`, the block is executed once for each line in
   its input, with `_` set to the line with its newline removed.  Each
   produced value has a newline appended before printing, except that
   `None` converts to no output rather than to a blank line.
   
 * With `-0`, the "line" terminator for `-l` is a null byte, rather
   than newline.  Implies `-l`.

 * With `-a`, each line (or "line" with `-0`) is split with `.split()`
   and `_` is set to the resulting list.  Implies `-l`.
   
   *(Or maybe this is superfluous because `str.split` is right
   there?)*

 * With `-j`, the input is parsed as a sequence of JSON values, and
   the block is executed once with `_` set to each value in turn.
   Each resulting value is converted with `json.dump` in place of the
   conversions described above, followed by a newline.

   *(Overlaps a bit with `jq` which is hard to compete with, but I
   think there are cases where integration with Python -- perhaps
   especially with a surrounding Shython program -- is what's needed,
   and this beats an explicit `json.load`/`json.dump`.)*

 * *(Some analogue / better version of `perl -ne '... END { ... }'`?
   Or maybe you just take that outside the pipeline, enjoying the fact
   it's the same program inside and out.  Example below.)*

 * *(Maybe a way to name parameters?  Especially handy with `-a`.)*

 * ... *(Surely more.)*

##### Examples

* Sum up a bunch of numbers:
```
... | perl -lane 'print $F[0] if (/.../)' \
  | py { sum(_) }
```

* Aggregate some data (a bit like Perl's `END { ... }`):
```
py { d = defaultdict(0) }
... | py -al { d[_[1]] = max(d[_[1]], _[0]) }
py { for k, v in d: print(v, k) } | sort -rn | head
```

  * ... or spitballing another syntax, including some vague thoughts above:
  
```
py { d = defaultdict(0) }
... | py -al { v, k: d[k] = max(d[k], v) }
py -nl { d.items() } | sort -rnk1 | head
# here `-n` is like `jq -n`
```

  * ... or maybe you'd just write
```
py {
  d = defaultdict(0)
  sh { ... | py -al { v, k: d[k] = max(d[k], v) } }
  items = sorted(d.items(), key=lambda t: t[1])
  for k, v in items[:-11:-1]: print(v, k)
}
```


#### Data Flow Constructs

Pipelines and redirections.  These work much like in Bash.

*(The status quo seems mostly OK here.  Redirections sure could be
made less confusing, so that's an opportunity; haven't thought
concretely about how to do so.)*


#### Control Flow Constructs

If, while, case, etc.

*(Surely `case` can be improved.)*

*(Also, though strictly this is probably an expression form, `test`
aka `[` -- or was that `[[`?  A lot of that is just that `if [ -z
"$flag" ]` becomes `if ${not flag}`, etc; but `-f` and friends are
valuable and need a new or rebuilt home.)*


#### Other Important Bits

* Variable definitions/assigments need some thought.
  `py { foo = bar[baz] }` "works"... but adds up to a lot of friction
  in the source code crossing the language boundary all the time,
  unless you really push all but small bits out into Shython.

* Functions.  Pysh syntax for defining them; how they interact when
  invoked as a command.

* Bytes vs. strings.  I'm not sure Python 3's standard behavior here
  when it comes to things like filenames and command-line arguments is
  quite what we want.  There's no question of going back to Python 2...
  but given how central these are to shell programming, this deserves
  close attention and perhaps some adjustments.

* Subshells.  Glossed over in some examples above is that in Bash, a
  command participating in a pipeline runs in a forked process, even
  if it's entirely within the shell language; while we'd really like
  such commands to be able to set and mutate data outside it (in
  lexically-explicit ways, of course.)  How can we define the
  semantics?  Maybe the key will be something like that we don't make
  promises about the actual fd 0, 1, and 2, or even `sys.stdin` etc.,
  because we're handling that data flow in more Python-natural ways.


## Interactive Use

Lots of work goes here.  But I'm not sure any fundamental new ideas
are needed.


## Yet-Further Ideas

This section is even more speculative than the rest of this document.

* This design provides two languages nested inside each other: a
  slightly-modified Python, and a new shell.

  But as Andy Chu often points out, shell programs tend to have a
  number of different languages intermingled: Bash itself, which
  comprises a number of language fragments like arithmetic expressions
  and fancy parameter expansions as well as the "simple command" core;
  the regexps in `grep` and friends; `sed` or `awk` or `perl`... and a
  complex CLI like `find` is effectively yet another language, as
  almost an EDSL.

  And there are some gaps in this Python/shell pair.  They can always
  be filled with `grep`, `perl`, and the rest the same way they are in
  Bash... but perhaps we can do better?  One way of looking at what
  this design attempts to do is to let shell code live inside Python
  code, and vice versa, in a real parse tree rather than as a string
  to be re-parsed through multiple layers and require careful
  escaping.  How about providing that for some kind of regexp
  match/substitution language?

  Or even somehow for actual Perl?  Though hard to see how that could
  be done to a similar degree with the Perl not running on the same
  object model and GC etc.  (Don't think I've heard anything about
  Parrot in quite a while.)

  Or for `jq`?  Maybe some kind of generic mechanism to assist with
  integrating any language, at least at a syntactic level even if each
  command is still entirely a new process.

* Relatedly, maybe a still simpler way to escape into Shython?
  E.g. `{ ... }` is Shython, while `( ... )` is another Pysh.


## Implementation Strategy

For a prototype, Shython programs are translated source-to-source to
Python.

A modified Python parser finds `sh { ... }` blocks and handles the
syntax extensions outside them, while a freshly-written parser in a
handy modern parser framework parses Pysh, in mutual recursion.

*(??? Obviously plenty of uncertainty.  But I'm not thrilled about
pushing the CPython parser super far into fresh new territory.)*

A Pysh program is handled basically as if by wrapping it in `sh { ... }`.

A slightly fancier implementation might generate Python bytecode
instead of source.

Still fancier... well, we're not going to beat whatever's the state of
the art in Python implementations, basically by reduction.


## Concerns

Many.  Among them:

* **Startup time.**

  ```
  $ time python -c pass

  time: 0.027s wall (0.016s u, 0.008s s)

  $ time bash -c :

  time: 0.006s wall (0.000s u, 0.004s s)
  ```

  (each the median of 3 trials)

  That will escalate if sourcing kLOCs of Pysh library code, let alone
  importing a bunch of Python dependencies to help with some task.

  That 27ms beats `node` at 59ms (or `ruby`, 78ms); so there's no
  escape by switching to JavaScript, either.
