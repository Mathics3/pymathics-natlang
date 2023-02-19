# -*- coding: utf-8 -*-
# FIXME: split this up into smaller pieces

"""
Natural language functions.

The following Python Packages are used:

<ul>
  <li> 'spacy' is used for parsing natural languages
  <li> 'nltk' is used for functions using WordNet-related builtins
  <li> 'langid', and `'pycountry' are used for 'LanguageIdentify[]'
  <li> 'pyenchant'` is used for 'SpellingCorrectionList[]'
</ul>

User customization:

For nltk, use the environment variable NLTK_DATA to specify a custom \
data path (instead of $HOME/.nltk).  For spacy, set 'MATHICS3_SPACY_DATA', \
a Mathics3-specific variable. \

In order to use the Extended Open Multilingual Wordnet (OMW) with 'NLTK'
and use even more languages, you need to install them manually.

Go to http://compling.hss.ntu.edu.sg/omw/summx.html, download the
data, and then create a new folder under
$HOME/nltk_data/corpora/omw/your_language where you put the file from
wiki/wn-wikt-your_language.tab, and rename it to
wn-data-your_language.tab.

Adding more languages to Open Multilingual Wordnet:

In order to use the Extended Open Multilingual Wordnet with NLTK and
use even more languages, you need to install them manually. Go to
http://compling.hss.ntu.edu.sg/omw/summx.html, download the data, and
then create a new folder under
$HOME/nltk_data/corpora/omw/your_language where you put the file from
wiki/wn-wikt-your_language.tab, and rename it to
wn-data-your_language.tab.

"""

import heapq
import itertools
import math
import os
import re
from itertools import chain
from typing import Optional, Union

from mathics.builtin.atomic.strings import anchor_pattern, to_regex
from mathics.builtin.base import Builtin, MessageException
from mathics.builtin.codetables import iso639_3
from mathics.builtin.numbers.randomnumbers import RandomEnv
from mathics.core.atoms import Integer, Real, String
from mathics.core.convert.expression import ListExpression, to_mathics_list
from mathics.core.evaluation import Evaluation
from mathics.core.expression import Expression
from mathics.core.symbols import Symbol, SymbolFalse, SymbolTrue, strip_context
from mathics.core.systemsymbols import SymbolFailed, SymbolMissing, SymbolN, SymbolRule

SymbolDictionaryLookup = Symbol("Pymathics`Natlang`DictionaryLookup")


def _parse_nltk_lookup_error(e):
    m = re.search(r"Resource '([^']+)' not found\.", str(e))
    if m:
        return m.group(1)
    else:
        return "unknown"


def _make_forms():
    forms = {
        "Word": lambda doc: (token for token in doc),
        "Sentence": lambda doc: (sent for sent in doc.sents),
        "Paragraph": lambda doc: _fragments(doc, re.compile(r"^[\n][\n]+$")),
        "Line": lambda doc: _fragments(doc, re.compile(r"^[\n]$")),
        "URL": lambda doc: (token for token in doc if token.orth_.like_url()),
        "EmailAddress": lambda doc: (
            token for token in doc if token.orth_.like_email()
        ),
    }

    def filter_named_entity(label):
        def generator(doc):
            for ent in doc.ents:
                if ent.label == label:
                    yield ent

        return generator

    def filter_pos(pos):
        def generator(doc):
            for token in doc:
                if token.pos == pos:
                    yield token

        return generator

    for name, symbol in _symbols.items():
        forms[name] = filter_named_entity(symbol)

    for tag, names in _pos_tags.items():
        name, phrase_name = names
        forms[name] = filter_pos(tag)

    return forms


# the following two may only be accessed after_WordNetBuiltin._load_wordnet has
# been called.

_wordnet_pos_to_type = {}
_wordnet_type_to_pos = {}

try:
    import nltk

    def _init_nltk_maps():
        _wordnet_pos_to_type.update(
            {
                nltk.corpus.wordnet.VERB: "Verb",
                nltk.corpus.wordnet.NOUN: "Noun",
                nltk.corpus.wordnet.ADJ: "Adjective",
                nltk.corpus.wordnet.ADJ_SAT: "Adjective",
                nltk.corpus.wordnet.ADV: "Adverb",
            }
        )
        _wordnet_type_to_pos.update(
            {
                "Verb": [nltk.corpus.wordnet.VERB],
                "Noun": [nltk.corpus.wordnet.NOUN],
                "Adjective": [nltk.corpus.wordnet.ADJ, nltk.corpus.wordnet.ADJ_SAT],
                "Adverb": [nltk.corpus.wordnet.ADV],
            }
        )

except ImportError:
    pass

