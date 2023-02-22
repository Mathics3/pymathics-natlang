# -*- coding: utf-8 -*-
from .helper import check_evaluation, session


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
            'Length[WordList[]]>10000',
            "True",
            "WordList",
        ),
        (
            'TextWords["Hickory, dickory, dock! The mouse ran up the clock."]',
            '{"Hickory", "dickory", "dock", "The", "mouse", "ran", "up", "the", "clock"}',
            "TextWords",
        ),
        (
            'TextSentences["Night and day. Day and night."]',
            '{"Night and day.", "Day and night."}',
            "TextSentences",
        ),
        (
            'TextSentences["Mr. Jones met Mrs. Jones."]',
            '{"Mr. Jones met Mrs. Jones."}',
            "TextSentences with Abbreviations",
        ),
        (
            'DeleteStopwords[{"Somewhere", "over", "the", "rainbow"}]',
            '{"rainbow"}',
            "DeleteStopWords",
        ),
        (
            'WordFrequency["Apple Tree", "apple", IgnoreCase -> True]',
            "0.5",
            "WordFrequency",
        ),
        (
            'TextCases["I was in London last year.", "Pronoun"]',
            '{"I"}',
            "TextCases",
        ),
        (
            'Pluralize["try"]',
            '"I"',
            "Pluralize",
        ),
    ):
        check_evaluation(str_expr, str_expected, message)
