# -*- coding: utf-8 -*-
"""
Text Analysis

<url>:See WMA guide:https://reference.wolfram.com/language/guide/TextAnalysis.html</url>
"""

# This module uses both enchant, nltk and spacy. Maybe we want to split this further.

import re
from itertools import islice
from typing import Optional

import enchant
import nltk
import spacy
from mathics.builtin.atomic.strings import anchor_pattern, to_regex
from mathics.builtin.base import Builtin
from mathics.core.atoms import Integer, Real, String
from mathics.core.evaluation import Evaluation
from mathics.core.expression import Expression
from mathics.core.list import ListExpression
from mathics.core.symbols import SymbolFalse, SymbolList, SymbolTrue
from mathics.core.systemsymbols import SymbolStringExpression
from mathics.eval.nevaluator import eval_N

from pymathics.natlang.spacy import _SpacyBuiltin
from pymathics.natlang.util import _WordListBuiltin, _WordNetBuiltin, merge_dictionaries

sort_order = "Text Analysis"


class Containing(Builtin):
    """
    <url>:WMA link:
    https://reference.wolfram.com/language/ref/Containing.html</url>

    <dl>
      <dt>'Containing[$outer$, $inner$]'
      <dd>represents an object of the type outer containing objects\
          of type inner.
    </dl>
    'Containing' can be used as the second parameter in 'TextCases' and 'TextPosition'.
    
    Supported $outer$ strings are in {"Word", "Sentence", "Paragraph", "Line", "URL", "EmailAddress"}.

    Supported $inner$ strings are in {"Person", "Company", "Quantity", "Number", "CurrencyAmount",
    "Country", "City"}.
    
    The implementation of this symbol is based on `spacy`.

    >> TextCases["This is a pencil. This is another pencil from England.", Containing["Sentence", "Country"]]
     = {This is another pencil from England.}
    >> TextPosition["This is a pencil. This is another pencil from England.", Containing["Sentence", "Country"]]
     = {{19, 54}}

    """
    # This is implemented in ``pymathics.natlang.spacy._containing``
    summary_text = "specify a container for matching"


class DictionaryLookup(_WordListBuiltin):
    """
    <url>:WMA link:
    https://reference.wolfram.com/language/ref/DictionaryLookup.html</url>

    <dl>
      <dt>'DictionaryLookup[$word$]'
      <dd>lookup words that match the given $word$ or pattern.

      <dt>'DictionaryLookup[$word$, $n$]'
      <dd>lookup first $n$ words that match the given $word$ or pattern.
    </dl>

    >> DictionaryLookup["baker" ~~ ___]
     = {baker, baker's dozen, baker's eczema, baker's yeast, bakersfield, bakery}

    >> DictionaryLookup["baker" ~~ ___, 3]
     = {baker, baker's dozen, baker's eczema}
    """

    summary_text = "Lookup words matching a pattern in a dictionary"

    def compile(self, pattern, evaluation):
        re_patt = to_regex(pattern, evaluation)
        if re_patt is None:
            evaluation.message(
                "StringExpression",
                "invld",
                pattern,
                Expression(SymbolStringExpression, pattern),
            )
            return
        re_patt = anchor_pattern(re_patt)

        return re.compile(re_patt, flags=re.IGNORECASE)

    def search(self, dictionary_words, pattern):
        for dictionary_word in dictionary_words:
            if pattern.match(dictionary_word):
                yield dictionary_word.replace("_", " ")

    def lookup(self, language_name, word, n, evaluation):
        pattern = self.compile(word, evaluation)
        if pattern:
            dictionary_words = self._words(language_name, "All", evaluation)
            if dictionary_words is not None:
                matches = self.search(dictionary_words, pattern)
                if n is not None:
                    matches = islice(matches, 0, n)
                return ListExpression(*(String(match) for match in sorted(matches)))

    def eval_english(self, word, evaluation):
        "DictionaryLookup[word_]"
        return self.lookup(String("English"), word, None, evaluation)

    def eval_language(self, language, word, evaluation):
        "DictionaryLookup[{language_String, word_}]"
        return self.lookup(language, word, None, evaluation)

    def eval_english_n(self, word, n, evaluation):
        "DictionaryLookup[word_, n_Integer]"
        return self.lookup(String("English"), word, n.value, evaluation)

    def eval_language_n(self, language, word, n, evaluation):
        "DictionaryLookup[{language_String, word_}, n_Integer]"
        return self.lookup(language, word, n.value, evaluation)


