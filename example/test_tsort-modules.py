
import json
import os
import subprocess
import sys
import tempfile

import pytest

THIS_DIR=os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.dirname(THIS_DIR))

from pysh import check_cmd, slurp_cmd


# TODO dedupe with test_knit.py
@pytest.fixture
def chtempdir():
    oldcwd = os.getcwd()
    try:
        with tempfile.TemporaryDirectory() as dirname:
            os.chdir(dirname)
            yield
    finally:
        os.chdir(oldcwd)


# Together with `flow_line`, this is the fixture data.
import_graph = {
    'src/a.js': ['node_modules/thing/index.js'],
    'src/b/c.js': ['src/a.js'],
    'node_modules/thing/index.js': [],
}


flow_line = {
    'src/a.js': '/* @flow strict-local */',
    'src/b/c.js': '/* @flow */',
}


def compute_json():
    '''
    Mock output for `flow get-imports --json`, from fixture data.

    This has a few properties the script ignores; the real output
    has more.
    '''
    return dict(
        (filename, {
            'not_flow': False,
            'requirements': [
                {
                    'import': imp,
                    'path': filename,
                    'line': 123,
                }
                for imp in imports
            ]
         })
        for filename, imports in import_graph.items()
    )


@pytest.fixture
def tree(chtempdir):
    '''
    A directory tree with our fixture data and appropriate scripts.

    Contents:
    * A mocked-out `flow` command, as a script that cats a file.
    * The said file, computed from the fixture data.
    * Stub source files, with `@flow` lines for `grep` to find,
      computed also from fixture data.
    * The reference script `tsort-modules.orig`, copied into place.
    '''
    for filename, imports in import_graph.items():
        check_cmd('mkdir -p {}', os.path.dirname(filename))
        with open(filename, 'w') as f:
            print(flow_line.get(filename, ''), file=f)

    with open('imports.json', 'w') as f:
        json.dump(compute_json(), f)

    check_cmd('mkdir -p node_modules/.bin')
    with open('node_modules/.bin/flow', 'w') as f:
        f.write('#!/bin/bash\ncat imports.json\n')
    check_cmd('chmod a+x node_modules/.bin/flow')

    check_cmd('mkdir -p tools')
    check_cmd('cp -a {}/tsort-modules.orig tools/tsort-modules', THIS_DIR)


tsort_script = os.path.join(THIS_DIR, "tsort-modules")


@pytest.mark.usefixtures("tree")
def test_pairs():
    assert (slurp_cmd('{} pairs', tsort_script)
            == slurp_cmd('tools/tsort-modules pairs'))
