# -*- coding: utf-8 -*-


"""
Language translation

"""

from typing import Union

import langid  # see https://github.com/saffsd/langid.py
import pycountry
from mathics.builtin.base import Builtin
from mathics.core.atoms import String
from mathics.core.evaluation import Evaluation
from mathics.core.symbols import Symbol
from mathics.core.systemsymbols import SymbolFailed


class LanguageIdentify(Builtin):
    """
    <url>:WMA:
    https://reference.wolfram.com/language/ref/LanguageIdentify.html</url>

    <dl>
      <dt>'LanguageIdentify[$text$]'
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
