"""Pymathics Natlang

This module provides Mathics functions and variables to work with \
expressions in natural language, using the libraries 'nltk' and  \
'spacy'.
"""


from pymathics.natlang.main import *
from pymathics.natlang.version import __version__

pymathics_version_data = {
    "author": "The Mathics Team",
    "version": __version__,
    "name": "Natlang",
    "requires": ["nltk", "spacy"],
}
