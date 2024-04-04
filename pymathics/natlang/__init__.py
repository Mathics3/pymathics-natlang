"""
Natural Language Processing

Mathics3 Module module provides functions and variables to work with \
expressions in natural language, using the Python libraries:

<ul>
  <li><url>:spacy:
https://spacy.io/</url> for parsing natural languages</url>
  <li><url>
:nltk:
https://www.nltk.org/</url> for functions using WordNet-related builtins
  <li><url>
:pyenchant:
https://pyenchant.github.io/pyenchant/</url> and <url>
:pycountry:
https://pypi.org/project/pycountry/</url> for language identification
</ul>

Examples:

   >> LoadModule["pymathics.natlang"]
    = pymathics.natlang

   >> Pluralize["try"]
    = tries

   >> LanguageIdentify["eins zwei drei"]
    = German

   >> WordFrequency["Apple Tree and apple", "apple", IgnoreCase -> True]
    = 0.5

   >> TextCases["I was in London last year.", "Pronoun"]
    = {I}

   >> DeleteStopwords["There was an Old Man of Apulia, whose conduct was very peculiar"]
     = Old Man Apulia, conduct peculiar
"""

from pymathics.natlang.linguistic_data import (
    DictionaryLookup,
    DictionaryWordQ,
    RandomWord,
    WordData,
    WordDefinition,
    WordList,
)
from pymathics.natlang.manipulate import Pluralize
from pymathics.natlang.normalization import (
    DeleteStopwords,
    TextCases,
    TextPosition,
    TextSentences,
    TextStructure,
    TextWords,
)
from pymathics.natlang.textual_analysis import (
    Containing,
    SpellingCorrectionList,
    WordCount,
    WordFrequency,
    WordSimilarity,
    WordStem,
)

from pymathics.natlang.linguistic_data import (
    DictionaryLookup,
    DictionaryWordQ,
    RandomWord,
    WordData,
    WordDefinition,
    WordList,
)
from pymathics.natlang.linguistic_data.translation import LanguageIdentify
from pymathics.natlang.version import __version__

pymathics_version_data = {
    "author": "The Mathics3 Team",
    "version": __version__,
    "name": "Natlang",
    "requires": ["langid", "pyenchant", "nltk", "spacy"],
}

__all__ = [
    "Containing",
    "DeleteStopwords",
    "DictionaryLookup",
    "DictionaryWordQ",
    "LanguageIdentify",
    "Pluralize",
    "RandomWord",
    "SpellingCorrectionList",
    "TextCases",
    "TextPosition",
    "TextSentences",
    "TextStructure",
    "TextWords",
    "WordCount",
    "WordData",
    "WordDefinition",
    "WordFrequency",
    "WordList",
    "WordSimilarity",
    "WordStem",
    "__version__",
    "pymathics_version_data",
]
