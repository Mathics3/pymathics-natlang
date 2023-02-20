# -*- coding: utf-8 -*-
"""
Linguistic Data

See <url>:WMA:https://reference.wolfram.com/language/guide/LinguisticData.html</url> guide.

"""
# This module uses both nltk and spacy. Maybe it makes sense to split this further.


# TODO: Complete me

# WordFrequencyData — data on typical current and historical word frequencies
# Synonyms — synonyms for a word
# Antonyms — antonyms for a word
# PartOfSpeech — possible parts of speech for a word


from typing import Optional

from mathics.builtin.base import Builtin, MessageException

# from mathics.builtin.codetables import iso639_3
from mathics.builtin.numbers.randomnumbers import RandomEnv
from mathics.core.atoms import String
from mathics.core.convert.expression import Expression, to_expression
from mathics.core.evaluation import Evaluation
from mathics.core.list import ListExpression
from mathics.core.symbols import Symbol, SymbolList
from mathics.core.systemsymbols import SymbolMissing, SymbolRule, SymbolStringExpression
from pattern.en import pluralize

from pymathics.natlang.textual_analysis import WordStem
from pymathics.natlang.util import (
    WordProperty,
    _WordListBuiltin,
    _wordnet_pos_to_type,
    _WordNetBuiltin,
    merge_dictionaries,
)

SymbolDictionaryLookup = Symbol("Pymathics`Natlang`DictionaryLookup")
StringNotAvailable = String("NotAvailable")


class Pluralize(Builtin):
    """
    <url>:WMA:
    https://reference.wolfram.com/language/ref/Pluralize.html</url>

    <dl>
      <dt>'Pluralize[$word$]'
      <dd>returns the plural form of $word$.
    </dl>

    >> Pluralize["potato"]
     = potatoes
    """

    requires = ("pattern",)
    summary_text = "Retrieve the pluralized form of a word"

    def eval(self, word, evaluation):
        "Pluralize[word_String]"

        return String(pluralize(word.value))


class RandomWord(_WordListBuiltin):
    """
    <url>:WMA:
    https://reference.wolfram.com/language/ref/RandomWord.html</url>

    <dl>
      <dt>'RandomWord[]'
      <dd>returns a random word.

      <dt>'RandomWord[$type$]'
      <dd>returns a random word of the given $type$, e.g. of type "Noun" or "Adverb".

      <dt>'RandomWord[$type$, $n$]'
      <dd>returns $n$ random words of the given $type$.

    >> RandomWord["Noun"]
     = ...
    >> RandomWord["Noun", 3]
     = {..., ..., ...}

    </dl>
    """

    summary_text = "generate a random word of a given kind"

    def _random_words(self, type, n, evaluation: Evaluation, options: dict):
        words = self._words(self._language_name(evaluation, options), type, evaluation)
        if words is not None:
            with RandomEnv(evaluation) as rand:
                return [
                    String(words[rand.randint(0, len(words) - 1)].replace("_", " "))
                    for _ in range(n)
                ]

    def eval(self, evaluation: Evaluation, options: dict):
        "RandomWord[OptionsPattern[RandomWord]]"
        words = self._random_words("All", 1, evaluation, options)
        if words:
            return words[0]

    def eval_type(self, type, evaluation: Evaluation, options: dict):
        "RandomWord[type_String, OptionsPattern[RandomWord]]"
        words = self._random_words(type.value, 1, evaluation, options)
        if words:
            return words[0]

    def eval_type_n(self, type, n, evaluation: Evaluation, options: dict):
        "RandomWord[type_String, n_Integer, OptionsPattern[RandomWord]]"
        words = self._random_words(type.value, n.value, evaluation, options)
        if words:
            return ListExpression(*words)


