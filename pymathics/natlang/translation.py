# -*- coding: utf-8 -*-


"""
Language Translation


"""

# This is under  Text Normalization in WR. But also in Natural Language Processing,
# and Linguistic Data. I put here because is the only module that uses langid and pycountry
# modules.
#
# TODO: WordTranslation, TextTranslation

from typing import Union

import langid  # see https://github.com/saffsd/langid.py
import pycountry
from mathics.core.atoms import String
from mathics.core.builtin import Builtin
from mathics.core.evaluation import Evaluation
from mathics.core.symbols import Symbol
from mathics.core.systemsymbols import SymbolFailed

sort_order = "Language Translation"


class LanguageIdentify(Builtin):
    """
    <url>:WMA link:
    https://reference.wolfram.com/language/ref/LanguageIdentify.html</url>

    <dl>
      <dt>'LanguageIdentify'[$text$]
      <dd>returns the name of the language used in $text$.
    </dl>

    >> LanguageIdentify["eins zwei drei"]
     = German
    """

    summary_text = "determine the predominant human language in a string"

    def eval(self, text: String, evaluation: Evaluation) -> Union[Symbol, String]:
        "LanguageIdentify[text_String]"

        # an alternative: https://github.com/Mimino666/langdetect

        code, _ = langid.classify(text.value)
        language = pycountry.languages.get(alpha_2=code)
        if language is None:
            return SymbolFailed
        return String(language.name)
