
import os
import subprocess
import sys
import tempfile

import pytest

THIS_DIR=os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.dirname(THIS_DIR))

from pysh import check_cmd, cmd, shwords, slurp_cmd


@pytest.fixture
def chtempdir():
    oldcwd = os.getcwd()
    try:
        with tempfile.TemporaryDirectory() as dirname:
            os.chdir(dirname)
            yield
    finally:
        os.chdir(oldcwd)


def example_ci(name):
    with open(name, "w") as f:
        f.write(f"{name}\n")
    check_cmd("git add {}", name)
    check_cmd("git commit -m {}", name)


@pytest.fixture
def repo(chtempdir):
    """
    * (master) m
    |
    | * (datacomp) d
    |/
    * a
    """
    check_cmd("git init")
    example_ci("a")
    example_ci("m")
    check_cmd("git checkout @^ -b datacomp")
    example_ci("d")
    check_cmd("git checkout master")


knit_script = os.path.join(THIS_DIR, "knit")


@pytest.mark.usefixtures("repo")
def test_basic_happy():
    check_cmd("git log --graph --oneline --all @")

    check_cmd("{} brown-dwarf", knit_script)

    check_cmd("git log --graph --oneline --all @")
    parents = \
        slurp_cmd("git log -n1 --format=%p @").split(b" ")
    assert parents == [
        slurp_cmd("git rev-parse --short master"),
        slurp_cmd("git rev-parse --short datacomp"),
    ]


@pytest.mark.usefixtures("repo")
def test_dirty():
    with open("a", "a") as f:
        f.write("aa\n")
    check_cmd("git log --graph --oneline --all @")

    with pytest.raises(subprocess.CalledProcessError):
        check_cmd("{} brown-dwarf", knit_script)

    check_cmd("git log --graph --oneline --all @")
    assert slurp_cmd("git rev-parse @") \
        == slurp_cmd("git rev-parse master")


@pytest.mark.usefixtures("repo")
def test_originfallback():
    check_cmd("git update-ref refs/remotes/origin/datacomp datacomp")
    check_cmd("git update-ref -d refs/heads/datacomp")
    check_cmd("git log --graph --oneline --all @")

    check_cmd("{} brown-dwarf", knit_script)

    check_cmd("git log --graph --oneline --all @")
    assert slurp_cmd("git log -n1 --format=%p @").split(b" ") == [
        slurp_cmd("git rev-parse --short master"),
        slurp_cmd("git rev-parse --short origin/datacomp"),
    ]
    

@pytest.mark.usefixtures("repo")
def test_fail_on_branch_missing():
    check_cmd("git update-ref -d refs/heads/datacomp")
    check_cmd("git log --graph --oneline --all @")

    with pytest.raises(subprocess.CalledProcessError):
        check_cmd("{} brown-dwarf", knit_script)

    check_cmd("git log --graph --oneline --all @")
    assert slurp_cmd("git rev-parse @") \
        == slurp_cmd("git rev-parse master")


@pytest.mark.usefixtures("repo")
def test_include_optional():
    check_cmd("git checkout @^ -b brown-dwarf.only")
    example_ci("b")
    check_cmd("git checkout master")
    check_cmd("git log --graph --oneline --all @")

    check_cmd("{} brown-dwarf", knit_script)

    check_cmd("git log --graph --oneline --all @")
    assert slurp_cmd("git log -n1 --format=%p @").split(b" ") == [
        slurp_cmd("git rev-parse --short master"),
        slurp_cmd("git rev-parse --short datacomp"),
        slurp_cmd("git rev-parse --short brown-dwarf.only"),
    ]