try:
    import spacy
    from spacy.tokens import Span

    # Part of speech tags and their public interface names in Mathics
    # see http://www.mathcs.emory.edu/~choi/doc/clear-dependency-2012.pdf
    _pos_tags = {
        spacy.parts_of_speech.ADJ: ("Adjective", ""),
        spacy.parts_of_speech.ADP: ("Preposition", "Prepositional Phrase"),
        spacy.parts_of_speech.ADV: ("Adverb", ""),
        spacy.parts_of_speech.CONJ: ("Conjunct", ""),
        spacy.parts_of_speech.DET: ("Determiner", ""),
        spacy.parts_of_speech.INTJ: ("Interjection", ""),
        spacy.parts_of_speech.NOUN: ("Noun", "Noun Phrase"),
        spacy.parts_of_speech.NUM: ("Number", ""),
        spacy.parts_of_speech.PART: ("Particle", ""),
        spacy.parts_of_speech.PRON: ("Pronoun", ""),
        spacy.parts_of_speech.PROPN: ("Proposition", ""),
        spacy.parts_of_speech.PUNCT: ("Punctuation", ""),
        spacy.parts_of_speech.SCONJ: ("Sconj", ""),
        spacy.parts_of_speech.SYM: ("Symbol", ""),
        spacy.parts_of_speech.VERB: ("Verb", "Verb Phrase"),
        spacy.parts_of_speech.X: ("X", ""),
        spacy.parts_of_speech.EOL: ("EOL", ""),
        spacy.parts_of_speech.SPACE: ("Space", ""),
    }

    # Mathics named entitiy names and their corresponding constants in spacy.
    _symbols = {
        "Person": spacy.symbols.PERSON,
        "Company": spacy.symbols.ORG,
        "Quantity": spacy.symbols.QUANTITY,
        "Number": spacy.symbols.CARDINAL,
        "CurrencyAmount": spacy.symbols.MONEY,
        "Country": spacy.symbols.GPE,  # also includes cities and states
        "City": spacy.symbols.GPE,  # also includes countries and states
    }

    # forms are everything one can use in TextCases[] or TextPosition[].
    _forms = _make_forms()
except ImportError:
    _pos_tags = {}
    _symbols = {}
    _forms = {}


def _merge_dictionaries(a, b):
    c = a.copy()
    c.update(b)
    return c


def _position(t):
    if isinstance(t, Span):
        i = t.doc[t.start]
        r = t.doc[t.end - 1]
        return 1 + i.idx, r.idx + len(r.text)
    else:
        return 1 + t.idx, t.idx + len(t.text)


def _fragments(doc, sep):
    start = 0
    for i, token in enumerate(doc):
        if sep.match(token.text):
            yield Span(doc, start, i)
            start = i + 1
    end = len(doc)
    if start < end:
        yield Span(doc, start, end)


class _SpacyBuiltin(Builtin):
    requires = ("spacy",)

    options = {
        "Language": '"English"',
    }

    messages = {
        "runtime": "Spacy gave the following error: ``",
        "lang": 'Language "`1`" is currently not supported with `2`[].',
    }

    _language_codes = {
        "English": "en",
        "German": "de",
    }

    _spacy_instances = {}

    def _load_spacy(self, evaluation: Evaluation, options: dict):
        language_code = None
        language_name = self.get_option(options, "Language", evaluation)
        if language_name is None:
            language_name = String("Undefined")
        if isinstance(language_name, String):
            language_code = _SpacyBuiltin._language_codes.get(language_name.value)
        if not language_code:
            evaluation.message(
                self.get_name(), "lang", language_name, strip_context(self.get_name())
            )
            return None

        instance = _SpacyBuiltin._spacy_instances.get(language_code)
        if instance:
            return instance

        try:
            if "MATHICS3_SPACY_DATA" in os.environ:
                instance = spacy.load(
                    language_code, via=os.environ["MATHICS3_SPACY_DATA"]
                )
            else:
                instance = spacy.load(f"{language_code}_core_web_md")

            _SpacyBuiltin._spacy_instances[language_code] = instance
            return instance
        except RuntimeError as e:
            evaluation.message(self.get_name(), "runtime", str(e))
            return None

    def _nlp(self, text, evaluation, options) -> Optional[spacy.tokens.doc.Doc]:
        nlp = self._load_spacy(evaluation, options)
        if not nlp:
            return None
        return nlp(text)

    def _is_stop_lambda(self, evaluation: Evaluation, options: dict):
        nlp = self._load_spacy(evaluation, options)
        if not nlp:
            return None

        vocab = nlp.vocab

        def is_stop(word):
            return vocab[word].is_stop

        return is_stop


class WordFrequencyData(_SpacyBuiltin):
    """
    <dl>
      <dt>'WordFrequencyData[$word$]'
      <dd>returns the frequency of $word$ in common English texts.
    </dl>
    """

    # Mathematica uses the gargantuan Google n-gram corpus, see
    # http://commondatastorage.googleapis.com/books/syntactic-ngrams/index.html

    def eval(self, word: String, evaluation: Evaluation, options: dict) -> Real:
        "WordFrequencyData[word_String,  OptionsPattern[%(name)s]]"
        doc = self._nlp(word.value, evaluation, options)
        frequency = 0.0
        if doc:
            if len(doc) == 1:
                frequency = math.exp(doc[0].prob)  # convert log probability
        return Real(frequency)


class WordCount(_SpacyBuiltin):
    """
    <dl>
      <dt>'WordCount[$string$]'
      <dd>returns the number of words in $string$.
    </dl>

    >> WordCount["A long time ago"]
     = 4
    """

    def eval(self, text, evaluation: Evaluation, options: dict):
        "WordCount[text_String, OptionsPattern[%(name)s]]"
        doc = self._nlp(text.value, evaluation, options)
        if doc:
            punctuation = spacy.parts_of_speech.PUNCT
            return Integer(sum(1 for word in doc if word.pos != punctuation))