class DictionaryWordQ(_WordNetBuiltin):
    """
    <url>:WMA link:
    https://reference.wolfram.com/language/ref/DictionaryWordQ.html</url>

    <dl>
      <dt>'DictionaryWordQ[$word$]'
      <dd>returns True if $word$ is a word usually found in dictionaries, and False otherwise.
    </dl>

    >> DictionaryWordQ["couch"]
     = True

    >> DictionaryWordQ["meep-meep"]
     = False
    """

    summary_text = "Check if a word is in the dictionary"

    def eval(self, word, evaluation: Evaluation, options: dict):
        "DictionaryWordQ[word_String,  OptionsPattern[DictionaryWordQ]]"
        if not isinstance(word, String):
            return False
        wordnet, language_code = self._load_wordnet(
            evaluation, self._language_name(evaluation, options)
        )
        if wordnet:
            if list(wordnet.synsets(word.value.lower(), None, language_code)):
                return SymbolTrue
            else:
                return SymbolFalse


class SpellingCorrectionList(Builtin):
    """
    <url>:WMA link:
    https://reference.wolfram.com/language/ref/SpellingCorrectionList.html</url>

    <dl>
      <dt>'SpellingCorrectionList[$word$]'
      <dd>returns a list of suggestions for spelling corrected versions of $word$.
    </dl>

    Results may differ depending on which dictionaries can be found by enchant.

    >> SpellingCorrectionList["hipopotamus"]
     = {hippopotamus...}
    """

    options = {
        "Language": '"English"',
    }

    messages = {
        "lang": "SpellingCorrectionList does not support `1` as a language.",
    }

    _languages = {
        "English": "en_US",  # en_GB, en_AU
        "German": "de_DE",
        "French": "fr_FR",
    }

    _dictionaries = {}

    summary_text = "Look for spelling correction candidates of a word"

    def eval(
        self, word: String, evaluation: Evaluation, options: dict
    ) -> Optional[ListExpression]:
        "SpellingCorrectionList[word_String, OptionsPattern[SpellingCorrectionList]]"

        language_name = self.get_option(options, "Language", evaluation)
        if not isinstance(language_name, String):
            return
        language_code = SpellingCorrectionList._languages.get(language_name.value, None)
        if not language_code:
            evaluation.message("SpellingCorrectionList", "lang", language_name)
            return

        d = SpellingCorrectionList._dictionaries.get(language_code, None)
        if not d:
            d = enchant.Dict(language_code)
            SpellingCorrectionList._dictionaries[language_code] = d

        py_word = word.value

        if d.check(py_word):
            return ListExpression(word)
        else:
            return ListExpression(*(String(word) for word in d.suggest(py_word)))


class WordCount(_SpacyBuiltin):
    """
    <url>:WMA link:
    https://reference.wolfram.com/language/ref/WordCount.html</url>

    <dl>
      <dt>'WordCount[$string$]'
      <dd>returns the number of words in $string$.
    </dl>

    >> WordCount["A long time ago"]
     = 4
    """

    summary_text = "Count the words in a text"

    def eval(self, text, evaluation: Evaluation, options: dict):
        "WordCount[text_String, OptionsPattern[WordCount]]"
        doc = self._nlp(text.value, evaluation, options)
        if doc:
            punctuation = spacy.parts_of_speech.PUNCT
            return Integer(sum(1 for word in doc if word.pos != punctuation))


class WordFrequency(_SpacyBuiltin):
    """
    <url>:WMA link:
    https://reference.wolfram.com/language/ref/WordFrequency.html</url>

    <dl>
      <dt>'WordFrequency[$text$, $word$]'
      <dd>returns the relative frequency of $word$ in $text$.
    </dl>

    $word$ may also specify multiple words using $a$ | $b$ | ...

    ## Problem with import for certain characters in the text.
    ## >> text = Import["ExampleData/EinsteinSzilLetter.txt"];
    >> text = "I have a dairy cow, it's not just any cow. \
She gives me milkshake, oh what a salty cow. She is the best \
cow in the county.";

    >> WordFrequency[text, "a" | "the"]
     = 0.121212

    >> WordFrequency["Apple Tree", "apple", IgnoreCase -> True]
     = 0.5
    """

    options = _SpacyBuiltin.options
    options.update({"IgnoreCase": "False"})
    summary_text = "retrieve the frequency of a word in a text"

    def eval(
        self, text: String, word, evaluation: Evaluation, options: dict
    ) -> Optional[Expression]:
        "WordFrequency[text_String, word_, OptionsPattern[WordFrequency]]"
        doc = self._nlp(text.value, evaluation, options)
        if not doc:
            return
        if isinstance(word, String):
            words = set([word.value])
        elif word.get_head_name() == "System`Alternatives":
            if not all(isinstance(a, String) for a in word.elements):
                return  # error
            words = set(a.value for a in word.elements)
        else:
            return  # error

        ignore_case = self.get_option(options, "IgnoreCase", evaluation) is SymbolTrue
        if ignore_case:
            words = [w.lower() for w in words]
        n = 0
        for token in doc:
            token_text = token.text
            if ignore_case:
                token_text = token_text.lower()
            if token_text in words:
                n += 1
        return eval_N(Integer(n) / Integer(len(doc)), evaluation)


