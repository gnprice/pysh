import re
import _string


def get_field(field_name, args, kwargs):
    first, rest = _string.formatter_field_name_split(field_name)

    obj = args[first] if isinstance(first, int) else kwargs[first]

    for is_attr, i in rest:
        if is_attr:
            obj = getattr(obj, i)
        else:
            obj = obj[i]

    return obj


def shwords(format_string, *args, **kwargs):
  result = []
  word = []
  auto_arg_index = 0
  after_list = False

  for literal_text, field_name, format_spec, conversion in \
      _string.formatter_parser(format_string.strip()):
    if after_list:
      after_list = False
      if not literal_text.startswith(' '):
        raise ValueError("Invalid use of {!@} not as whole words")
      literal_text = literal_text.lstrip(' ')

    if literal_text:
      words = re.split(' +', literal_text)
      word.append(words[0])
      if len(words) > 1:
        result.append(''.join(word))
        result.extend(words[1:-1])
        word.clear()
        if words[-1]:
          word.append(words[-1])

    # This is largely cribbed from cpython Formatter.vformat in
    # cpython:Lib/string.py
    if field_name is not None:
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
        if word:
          raise ValueError("Invalid use of {!@} not as whole words")
        result.extend(format(item, format_spec) for item in obj)
        after_list = True
      else:
        raise ValueError("Unknown conversion specifier {0!s}".format(conversion))

  if word:
    result.append(''.join(word))
  return result


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