class TextWords(_SpacyBuiltin):
    """
    <dl>
      <dt>'TextWords[$string$]'
      <dd>returns the words in $string$.

      <dt>'TextWords[$string$, $n$]'
      <dd>returns the first $n$ words in $string$
    </dl>

    >> TextWords["Hickory, dickory, dock! The mouse ran up the clock."]
     = {Hickory, dickory, dock, The, mouse, ran, up, the, clock}
    """

    def eval(
        self, text: String, evaluation: Evaluation, options: dict
    ) -> Optional[ListExpression]:
        "TextWords[text_String, OptionsPattern[%(name)s]]"
        doc = self._nlp(text.value, evaluation, options)
        if doc:
            punctuation = spacy.parts_of_speech.PUNCT
            return ListExpression(
                *[String(word.text) for word in doc if word.pos != punctuation],
            )

    def eval_n(self, text: String, n: Integer, evaluation: Evaluation, options: dict):
        "TextWords[text_String, n_Integer, OptionsPattern[%(name)s]]"
        doc = self._nlp(text.value, evaluation, options)
        if doc:
            punctuation = spacy.parts_of_speech.PUNCT
            return ListExpression(
                *itertools.islice(
                    (String(word.text) for word in doc if word.pos != punctuation),
                    n.value,
                ),
            )


class TextSentences(_SpacyBuiltin):
    """
    <dl>
      <dt>'TextSentences[$string$]'
      <dd>returns the sentences in $string$.

      <dt>'TextSentences[$string$, $n$]'
      <dd>returns the first $n$ sentences in $string$
    </dl>

    >> TextSentences["Night and day. Day and night."]
     = {Night and day., Day and night.}

    >> TextSentences["Night and day. Day and night.", 1]
     = {Night and day.}

    >> TextSentences["Mr. Jones met Mrs. Jones."]
     = {Mr. Jones met Mrs. Jones.}
    """

    def eval(self, text: String, evaluation: Evaluation, options: dict):
        "TextSentences[text_String, OptionsPattern[%(name)s]]"
        doc = self._nlp(text.value, evaluation, options)
        if doc:
            return ListExpression(*[String(sent.text) for sent in doc.sents])

    def eval_n(self, text: String, n: Integer, evaluation: Evaluation, options: dict):
        "TextSentences[text_String, n_Integer, OptionsPattern[%(name)s]]"
        doc = self._nlp(text.value, evaluation, options)
        if doc:
            return ListExpression(
                *itertools.islice((String(sent.text) for sent in doc.sents), n.value),
            )


class DeleteStopwords(_SpacyBuiltin):
    """
    <dl>
      <dt>'DeleteStopwords[$list$]'
      <dd>returns the words in $list$ without stopwords.

      <dt>'DeleteStopwords[$string$]'
      <dd>returns $string$ without stopwords.
    </dl>

    >> DeleteStopwords[{"Somewhere", "over", "the", "rainbow"}]
     = {rainbow}

    >> DeleteStopwords["There was an Old Man of Apulia, whose conduct was very peculiar"]
     = Old Man Apulia, conduct peculiar
    """

    def eval_list(self, li, evaluation: Evaluation, options: dict) -> ListExpression:
        "DeleteStopwords[li_List, OptionsPattern[%(name)s]]"
        is_stop = self._is_stop_lambda(evaluation, options)

        def filter_words(words):
            for w in words:
                s = w.get_string_value()
                if not s:
                    yield String(s)
                elif not is_stop(s):
                    yield String(s)

        return ListExpression(*list(filter_words(li.elements)))

    def eval_string(self, s: String, evaluation: Evaluation, options: dict):
        "DeleteStopwords[s_String, OptionsPattern[%(name)s]]"
        doc = self._nlp(s.value, evaluation, options)
        if doc:
            is_stop = self._is_stop_lambda(evaluation, options)
            if is_stop:

                def tokens():
                    for token in doc:
                        if not is_stop(token.text):
                            yield token.text_with_ws
                        else:
                            yield token.whitespace_.strip()

                return String("".join(tokens()))


class WordFrequency(_SpacyBuiltin):
    """
    <dl>
      <dt>'WordFrequency[$text$, $word$]'
      <dd>returns the relative frequency of $word$ in $text$.
    </dl>

    $word$ may also specify multiple words using $a$ | $b$ | ...

    ## Problem with import for certain characters in the text.
    ## >> text = Import["ExampleData/EinsteinSzilLetter.txt"];
    >> text = "I have a dairy cow, it's not just any cow. \
       She gives me milkshake, oh what a salty cow. She is the best\
       cow in the county.";
    >> WordFrequency[text, "a" | "the"]
     = 0.114286

    >> WordFrequency["Apple Tree", "apple", IgnoreCase -> True]
     = 0.5
    """

    options = _SpacyBuiltin.options
    options.update({"IgnoreCase": "False"})

    def eval(self, text: String, word, evaluation: Evaluation, options: dict):
        "WordFrequency[text_String, word_, OptionsPattern[%(name)s]]"
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
            text = token.text
            if ignore_case:
                text = text.lower()
            if text in words:
                n += 1
        return Expression(SymbolN, Integer(n) / Integer(len(doc)))


class Containing(Builtin):
    pass