class WordData(_WordListBuiltin):
    """

    <url>:WMA:
    https://reference.wolfram.com/language/ref/WordData.html</url>

    <dl>
      <dt>'WordData[$word$]'
      <dd>returns a list of possible senses of a word.

      <dt>'WordData[$word$, $property$]'
      <dd>returns detailed information about a word regarding $property$, e.g. "Definitions" or "Examples".
    </dl>

    The following are valid properties:
    <ul>
      <li> Definitions, Examples
      <li> InflectedForms
      <li> Synonyms, Antonyms
      <li> BroaderTerms, NarrowerTerms
      <li> WholeTerms, PartTerms, MaterialTerms
      <li> EntailedTerms, CausesTerms
      <li> UsageField
      <li> WordNetID
      <li> Lookup
    </ul>

    >> WordData["riverside", "Definitions"]
     = {{riverside, Noun, Bank} -> the bank of a river}

    >> WordData[{"fish", "Verb", "Angle"}, "Examples"]
     = {{fish, Verb, Angle} -> {fish for compliments}}
    """

    messages = merge_dictionaries(
        _WordNetBuiltin.messages,
        {
            "notprop": "WordData[] does not recognize `1` as a valid property.",
        },
    )
    summary_text = "retrieve an association with properties of a word"

    def _parse_word(self, word):
        if isinstance(word, String):
            return word.value.lower()
        elif word.get_head_name() == "System`List":
            if len(word.elements) == 3 and all(
                isinstance(s, String) for s in word.elements
            ):
                return tuple(s.value for s in word.elements)

    def _standard_property(
        self, py_word, py_form, py_property, wordnet, language_code, evaluation
    ):
        senses = self._senses(py_word, wordnet, language_code)
        if not senses:
            return Expression(SymbolMissing, StringNotAvailable)
        elif py_form == "List":
            word_property = WordProperty(self._short_syn_form, wordnet, language_code)
            property_getter = getattr(
                word_property, "%s" % self._underscore(py_property), None
            )
            if property_getter:
                return ListExpression(
                    *[property_getter(syn, desc) for syn, desc in senses]
                )
        elif py_form in ("Rules", "ShortRules"):
            syn_form = (lambda s: s) if py_form == "Rules" else (lambda s: s[0])
            word_property = WordProperty(syn_form, wordnet, language_code)
            property_getter = getattr(
                word_property, self._underscore(py_property), None
            )
            if property_getter:
                list_expr_elements = [
                    to_expression(SymbolRule, desc, property_getter(syn, desc))
                    for syn, desc in senses
                ]
                return ListExpression(*list_expr_elements)
        evaluation.message(self.get_name(), "notprop", property)

    def _parts_of_speech(self, py_word, wordnet, language_code):
        parts = set(
            syn.pos() for syn, _ in self._senses(py_word, wordnet, language_code)
        )
        if not parts:
            return Expression(SymbolMissing, StringNotAvailable)
        else:
            return ListExpression(
                *[String(s) for s in sorted([_wordnet_pos_to_type[p] for p in parts])]
            )

    def _property(
        self, word, py_property, py_form, evaluation: Evaluation, options: dict
    ):
        if py_property == "PorterStem":
            if isinstance(word, String):
                return String(WordStem.porter(word.value))
            else:
                return

        wordnet, language_code = self._load_wordnet(
            evaluation, self._language_name(evaluation, options)
        )
        if not wordnet:
            return

        py_word = self._parse_word(word)
        if not py_word:
            return

        if py_property == "PartsOfSpeech":
            return self._parts_of_speech(py_word, wordnet, language_code)

        try:
            return self._standard_property(
                py_word, py_form, py_property, wordnet, language_code, evaluation
            )
        except MessageException as e:
            e.message(evaluation)

    def eval(self, word, evaluation: Evaluation, options: dict) -> Optional[Expression]:
        "WordData[word_, OptionsPattern[WordData]]"
        if word.get_head() is SymbolStringExpression:
            return Expression(SymbolDictionaryLookup, word)
        elif isinstance(word, String) or word.get_head() is SymbolList:
            pass
        else:
            return

        wordnet, language_code = self._load_wordnet(
            evaluation, self._language_name(evaluation, options)
        )
        if not wordnet:
            return

        py_word = self._parse_word(word)
        if not py_word:
            return

        senses = self._senses(py_word, wordnet, language_code)
        if senses is not None:
            return ListExpression(*[[String(s) for s in desc] for syn, desc in senses])

    def eval_property(self, word, property, evaluation: Evaluation, options: dict):
        "WordData[word_, property_String, OptionsPattern[WordData]]"
        if word.get_head is SymbolStringExpression:
            if property.get_string_value() == "Lookup":
                return Expression(SymbolDictionaryLookup, word)
        elif isinstance(word, String) or word.get_head() is SymbolList:
            return self._property(
                word, property.get_string_value(), "ShortRules", evaluation, options
            )

    def eval_property_form(
        self, word, property, form, evaluation: Evaluation, options: dict
    ):
        "WordData[word_, property_String, form_String, OptionsPattern[WordData]]"
        if isinstance(word, String) or word.get_head() is SymbolList:
            return self._property(
                word,
                property.value,
                form.value,
                evaluation,
                options,
            )


class WordDefinition(_WordNetBuiltin):
    """
    <url>:WMA:
    https://reference.wolfram.com/language/ref/WordDefinition.html</url>

    <dl>
      <dt>'WordDefinition[$word$]'
      <dd>returns a definition of $word$ or Missing["Available"] if $word$ is not known.
    </dl>

    >> WordDefinition["gram"]
     = {a metric unit of weight equal to one thousandth of a kilogram}
    """

    summary_text = "retrieve the definition of a word"

    def eval(self, word, evaluation: Evaluation, options: dict):
        "WordDefinition[word_String, OptionsPattern[WordDefinition]]"
        wordnet, language_code = self._load_wordnet(
            evaluation, self._language_name(evaluation, options)
        )
        if wordnet:
            senses = self._senses(word.value.lower(), wordnet, language_code)
            if senses:
                return ListExpression(*[String(syn.definition()) for syn, _ in senses])
            else:
                return Expression(SymbolMissing, StringNotAvailable)


class WordList(_WordListBuiltin):
    """
    <url>:WMA:
    https://reference.wolfram.com/language/ref/WordList.html</url>

    <dl>
      <dt>'WordList[]'
      <dd>returns a list of common words.

      <dt>'WordList[$type$]'
      <dd>returns a list of common words of type $type$.
    </dl>

    >> N[Mean[StringLength /@ WordList["Adjective"]], 2]
     = 9.3
    """

    summary_text = "retrieve a list of common words"

    def eval(self, evaluation: Evaluation, options: dict):
        "WordList[OptionsPattern[]]"
        words = self._words(self._language_name(evaluation, options), "All", evaluation)
        if words is not None:
            return ListExpression(*(String(word) for word in words))

    def eval_type(self, wordtype, evaluation: Evaluation, options: dict):
        "WordList[wordtype_String, OptionsPattern[]]"
        words = self._words(
            self._language_name(evaluation, options),
            wordtype.value,
            evaluation,
        )
        if words is not None:
            return ListExpression(*(String(word) for word in words))
