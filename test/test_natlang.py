# -*- coding: utf-8 -*-
from .helper import session, check_evaluation

import sys
from mathics.core.parser import parse, SingleLineFeeder
from mathics.core.definitions import Definitions
from mathics.core.evaluation import Evaluation
import pytest

def test_natlang():

    session.evaluate(
        """
        LoadModule["pymathics.natlang"]
        """
        )

    for str_expr, str_expected, message in (
        (
            'WordCount["A long time ago"]',
            "4",
            "WordCount",
        ),
        (
            'TextWords["Hickory, dickory, dock! The mouse ran up the clock."]',
            'System`List["Hickory", "dickory", "dock", "The", "mouse", "ran", "up", "the", "clock"]',
            "TextWords",
        ),
        (
            'TextSentences["Night and day. Day and night."]',
            'System`List["Night and day.", "Day and night."]',
            "TextSentences",
        ),
        (
            'TextSentences["Mr. Jones met Mrs. Jones."]',
            'System`List["Mr. Jones met Mrs. Jones."]',
            "TextSentences with Abbreviations",
        ),
        (
            'DeleteStopwords[{"Somewhere", "over", "the", "rainbow"}]',
            'System`List["rainbow"]',
            "DeleteStopWords",
        ),
        (
            'WordFrequency["Apple Tree", "apple", IgnoreCase -> True]',
            "0.5",
            "WordFrequency",
        ),
        (
            'TextCases["I was in London last year.", "Pronoun"]',
            'System`List["I"]',
            "TextCases",
        ),
    ):
        check_evaluation(str_expr, str_expected, message)