def _cases(doc, form):
    if isinstance(form, String):
        generators = [_forms.get(form.value)]
    elif form.get_head_name() == "System`Alternatives":
        if not all(isinstance(f, String) for f in form.elements):
            return  # error
        generators = [_forms.get(f.value) for f in form.elements]
    elif form.get_head_name() == "PyMathics`Containing":
        if len(form.elements) == 2:
            for t in _containing(doc, *form.elements):
                yield t
            return
        else:
            return  # error
    else:
        return  # error

    def try_next(iterator):
        try:
            return next(iterator)
        except StopIteration:
            return None

    feeds = []
    for i, iterator in enumerate([iter(generator(doc)) for generator in generators]):
        t = try_next(iterator)
        if t:
            feeds.append((_position(t), i, t, iterator))
    heapq.heapify(feeds)
    while feeds:
        pos, i, token, iterator = heapq.heappop(feeds)
        yield token
        t = try_next(iterator)
        if t:
            heapq.heappush(feeds, (_position(t), i, t, iterator))


def _containing(doc, outer, inner):
    if not isinstance(outer, String):
        return  # error
    outer_generator = _forms.get(outer.value)
    inner_iter = _cases(doc, inner)
    inner_start = None
    produce_t = False
    try:
        for t in outer_generator(doc):
            start, end = _position(t)
            if inner_start is not None and inner_start < end:
                produce_t = True
            if produce_t:
                yield t
                produce_t = False
            while True:
                inner_start, inner_end = _position(next(inner_iter))
                if inner_end > start:
                    break
            if inner_start < end:
                produce_t = True
    except StopIteration:
        pass


class TextCases(_SpacyBuiltin):
    """
    <dl>
      <dt>'TextCases[$text$, $form$]'
      <dd>returns all elements of type $form$ in $text$ in order of their appearance.
    </dl>

    >> TextCases["I was in London last year.", "Pronoun"]
     = {I}

    >> TextCases["I was in London last year.", "City"]
     = {London}

    ## >> TextCases[Import["ExampleData/EinsteinSzilLetter.txt"], "Person", 3][[2;;3]]
    ##  = {L. Szilard, Joliot}

    >> TextCases["Anne, Peter and Mr Johnes say hello.", "Person", 3][[2;;3]]
     = {Peter, Johnes}

    """

    def eval_string_form(
        self, text: String, form, evaluation: Evaluation, options: dict
    ):
        "TextCases[text_String, form_,  OptionsPattern[%(name)s]]"
        doc = self._nlp(text.value, evaluation, options)
        if doc:
            return to_mathics_list(*[t.text for t in _cases(doc, form)])

    def eval_string_form_n(
        self, text: String, form, n: Integer, evaluation: Evaluation, options: dict
    ):
        "TextCases[text_String, form_, n_Integer,  OptionsPattern[%(name)s]]"
        doc = self._nlp(text.value, evaluation, options)
        if doc:
            return to_mathics_list(
                *itertools.islice((t.text for t in _cases(doc, form)), n.value)
            )


class TextPosition(_SpacyBuiltin):
    """
    <dl>
      <dt>'TextPosition[$text$, $form$]'
      <dd>returns the positions of elements of type $form$ in $text$ in order of their appearance.
    </dl>

    >> TextPosition["Liverpool and London are two English cities.", "City"]
     = {{1, 9}, {15, 20}}
    """

    def eval_text_form(self, text: String, form, evaluation: Evaluation, options: dict):
        "TextPosition[text_String, form_,  OptionsPattern[%(name)s]]"
        doc = self._nlp(text.value, evaluation, options)
        if doc:
            return to_mathics_list(*[_position(t) for t in _cases(doc, form)])

    def eval_text_form_n(
        self, text: String, form, n: Integer, evaluation: Evaluation, options: dict
    ):
        "TextPosition[text_String, form_, n_Integer,  OptionsPattern[%(name)s]]"
        doc = self._nlp(text.value, evaluation, options)
        if doc:
            return to_mathics_list(
                *itertools.islice((_position(t) for t in _cases(doc, form)), n.value)
            )


class TextStructure(_SpacyBuiltin):
    """
    <dl>
      <dt>'TextStructure[$text$, $form$]'
      <dd>returns the grammatical structure of $text$ as $form$.
    </dl>

    >> TextStructure["The cat sat on the mat.", "ConstituentString"]
     = {(Sentence, ((Verb Phrase, (Noun Phrase, (Determiner, The), (Noun, cat)), (Verb, sat), (Prepositional Phrase, (Preposition, on), (Noun Phrase, (Determiner, the), (Noun, mat))), (Punctuation, .))))}
    """

    _root_pos = set(i for i, names in _pos_tags.items() if names[1])

    def _to_constituent_string(self, node):
        token, children = node
        name, phrase_name = _pos_tags.get(token.pos, ("Unknown", "Unknown Phrase"))
        if not children:
            return "(%s, %s)" % (name, token.text)
        else:
            sub = ", ".join(
                self._to_constituent_string(next_node) for next_node in children
            )
            return "(%s, %s)" % (phrase_name, sub)

    def _to_tree(self, tokens, path=[]):
        roots = []
        i = 0
        while i < len(tokens):
            token = tokens[i]

            if token in path:
                roots.append((token, None))
                i += 1
            else:
                root = token
                while root.head != root and root.head not in path:
                    root = root.head

                sub = list(root.subtree)

                if root.pos not in self._root_pos:
                    roots.extend(self._to_tree(sub, path + [root]))
                else:
                    roots.append((root, self._to_tree(sub, path + [root])))

                i += len(sub)

        return roots

    def eval(self, text, evaluation: Evaluation, options: dict):
        'TextStructure[text_String, "ConstituentString",  OptionsPattern[%(name)s]]'
        doc = self._nlp(text.value, evaluation, options)
        if doc:
            tree = self._to_tree(list(doc))
            sents = ["(Sentence, (%s))" % self._to_constituent_string(x) for x in tree]
            return to_mathics_list(*sents, elements_conversion_fn=String)


