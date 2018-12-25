import string

def shformat(format_string, *args, **kwargs):
  formatter = string.Formatter()
  result = []
  word = []
  auto_arg_index = 0

  for literal_text, field_name, format_spec, conversion in \
      formatter.parse(format_string):
    if literal_text:
      words = literal_text.split(' ')
      word.append(words[0])
      if len(words) > 1:
        result.append(''.join(word))
        word = []
        if words[-1] == '':
          words.pop()
        result.extend(words[1:])

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
          # disable auto arg incrementing, if it gets
          # used later on, then an exception will be raised
          auto_arg_index = False

      # given the field_name, find the object it references
      #  and the argument it came from
      obj, arg_used = formatter.get_field(field_name, args, kwargs)

      # do any conversion on the resulting object
      obj = formatter.convert_field(obj, conversion)

      # expand the format spec, if needed
      format_spec = formatter.vformat(format_spec, args, kwargs)

      # format the object and append to the result
      word.append(formatter.format_field(obj, format_spec))

  if word:
    result.append(''.join(word))
    return result

def test_shformat():
  assert shformat('git grep {}', 'hello world') \
    == ['git', 'grep', 'hello world']
  assert shformat('{} {} {}', 'a', 'b c', 'd') \
    == ['a', 'b c', 'd']
  assert shformat('tar -C {outdir} -xzf {tarball}',
                  outdir='/path/with/spaces in it',
                  tarball='2019 Planning (final) (v2) (final final).tgz') \
                  == ['tar', '-C', '/path/with/spaces in it', '-xzf', '2019 Planning (final) (v2) (final final).tgz']
