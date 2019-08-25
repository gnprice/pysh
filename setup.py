from pathlib import Path
from setuptools import setup

# TODO: version; project_urls; long_description;
#       test_suite; classifiers; keywords

THIS_DIR = Path(__file__).parent

long_description = open(THIS_DIR / "pysh" / "README.md").read()

setup(
    name="pysh-lib",
    version="0.1.0",
    description="Pythonically simple alternative to shell scripts and subprocess",
    keywords="scripting shell subprocess cli",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Greg Price et al.",
    author_email="gnprice@gmail.com",
    url="https://github.com/gnprice/pysh",
    license="MIT",
    packages=["pysh"],
    python_requires=">=3.7",
    install_requires=[
        "click>=7.0",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
    ],
)