class WordSimilarity(_SpacyBuiltin):
    """

    <url>:WMA link:
    https://reference.wolfram.com/language/ref/WordSimilarity.html</url>

    <dl>
      <dt>'WordSimilarity[$text1$, $text2$]'
      <dd>returns a real-valued measure of semantic similarity of two texts or words.

      <dt>'WordSimilarity[{$text1$, $i1$}, {$text2$, $j1$}]'
      <dd>returns a measure of similarity of two words within two texts.

      <dt>'WordSimilarity[{$text1$, {$i1$, $i2$, ...}}, {$text2$, {$j1$, $j2$, ...}}]'
      <dd>returns a measure of similarity of multiple words within two texts.
    </dl>

    >> NumberForm[WordSimilarity["car", "train"], 3]
     = 0.439

    >> NumberForm[WordSimilarity["car", "hedgehog"], 3]
     = 0.195

    >> NumberForm[WordSimilarity[{"An ocean full of water.", {2, 2}}, { "A desert full of sand.", {2, 5}}], 3]
     = {0.505, 0.481}
    """

    messages = merge_dictionaries(
        _SpacyBuiltin.messages,
        {
            "txtidx": "Index `1` in position `2` must be between 1 and `3`.",
            "idxfmt": "Indices must be integers or lists of integers of the same length.",
        },
    )
    summary_text = "Measure the similarity of two texts"

    def eval(
        self, text1: String, text2: String, evaluation: Evaluation, options: dict
    ) -> Optional[Real]:
        "WordSimilarity[text1_String, text2_String, OptionsPattern[WordSimilarity]]"
        doc1 = self._nlp(text1.value, evaluation, options)
        if doc1:
            doc2 = self._nlp(text2.value, evaluation, options)
            if doc2:
                return Real(doc1.similarity(doc2))

    def eval_pair(self, text1, i1, text2, i2, evaluation: Evaluation, options: dict):
        "WordSimilarity[{text1_String, i1_}, {text2_String, i2_}, OptionsPattern[WordSimilarity]]"
        doc1 = self._nlp(text1.value, evaluation, options)
        if doc1:
            if text2.value == text1.value:
                doc2 = doc1
            else:
                doc2 = self._nlp(text2.value, evaluation, options)
            if doc2:
                if i1.get_head() is SymbolList and i2.get_head() is SymbolList:
                    if len(i1.elements) != len(i2.elements):
                        evaluation.message("TextSimilarity", "idxfmt")
                        return
                    if any(
                        not all(isinstance(i, Integer) for i in li.elements)
                        for li in (i1, i2)
                    ):
                        evaluation.message("TextSimilarity", "idxfmt")
                        return
                    indices1 = [i.value for i in i1.elements]
                    indices2 = [i.value for i in i2.elements]
                    multiple = True
                elif isinstance(i1, Integer) and isinstance(i2, Integer):
                    indices1 = [i1.value]
                    indices2 = [i2.value]
                    multiple = False
                else:
                    evaluation.message("TextSimilarity", "idxfmt")
                    return

                for index1, index2 in zip(indices1, indices2):
                    for i, pos, doc in zip((index1, index2), (1, 2), (doc1, doc2)):
                        if i < 1 or i > len(doc):
                            evaluation.message(
                                "TextSimilarity", "txtidx", i, pos, len(doc)
                            )
                            return

                result = [
                    Real(doc1[j1 - 1].similarity(doc2[j2 - 1]))
                    for j1, j2 in zip(indices1, indices2)
                ]

                if multiple:
                    return ListExpression(*result)
                else:
                    return result[0]


class WordStem(Builtin):
    """
    <url>:WMA link:
    https://reference.wolfram.com/language/ref/WordStem.html</url>

    <dl>
      <dt>'WordStem[$word$]'
      <dd>returns a stemmed form of $word$, thereby reducing an inflected form to its root.

      <dt>'WordStem[{$word1$, $word2$, ...}]'
      <dd>returns a stemmed form for list of $word$, thereby reducing an inflected form to its root.
    </dl>

    >> WordStem["towers"]
     = tower

    >> WordStem[{"heroes", "roses", "knights", "queens"}]
     = {hero, rose, knight, queen}
    """

    _stemmer = None

    requires = ("nltk",)
    summary_text = "retrieve the stem of a word"

    @staticmethod
    def _get_porter_stemmer():
        if WordStem._stemmer is None:
            WordStem._stemmer = nltk.stem.porter.PorterStemmer()
        return WordStem._stemmer

    @staticmethod
    def porter(w):
        return WordStem._get_porter_stemmer().stem(w)

    def eval(self, word: String, evaluation: Evaluation) -> String:
        "WordStem[word_String]"
        stemmer = self._get_porter_stemmer()
        return String(stemmer.stem(word.value))

    def eval_list(self, words, evaluation: Evaluation) -> Optional[ListExpression]:
        "WordStem[words_List]"
        if all(isinstance(w, String) for w in words.elements):
            stemmer = self._get_porter_stemmer()
            return ListExpression(
                *[String(stemmer.stem(w.value)) for w in words.elements]
            )
