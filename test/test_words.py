import sys

import pytest

from pysh import shwords, shwords_f


def test_conversions():
  with pytest.raises(ValueError):
    shwords('{:{}}', 1, 2)
  assert '{:{}}'.format(1, 2) == ' 1'  # by contrast


def test_multiword():
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
