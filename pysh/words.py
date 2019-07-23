import re
import _string
import sys


def get_field(field_name, args, kwargs):
    first, rest = _string.formatter_field_name_split(field_name)

    obj = args[first] if isinstance(first, int) else kwargs[first]

    for is_attr, i in rest:
        if is_attr:
            obj = getattr(obj, i)
        else:
            obj = obj[i]

    return obj


PAT_SPACE = re.compile(r' +')
PAT_SPACE_OR_END = re.compile(r' +|\Z')

# Based on MarkupIterator_next in cpython:Objects/stringlib/unicode_format.h.
PAT_LITERAL = re.compile(r'(?: [^{}] | \{\{ | \}\} )*', re.X)

# Based on parse_field in cpython:Objects/stringlib/unicode_format.h.
PAT_MARKUP = re.compile(
  r'''\{
         (?P<field_name>  (?: [^[{}:!] | \[ [^]]* \] )* )
         (?: \! (?P<conversion> [^:}] ) )?
         (?P<format_spec> (?: : [^{}]* )? )
      \}''', re.X)


def shwords(format_string, *args, **kwargs):
  result = []

  fmt = format_string.strip()
  pos = 0
  auto_arg_index = 0
  word = []
  while pos < len(fmt):
    match = PAT_LITERAL.match(fmt, pos)
    pos = match.end()
    literal_raw = match[0]
    if literal_raw:
      literal = literal_raw.replace('{{', '{').replace('}}', '}')
      words = PAT_SPACE.split(literal)
      word.append(words[0])
      if len(words) > 1:
        result.append(''.join(word))
        result.extend(words[1:-1])
        word.clear()
        if words[-1]:
          word.append(words[-1])

    match = PAT_MARKUP.match(fmt, pos)
    if pos < len(fmt) and not match:
      raise ValueError("bad format string: {!s} (at char {})".format(
        format_string, pos))
    while match:
      pos = match.end()
      field_name, conversion, format_spec = match.groups()

      if field_name == '':
        if auto_arg_index is False:
          raise ValueError('cannot switch from manual field '
                           'specification to automatic field '
                           'numbering')
        field_name = str(auto_arg_index)
        auto_arg_index += 1
      elif field_name.isdigit():
        if auto_arg_index:
          raise ValueError('cannot switch from manual field '
                           'specification to automatic field '
                           'numbering')
        auto_arg_index = False

      obj = get_field(field_name, args, kwargs)

      if conversion is None:
        word.append(format(obj, format_spec))
      elif conversion == 's':
        word.append(format(str(obj), format_spec))
      elif conversion == '@':
        match = PAT_SPACE_OR_END.match(fmt, pos)
        if word or (match is None):
          raise ValueError("Invalid use of {!@} not as whole words")
        pos = match.end()
        result.extend(format(item, format_spec) for item in obj)
      else:
        raise ValueError("Unknown conversion specifier {0!s}".format(conversion))

      match = PAT_MARKUP.match(fmt, pos)

  if word:
    result.append(''.join(word))
  return result


def caller_namespace(caller_depth=2):
  '''
  Get the names available in an ancestor frame, for emulating f-strings.

  This gets the ancestor's locals; but unlike actual f-strings, no
  globals, and enclosing scopes are complicated.

  By default, applies to the caller's caller; so another function can
  call this one to get at its own caller's locals.  In general, applies
  to the frame `caller_depth` many calls below itself.

  By specification this function is quite magical, and makes its
  caller quite magical.  Use responsibly.
  '''
  # TODO perhaps add globals; nonlocals seem harder but probably matter less
  return sys._getframe(caller_depth).f_locals


def shwords_f(format_string):
  '''
  Process (almost) like an f-string, but with splitting like `shwords`.

  NB unlike an f-string, only the caller's locals are available;
  not globals, and enclosing scopes are complicated.
  '''
  namespace = caller_namespace()
  return shwords(format_string, **namespace)


def test_conversions():
  import pytest
  with pytest.raises(ValueError):
    shwords('{:{}}', 1, 2)
  assert '{:{}}'.format(1, 2) == ' 1'  # by contrast

def test_multiword():
  import pytest
  assert shwords('touch {!@}', ['a', 'b']) \
    == ['touch', 'a', 'b']
  with pytest.raises(ValueError):
    shwords('a b{!@}', ['x'])
  with pytest.raises(ValueError):
    shwords('a {!@}c', ['x'])
  with pytest.raises(ValueError):
    shwords('a {!@}{}', ['b'], 'c')
  assert shwords('touch {!@} c', ['a', 'b']) \
    == ['touch', 'a', 'b', 'c']

def test_splitting():
  assert shwords('git grep {}', 'hello world') \
    == ['git', 'grep', 'hello world']
  assert shwords('{} {} {}', 'a', 'b c', 'd') \
    == ['a', 'b c', 'd']
  assert shwords('  a  {} c ', 'b') \
    == ['a', 'b', 'c']
  assert shwords('tar -C {outdir} -xzf {tarball}',
                  outdir='/path/with/spaces in it',
                  tarball='2019 Planning (final) (v2) (final final).tgz') \
                  == ['tar', '-C', '/path/with/spaces in it', '-xzf', '2019 Planning (final) (v2) (final final).tgz']

def test_within_word():
  assert shwords('git log --format={}', '%aN') \
    == ['git', 'log', '--format=%aN']
  assert shwords('{basedir}/deployments/{deploy_id}/bin/start',
                 basedir='/srv/app', deploy_id='0f1e2d3c') \
    == ['/srv/app/deployments/0f1e2d3c/bin/start']

def test_locals():
  import pytest
  l = ['a', 'b']
  assert shwords_f('touch {l!@}') \
    == ['touch', 'a', 'b']
  assert shwords_f('touch {l[1]}') \
    == ['touch', 'b']
  assert shwords_f('echo {pytest.__name__}') \
    == ['echo', 'pytest']

  # Known limitation: locals only, no globals...
  with pytest.raises(KeyError, match='sys'):
    shwords_f('echo {sys}')
  # (unlike real, compiler-assisted f-strings)
  assert f'{sys}' \
    == "<module 'sys' (built-in)>"

  # ... and enclosing scopes' locals are complicated.
  def inner1():
    with pytest.raises(KeyError):
      return shwords_f('touch {l!@}')
  inner1()
  def inner2():
    l
    assert shwords_f('touch {l!@}') \
      == ['touch', 'a', 'b']
  inner2()
  def inner3():
    nonlocal l
    assert shwords_f('touch {l!@}') \
      == ['touch', 'a', 'b']
  inner3()
