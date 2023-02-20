# -*- coding: utf-8 -*-

"""
Spacy tools

"""

# TODO: move here low-level implementation depending on spacy

import heapq
import re
from typing import Optional

import spacy
from mathics.builtin.base import Builtin
from mathics.core.atoms import String
from mathics.core.evaluation import Evaluation
from mathics.core.symbols import strip_context
from spacy.tokens import Span

no_doc = True

# Mathics3 named entitiy names and their corresponding constants in spacy.
symbols = {
    "Person": spacy.symbols.PERSON,
    "Company": spacy.symbols.ORG,
    "Quantity": spacy.symbols.QUANTITY,
    "Number": spacy.symbols.CARDINAL,
    "CurrencyAmount": spacy.symbols.MONEY,
    "Country": spacy.symbols.GPE,  # also includes cities and states
    "City": spacy.symbols.GPE,  # also includes countries and states
}

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


def _fragments(doc, sep):
    start = 0
    for i, token in enumerate(doc):
        if sep.match(token.text):
            yield Span(doc, start, i)
            start = i + 1
    end = len(doc)
    if start < end:
        yield Span(doc, start, end)


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

    for name, symbol in symbols.items():
        forms[name] = filter_named_entity(symbol)

    for tag, names in _pos_tags.items():
        name, phrase_name = names
        forms[name] = filter_pos(tag)

    return forms


# forms are everything one can use in TextCases[] or TextPosition[].
_forms = _make_forms()


def _position(t):
    if isinstance(t, Span):
        i = t.doc[t.start]
        r = t.doc[t.end - 1]
        return 1 + i.idx, r.idx + len(r.text)
    else:
        return 1 + t.idx, t.idx + len(t.text)


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
            instance = spacy.load(f"{language_code}_core_web_md")

            # "via" parameter no longer exists. This was used in MATHICS3_SPACY_DATA
            # if "MATHICS3_SPACY_DATA" in os.environ:
            #     instance = spacy.load(
            #         language_code, via=os.environ["MATHICS3_SPACY_DATA"]
            #     )
            # else:
            #     instance = spacy.load(f"{language_code}_core_web_md")

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
