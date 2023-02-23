# -*- coding: utf-8 -*-
"""
Word manipulation

This module uses pattern.en to change the form of a word.

"""
from mathics.builtin.base import Builtin
from mathics.core.atoms import String
from mathics.core.evaluation import Evaluation
from pattern.en import pluralize

sort_order = "Word manipulation"


class Pluralize(Builtin):
    """
    <url>:WMA link:
    https://reference.wolfram.com/language/ref/Pluralize.html</url>

    <dl>
      <dt>'Pluralize[$word$]'
      <dd>returns the plural form of $word$.
    </dl>

    >> Pluralize["potato"]
     = potatoes
    """

    requires = ("pattern",)
    summary_text = "retrieve the pluralized form of a word"

    def eval(self, word: String, evaluation: Evaluation) -> String:
        "Pluralize[word_String]"

        return String(pluralize(word.value))
