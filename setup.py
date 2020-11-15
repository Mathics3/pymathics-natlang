#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import platform
import os
from setuptools import setup, find_namespace_packages

# Ensure user has the correct Python version
if sys.version_info < (3, 6):
    print("Mathics support Python 3.6 and above; you have %d.%d" % sys.version_info[:2])
    sys.exit(-1)

# stores __version__ in the current namespace
exec(compile(open("pymathics/natlang/version.py").read(), "version.py", "exec"))

is_PyPy = platform.python_implementation() == "PyPy"

# Install a wordlist.
# Environment variables "lang", "WORDLIST_SIZE", and "SPACY_DOWNLOAD" override defaults.

# Two-letter language code, e.g. fr, zh
lang = os.environ.get("lang", "en")

# Size of wordlist used
# sm=small, lg=large, md=medium.
WORDLIST_SIZE = os.environ.get("WORDLIST_SIZE", "md")

SPACY_DOWNLOAD = os.environ.get("SPACY_DOWNLOAD", "%s" % (lang,))

setup(
    name="pymathics-natlang",
    version=__version__,
    packages=find_namespace_packages(include=["pymathics.*"]),
    install_requires=["mathics>=1.0", "nltk", "spacy<3.0"],
    # don't pack Mathics in egg because of media files, etc.
    zip_safe=False,
    maintainer="Mathics Group",
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

os.system("%s -m nltk.downloader wordnet omw" % sys.executable)
os.system("%s -m spacy download %s" % (sys.executable, lang))