class WordSimilarity(_SpacyBuiltin):
    """
    <dl>
      <dt>'WordSimilarity[$text1$, $text2$]'
      <dd>returns a real-valued measure of semantic similarity of two texts or words.

      <dt>'WordSimilarity[{$text1$, $i1$}, {$text2, $j1$}]'
      <dd>returns a measure of similarity of two words within two texts.

      <dt>'WordSimilarity[{$text1$, {$i1$, $i2$, ...}}, {$text2, {$j1$, $j2$, ...}}]'
      <dd>returns a measure of similarity of multiple words within two texts.
    </dl>

    >> NumberForm[WordSimilarity["car", "train"], 3]
     = 0.439

    >> NumberForm[WordSimilarity["car", "hedgehog"], 3]
     = 0.195

    >> NumberForm[WordSimilarity[{"An ocean full of water.", {2, 2}}, { "A desert full of sand.", {2, 5}}], 3]
     = {0.505, 0.481}
    """

    messages = _merge_dictionaries(
        _SpacyBuiltin.messages,
        {
            "txtidx": "Index `1` in position `2` must be between 1 and `3`.",
            "idxfmt": "Indices must be integers or lists of integers of the same length.",
        },
    )

    def eval(
        self, text1: String, text2: String, evaluation: Evaluation, options: dict
    ) -> Optional[Real]:
        "WordSimilarity[text1_String, text2_String, OptionsPattern[%(name)s]]"
        doc1 = self._nlp(text1.value, evaluation, options)
        if doc1:
            doc2 = self._nlp(text2.value, evaluation, options)
            if doc2:
                return Real(doc1.similarity(doc2))

    def eval_pair(self, text1, i1, text2, i2, evaluation: Evaluation, options: dict):
        "WordSimilarity[{text1_String, i1_}, {text2_String, i2_}, OptionsPattern[%(name)s]]"
        doc1 = self._nlp(text1.value, evaluation, options)
        if doc1:
            if text2.value == text1.value:
                doc2 = doc1
            else:
                doc2 = self._nlp(text2.value, evaluation, options)
            if doc2:
                if (
                    i1.get_head_name() == "System`List"
                    and i2.get_head_name() == "System`List"
                ):
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

    requires = ("nltk",)

    _stemmer = None

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


