"""
Pymathics Natlang

This module provides tools to work with expressions in natural language, using the libraries ``nltk`` and ``spacy``.
"""


from pymathics.natlang.__main__ import *
from pymathics.natlang.version import __version__

pymathics_version_data = {
    "author": "The Mathics Team",
    "version": __version__,
    "name": "Natlang",
    "requires": ["nltk", "spacy"],
}
