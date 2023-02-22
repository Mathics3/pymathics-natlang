# -*- coding: utf-8 -*-

"""
nltk backend
"""
import re
from itertools import chain

import nltk
from mathics.builtin.base import Builtin, MessageException
from mathics.builtin.codetables import iso639_3
from mathics.core.atoms import String
from mathics.core.evaluation import Evaluation
from mathics.core.symbols import strip_context

no_doc = True


_wordnet_pos_to_type = {}
_wordnet_type_to_pos = {}


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


def _parse_nltk_lookup_error(e):
    m = re.search(r"Resource '([^']+)' not found\.", str(e))
    if m:
        return m.group(1)
    else:
        return "unknown"


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
                            "type: %s should be in %s"
                            % (ilk, _wordnet_type_to_pos.keys()),
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
