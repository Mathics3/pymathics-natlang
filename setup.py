#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import os.path as osp
import platform
import sys

from setuptools import find_namespace_packages, setup

# Ensure user has the correct Python version
if sys.version_info < (3, 6):
    print("Mathics support Python 3.6 and above; you have %d.%d" % sys.version_info[:2])
    sys.exit(-1)


def get_srcdir():
    filename = osp.normcase(osp.dirname(osp.abspath(__file__)))
    return osp.realpath(filename)


def read(*rnames):
    return open(osp.join(get_srcdir(), *rnames)).read()


# Get/set VERSION and long_description from files
long_description = read("README.rst") + "\n"

__version__ = "0.0.0"  # overwritten by exec below

# stores __version__ in the current namespace
exec(compile(open("pymathics/natlang/version.py").read(), "version.py", "exec"))

is_PyPy = platform.python_implementation() == "PyPy"

# Install a wordlist.
# Environment variables "lang", "WORDLIST_SIZE", and "SPACY_DOWNLOAD" override defaults.

# Full package name with two-letter language code, e.g. fr, zh
lang = os.environ.get("lang", "en_core_web_md")

# Size of wordlist used
# sm=small, lg=large, md=medium.
WORDLIST_SIZE = os.environ.get("WORDLIST_SIZE", "md")

SPACY_DOWNLOAD = os.environ.get("SPACY_DOWNLOAD", "%s" % (lang,))

# FIXME:
# consider using langid3 and pyenchant

setup(
    name="pymathics-natlang",
    version=__version__,
    packages=find_namespace_packages(include=["pymathics.*"]),
    install_requires=[
        "Mathics3 >=6.0.0,<6.1.0",
        "click>=8.0",
        "joblib>=1.0.1",
        "langid",  # replace with a supported newer package, e.g. via spacy
        "llvmlite>=0.36",
        "nltk>=3.8.0",
        "pattern>=3.6.0",
        "pyenchant>=3.2.0",
        "pycountry>=3.2.0",
        "spacy>=3.4",
        "wasabi<1.1.0,>=0.8.2",
    ],
    zip_safe=False,
    maintainer="Mathics3 Group",
    maintainer_email="rb@dustyfeet.com",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    # metadata for upload to PyPI
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Mathematics",
        "Topic :: Scientific/Engineering :: Physics",
        "Topic :: Software Development :: Interpreters",
        "Topic :: Scientific/Engineering :: Human Machine Interfaces",
        "Topic :: Text Processing",
        "Topic :: Text Processing :: Linguistic",
    ],
    # TODO: could also include long_description, download_url,
)

os.system("%s -m nltk.downloader wordnet2022 omw" % sys.executable)
os.system("%s -m spacy download %s" % (sys.executable, lang))