class _WordNetBuiltin(Builtin):
    requires = ("nltk",)

    options = {
        "Language": '"English"',
    }

    messages = {
        "package": "NLTK's `` corpus is not installed. Please install it using nltk.download().",
        "lang": 'Language "`1`" is currently not supported with `2`[]. Please install it manually.',
        # 'load': 'Loading `1` word data. Please wait.',
        "wordnet": "WordNet returned the following error: ``",
    }

    _wordnet_instances = {}

    def _language_name(self, evaluation: Evaluation, options: dict):
        return self.get_option(options, "Language", evaluation)

    def _init_wordnet(self, evaluation: Evaluation, language_name, language_code):
        try:
            wordnet_resource = nltk.data.find("corpora/wordnet2022")
            _init_nltk_maps()
        except LookupError:
            evaluation.message(self.get_name(), "package", "wordnet2022")
            return None

        try:
            omw = nltk.corpus.util.LazyCorpusLoader(
                "omw",
                nltk.corpus.reader.CorpusReader,
                r".*/wn-data-.*\.tab",
                encoding="utf8",
            )
        except LookupError:
            evaluation.message(self.get_name(), "package", "omw")
            return None

        wordnet = nltk.corpus.reader.wordnet.WordNetCorpusReader(wordnet_resource, omw)

        if language_code not in wordnet.langs():
            evaluation.message(
                self.get_name(), "lang", language_name, strip_context(self.get_name())
            )
            return None

        return wordnet

    def _load_wordnet(self, evaluation: Evaluation, language_name) -> tuple:
        language_code = None
        if isinstance(language_name, String):
            language_code = iso639_3.get(language_name.value)
        if not language_code:
            evaluation.message(
                self.get_name(), "lang", language_name, strip_context(self.get_name())
            )
            return None, None

        wordnet = _WordNetBuiltin._wordnet_instances.get(language_code)
        if not wordnet:
            try:
                wordnet = self._init_wordnet(evaluation, language_name, language_code)
            except LookupError as e:
                evaluation.message(
                    self.get_name(), "package", _parse_nltk_lookup_error(e)
                )
                return None, None

            _WordNetBuiltin._wordnet_instances[language_code] = wordnet

        return wordnet, language_code

    @staticmethod
    def _decode_synset(syn):
        what, pos, nr = (syn.name().split(".") + ["01"])[:3]
        return what.replace("_", " "), pos, nr

    @staticmethod
    def _capitalize(s) -> str:
        return re.sub(r"^[a-z]|\s[a-z]", lambda m: m.group(0).upper().lstrip(" "), s)

    @staticmethod
    def _underscore(s) -> str:
        return re.sub(
            r"[a-z][A-Z]", lambda m: m.group(0)[0] + "_" + m.group(0)[1].lower(), s
        ).lower()

    @staticmethod
    def _list_syn_form(syn):
        what, pos, nr = _WordNetBuiltin._decode_synset(syn)

        def containers():
            for name in syn.lemma_names():
                if name != what:
                    yield name

            for s in chain(syn.hypernyms(), syn.hyponyms(), syn.similar_tos()):
                container, _, _ = _WordNetBuiltin._decode_synset(s)
                yield container

            for lemma in WordProperty._synonymous_lemmas(syn):
                yield lemma.name()

        return what, _wordnet_pos_to_type[pos], containers

    @staticmethod
    def syn(syn, wordnet, language_code) -> tuple:
        what, pos, nr = _WordNetBuiltin._decode_synset(syn)
        for s, form in _WordNetBuiltin._iterate_senses(what, wordnet, language_code):
            if s == syn:
                return form
        return what, pos, "Unknown"

    @staticmethod
    def _iterate_senses(word, wordnet, language_code):
        if not word:
            return

        used = set()
        output_word = word.replace("_", " ")

        for syn in wordnet.synsets(word, None, language_code):
            if syn.lexname() in ("noun.location", "noun.person"):
                continue  # ignore

            what, pos, containers = _WordNetBuiltin._list_syn_form(syn)

            for container in containers():
                container = container.replace("_", " ")
                if container != word:
                    if container not in used:
                        used.add(container)
                        yield syn, (
                            output_word,
                            pos,
                            _WordNetBuiltin._capitalize(container),
                        )
                        break

    def _senses(self, word, wordnet, language_code):
        if isinstance(word, tuple):  # find forms like ["tree", "Noun", "WoodyPlant"]
            for syn, form in _WordNetBuiltin._iterate_senses(
                word[0], wordnet, language_code
            ):
                if form == word:
                    return [[syn, form]]
        else:  # find word given as strings, e.g. "tree"
            word = wordnet.morphy(word)  # base form, e.g. trees -> tree
            return list(_WordNetBuiltin._iterate_senses(word, wordnet, language_code))


class WordDefinition(_WordNetBuiltin):
    """
    <dl>
      <dt>'WordDefinition[$word$]'
      <dd>returns a definition of $word$ or Missing["Available"] if $word$ is not known.
    </dl>

    >> WordDefinition["gram"]
     = {a metric unit of weight equal to one thousandth of a kilogram}
    """

    def eval(self, word, evaluation: Evaluation, options: dict):
        "WordDefinition[word_String, OptionsPattern[%(name)s]]"
        wordnet, language_code = self._load_wordnet(
            evaluation, self._language_name(evaluation, options)
        )
        if wordnet:
            senses = self._senses(word.value.lower(), wordnet, language_code)
            if senses:
                return ListExpression(*[String(syn.definition()) for syn, _ in senses])
            else:
                return Expression(SymbolMissing, "NotAvailable")


class WordProperty:
    def __init__(self, syn_form, wordnet, language_code):
        self.syn_form = syn_form
        self.wordnet = wordnet
        self.language_code = language_code

    def syn(self, syn):
        return self.syn_form(_WordNetBuiltin.syn(syn, self.wordnet, self.language_code))

    @staticmethod
    def _synonymous_lemmas(syn):
        first_lemma = syn.name().split(".")[0]
        return (s for s in syn.lemmas() if s.name() != first_lemma)

    @staticmethod
    def _antonymous_lemmas(syn):
        return (s for lemma in syn.lemmas() for s in lemma.antonyms())

    def definitions(self, syn, desc):
        return syn.definition()

    def examples(self, syn, desc):
        return syn.examples()

    def synonyms(self, syn, desc):
        _, pos, container = desc
        return [
            self.syn_form((s.name().replace("_", " "), pos, container))
            for s in WordProperty._synonymous_lemmas(syn)
        ]

    def antonyms(self, syn, desc):
        return [self.syn(s.synset()) for s in WordProperty._antonymous_lemmas(syn)]

    def broader_terms(self, syn, desc):
        return [self.syn(s) for s in syn.hypernyms()]

    def narrower_terms(self, syn, desc):
        return [self.syn(s) for s in syn.hyponyms()]

    def usage_field(self, syn, desc):
        return syn.usage_domains()

    def whole_terms(self, syn, desc):
        return [self.syn(s) for s in syn.part_holonyms()]

    def part_terms(self, syn, desc):
        return [self.syn(s) for s in syn.part_meronyms()]

    def material_terms(self, syn, desc):
        return [self.syn(s) for s in syn.substance_meronyms()]

    def word_net_id(self, syn, desc):
        return syn.offset()

    def entailed_terms(self, syn, desc):  # e.g. fall to condense
        return [self.syn(s) for s in syn.entailments()]

    def causes_terms(self, syn, desc):  # e.g. ignite to burn
        return [self.syn(s) for s in syn.causes()]

    def inflected_forms(self, syn, desc):
        try:
            word, pos, _ = desc
            if pos == "Verb":
                from pattern.en import lexeme

                return [w for w in reversed(lexeme(word)) if w != word]
            elif pos == "Noun":
                from pattern.en import pluralize

                return [pluralize(word)]
            elif pos == "Adjective":
                from pattern.en import comparative, superlative

                return [comparative(word), superlative(word)]
            else:
                return []
        except ImportError:
            raise MessageException(
                "General", "unavailable", 'WordData[_, "InflectedForms"]', "pattern"
            )


