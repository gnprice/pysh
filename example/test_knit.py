
import os
import subprocess
import sys
import tempfile

import pytest

THIS_DIR=os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.dirname(THIS_DIR))

from pysh import cmd
from pysh.filters import slurp
from pysh.words import shwords


@pytest.fixture
def chtempdir():
    oldcwd = os.getcwd()
    try:
        with tempfile.TemporaryDirectory() as dirname:
            os.chdir(dirname)
            yield
    finally:
        os.chdir(oldcwd)


def run(cmd, *args):
    subprocess.check_call(shwords(cmd, *args))


def example_ci(name):
    with open(name, "w") as f:
        f.write(f"{name}\n")
    run("git add {}", name)
    run("git commit -m {}", name)


@pytest.fixture
def repo(chtempdir):
    """
    * (master) m
    |
    | * (datacomp) d
    |/
    * a
    """
    run("git init")
    example_ci("a")
    example_ci("m")
    run("git checkout @^ -b datacomp")
    example_ci("d")
    run("git checkout master")


knit_script = os.path.join(THIS_DIR, "knit")


@pytest.mark.usefixtures("repo")
def test_basic_happy():
    run("git log --graph --oneline --all @")

    run("{} brown-dwarf", knit_script)

    run("git log --graph --oneline --all @")
    parents = \
        slurp(cmd.run("git log -n1 --format=%p @")).split(b" ")
    assert parents == [
        slurp(cmd.run("git rev-parse --short master")),
        slurp(cmd.run("git rev-parse --short datacomp")),
    ]


@pytest.mark.usefixtures("repo")
def test_dirty():
    with open("a", "a") as f:
        f.write("aa\n")
    run("git log --graph --oneline --all @")

    with pytest.raises(subprocess.CalledProcessError):
        run("{} brown-dwarf", knit_script)

    run("git log --graph --oneline --all @")
    assert slurp(cmd.run("git rev-parse @")) \
        == slurp(cmd.run("git rev-parse master"))


@pytest.mark.usefixtures("repo")
def test_originfallback():
    run("git update-ref refs/remotes/origin/datacomp datacomp")
    run("git update-ref -d refs/heads/datacomp")
    run("git log --graph --oneline --all @")

    run("{} brown-dwarf", knit_script)

    run("git log --graph --oneline --all @")
    assert slurp(cmd.run("git log -n1 --format=%p @")).split(b" ") == [
        slurp(cmd.run("git rev-parse --short master")),
        slurp(cmd.run("git rev-parse --short origin/datacomp")),
    ]
    

@pytest.mark.usefixtures("repo")
def test_fail_on_branch_missing():
    run("git update-ref -d refs/heads/datacomp")
    run("git log --graph --oneline --all @")

    with pytest.raises(subprocess.CalledProcessError):
        run("{} brown-dwarf", knit_script)

    run("git log --graph --oneline --all @")
    assert slurp(cmd.run("git rev-parse @")) \
        == slurp(cmd.run("git rev-parse master"))


@pytest.mark.usefixtures("repo")
def test_include_optional():
    run("git checkout @^ -b brown-dwarf.only")
    example_ci("b")
    run("git checkout master")
    run("git log --graph --oneline --all @")

    run("{} brown-dwarf", knit_script)

    run("git log --graph --oneline --all @")
    assert slurp(cmd.run("git log -n1 --format=%p @")).split(b" ") == [
        slurp(cmd.run("git rev-parse --short master")),
        slurp(cmd.run("git rev-parse --short datacomp")),
        slurp(cmd.run("git rev-parse --short brown-dwarf.only")),
    ]
