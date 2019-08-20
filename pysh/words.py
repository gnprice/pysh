import re
import _string
import sys


def get_field(field_name, args, kwargs):
    # Corresponds to string.Formatter.get_field in the stdlib.

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
  '''
  Split format_string, then format using args and kwargs, producing a list.

  Handy for producing the command line for invoking an external
  program, conveniently but without the complex gotchas of
  shell parsing.  For example:

  >>> shwords('rm -rf /tmp/{userdoc}', userdoc='1 .. 2')
  ['rm', '-rf', '/tmp/1 .. 2']

  The `format_string` is split on spaces.  Each word is then formatted
  through a minilanguage similar to `str.format`.  Each word of
  `format_string` produces exactly one item in the result (unless
  explicitly instructed otherwise with `{!@}`), regardless of the
  contents of the interpolated values.

  The formatting minilanguage is exactly the same as for `str.format`,
  except:

  * An additional conversion `!@`, as in `{!@}`.  This must appear in
    format_string as a whole word.  The argument must be an iterable,
    and each element of the iterable becomes an element in the result.

  * The conversions `!r` and `!a` are omitted, because they only make
    sense within a Python context.

  * No nested interpolation, as in `{:{}}`.
  '''
  # This implementation is closely based on `string.Formatter` in the
  # stdlib, particularly the `vformat` method; but modified to make
  # the customizations we need.
  #
  # One salient change is that to get more control of the loop,
  # instead of using `_string.formatter_parser` we drive it ourselves
  # using the regexes above, some of which are distilled from the
  # C code that implements that function.

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