class _WordListBuiltin(_WordNetBuiltin):
    _dictionary = {}

    def _words(self, language_name, ilk, evaluation):
        wordnet, language_code = self._load_wordnet(evaluation, language_name)

        if not wordnet:
            return

        key = "%s.%s" % (language_code, ilk)
        words = self._dictionary.get(key)
        if not words:
            try:
                if ilk == "All":
                    filtered_pos = [None]
                else:
                    try:
                        filtered_pos = _wordnet_type_to_pos[ilk]
                    except KeyError:
                        evaluation.message(
                            self.get_name(),
                            "wordnet",
                            "type: %s is should be in %s"
                            % (ilk._wordnet_type_to_pos.keys()),
                        )
                        return

                words = []
                for pos in filtered_pos:
                    words.extend(list(wordnet.all_lemma_names(pos, language_code)))
                words.sort()
                self._dictionary[key] = words
            except nltk.corpus.reader.wordnet.WordNetError as err:
                evaluation.message(self.get_name(), "wordnet", str(err))
                return

        return words


class WordData(_WordListBuiltin):
    """
    <dl>
      <dt>'WordData[$word$]'
      <dd>returns a list of possible senses of a word.

      <dt>'WordData[$word$, $property$]'
      <dd>returns detailed information about a word regarding $property$, e.g. "Definitions" or "Examples".
    </dl>

    The following are valid properties:
    - Definitions, Examples
    - InflectedForms
    - Synonyms, Antonyms
    - BroaderTerms, NarrowerTerms
    - WholeTerms, PartTerms, MaterialTerms
    - EntailedTerms, CausesTerms
    - UsageField
    - WordNetID
    - Lookup

    ## Not working yet
    ## >> WordData["riverside", "Definitions"]
    ## = {{riverside, Noun, Bank} -> the bank of a river}

    ## >> WordData[{"fish", "Verb", "Angle"}, "Examples"]
    ## = {{fish, Verb, Angle} -> {fish for compliments}}
    """

    messages = _merge_dictionaries(
        _WordNetBuiltin.messages,
        {
            "notprop": "WordData[] does not recognize `1` as a valid property.",
        },
    )

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
            return Expression(SymbolMissing, "NotAvailable")
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
                word_property, "%s" % self._underscore(py_property), None
            )
            if property_getter:
                list_expr_elements = [
                    Expression(SymbolRule, desc, *property_getter(syn, desc))
                    for syn, desc in senses
                ]
                return ListExpression(*list_expr_elements)
        evaluation.message(self.get_name(), "notprop", property)

    def _parts_of_speech(self, py_word, wordnet, language_code):
        parts = set(
            syn.pos() for syn, _ in self._senses(py_word, wordnet, language_code)
        )
        if not parts:
            return Expression(SymbolMissing, "NotAvailable")
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

    def eval(self, word, evaluation: Evaluation, options: dict):
        "WordData[word_, OptionsPattern[%(name)s]]"
        if word.get_head_name() == "System`StringExpression":
            return Expression(SymbolDictionaryLookup, word)
        elif isinstance(word, String) or word.get_head_name() == "System`List":
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
        return ListExpression(*[[String(s) for s in desc] for syn, desc in senses])

    def eval_property(self, word, property, evaluation: Evaluation, options: dict):
        "WordData[word_, property_String, OptionsPattern[%(name)s]]"
        if word.get_head_name() == "System`StringExpression":
            if property.get_string_value() == "Lookup":
                return Expression(SymbolDictionaryLookup, word)
        elif isinstance(word, String) or word.get_head_name() == "System`List":
            return self._property(
                word, property.get_string_value(), "ShortRules", evaluation, options
            )

    def eval_property_form(
        self, word, property, form, evaluation: Evaluation, options: dict
    ):
        "WordData[word_, property_String, form_String, OptionsPattern[%(name)s]]"
        if isinstance(word, String) or word.get_head_name() == "System`List":
            return self._property(
                word,
                property.value,
                form.value,
                evaluation,
                options,
            )


class DictionaryWordQ(_WordNetBuiltin):
    """
    <dl>
      <dt>'DictionaryWordQ[$word$]'
      <dd>returns True if $word$ is a word usually found in dictionaries, and False otherwise.
    </dl>

    >> DictionaryWordQ["couch"]
     = True

    >> DictionaryWordQ["meep-meep"]
     = False
    """

    def eval(self, word, evaluation: Evaluation, options: dict):
        "DictionaryWordQ[word_String,  OptionsPattern[%(name)s]]"
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


