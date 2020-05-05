from pathlib import Path
from setuptools import setup

# TODO: auto-version; test_suite; keywords;
#       get LICENSE file into sdist (it's in wheel already);
#       more long_description? in rST?

THIS_DIR = Path(__file__).parent

long_description = open(THIS_DIR / "pysh" / "README.md").read()

setup(
    name="pysh-lib",
    version="0.0.2",
    description="Pythonically simple alternative to shell scripts and subprocess",
    keywords="scripting shell subprocess cli",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Greg Price",
    author_email="gnprice@gmail.com",
    url="https://github.com/gnprice/pysh",
    project_urls={
        "Documentation": "https://github.com/gnprice/pysh/blob/master/pysh/README.md",
        "Examples": "https://github.com/gnprice/pysh/tree/master/example",
    },
    license="MIT",
    packages=["pysh"],
    python_requires=">=3.6",
    install_requires=[
        "click>=7.0",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Operating System :: Unix",
        "Operating System :: POSIX",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS :: MacOS X",
        "Environment :: Console",
        "Environment :: No Input/Output (Daemon)",
        "Environment :: Web Environment",
        "Environment :: Other Environment",
        # perhaps topics?
    ],
)