class DictionaryLookup(_WordListBuiltin):
    """
    <dl>
      <dt>'DictionaryLookup[$word$]'
      <dd>lookup words that match the given $word$ or pattern.

    <dt>'DictionaryLookup[$word$, $n$]'
      <dd>lookup first $n$ words that match the given $word$ or pattern.
    </dl>

    >> DictionaryLookup["bake" ~~ ___, 3]
     = {bake, bakeapple, baked}
    """

    def compile(self, pattern, evaluation):
        re_patt = to_regex(pattern, evaluation)
        if re_patt is None:
            evaluation.message(
                "StringExpression",
                "invld",
                pattern,
                Expression("StringExpression", pattern),
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
            if dictionary_words:
                matches = self.search(dictionary_words, pattern)
                if n is not None:
                    matches = itertools.islice(matches, 0, n)
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


class WordList(_WordListBuiltin):
    """
    <dl>
      <dt>'WordList[]'
      <dd>returns a list of common words.

      <dt>'WordList[$type$]'
      <dd>returns a list of common words of type $type$.
    </dl>

    >> N[Mean[StringLength /@ WordList["Adjective"]], 2]
     = 9.3
    """

    def eval(self, evaluation: Evaluation, options: dict):
        "WordList[OptionsPattern[%(name)s]]"
        words = self._words(self._language_name(evaluation, options), "All", evaluation)
        if words:
            return to_mathics_list(*words, elements_conversion_fn=String)

    def eval_type(self, wordtype, evaluation: Evaluation, options: dict):
        "WordList[wordtype_String, OptionsPattern[%(name)s]]"
        words = self._words(
            self._language_name(evaluation, options),
            wordtype.value,
            evaluation,
        )
        if words:
            return to_mathics_list(*words, elements_conversion_fn=String)


class RandomWord(_WordListBuiltin):
    """
    <dl>
      <dt>'RandomWord[]'
      <dd>returns a random word.

      <dt>'RandomWord[$type$]'
      <dd>returns a random word of the given $type$, e.g. of type "Noun" or "Adverb".

      <dt>'RandomWord[$type$, $n$]'
      <dd>returns $n$ random words of the given $type$.
    </dl>
    """

    def _random_words(self, type, n, evaluation: Evaluation, options: dict):
        words = self._words(self._language_name(evaluation, options), type, evaluation)
        with RandomEnv(evaluation) as rand:
            return [
                String(words[rand.randint(0, len(words) - 1)].replace("_", " "))
                for _ in range(n)
            ]

    def eval(self, evaluation: Evaluation, options: dict):
        "RandomWord[OptionsPattern[%(name)s]]"
        words = self._random_words("All", 1, evaluation, options)
        if words:
            return words[0]

    def eval_type(self, type, evaluation: Evaluation, options: dict):
        "RandomWord[type_String, OptionsPattern[%(name)s]]"
        words = self._random_words(type.value, 1, evaluation, options)
        if words:
            return words[0]

    def eval_type_n(self, type, n, evaluation: Evaluation, options: dict):
        "RandomWord[type_String, n_Integer, OptionsPattern[%(name)s]]"
        words = self._random_words(type.value, n.value, evaluation, options)
        if words:
            return ListExpression(*words)


class LanguageIdentify(Builtin):
    """
    <dl>
    <dt>'LanguageIdentify[$text$]'
      <dd>returns the name of the language used in $text$.
    </dl>

    >> LanguageIdentify["eins zwei drei"]
     = German
    """

    requires = (
        "langid",
        "pycountry",
    )

    def eval(self, text: String, evaluation: Evaluation) -> Union[Symbol, String]:
        "LanguageIdentify[text_String]"
        import langid  # see https://github.com/saffsd/langid.py

        # an alternative: https://github.com/Mimino666/langdetect
        import pycountry

        code, _ = langid.classify(text.value)
        language = pycountry.languages.get(alpha_2=code)
        if language is None:
            return SymbolFailed
        return String(language.name)


class Pluralize(Builtin):
    """
    <dl>
    <dt>'Pluralize[$word$]'
      <dd>returns the plural form of $word$.
    </dl>

    >> Pluralize["potato"]
     = potatoes
    """

    requires = ("pattern",)

    def eval(self, word, evaluation):
        "Pluralize[word_String]"
        from pattern.en import pluralize

        return String(pluralize(word.value))


class SpellingCorrectionList(Builtin):
    """
    <dl>
    <dt>'SpellingCorrectionList[$word$]'
      <dd>returns a list of suggestions for spelling corrected versions of $word$.
    </dl>

    Results may differ depending on which dictionaries can be found by enchant.

    >> SpellingCorrectionList["hipopotamus"]
     = {hippopotamus...}
    """

    requires = ("enchant",)

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

    def eval(
        self, word: String, evaluation: Evaluation, options: dict
    ) -> Optional[ListExpression]:
        "SpellingCorrectionList[word_String, OptionsPattern[%(name)s]]"
        import enchant

        language_name = self.get_option(options, "Language", evaluation)
        if not isinstance(language_name, String):
            return
        language_code = SpellingCorrectionList._languages.get(language_name.value, None)
        if not language_code:
            return evaluation.message("SpellingCorrectionList", "lang", language_name)

        d = SpellingCorrectionList._dictionaries.get(language_code, None)
        if not d:
            d = enchant.Dict(language_code)
            SpellingCorrectionList._dictionaries[language_code] = d

        py_word = word.value

        if d.check(py_word):
            return ListExpression(word)
        else:
            return to_mathics_list(*d.suggest(py_word), elements_conversion_fn=String)
