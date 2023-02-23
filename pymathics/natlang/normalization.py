"""

Text Normalization

See the corresponding <url>
:WMA:
https://reference.wolfram.com/language/guide/TextNormalization.html</url> guide.


This module uses spacy as a backend.
"""
import itertools
from itertools import islice
from typing import Optional

import spacy
from mathics.core.atoms import Integer, String
from mathics.core.convert.python import from_python
from mathics.core.evaluation import Evaluation
from mathics.core.list import ListExpression

from pymathics.natlang.spacy import _cases, _pos_tags, _position, _SpacyBuiltin

sort_order = "Text Normalization"


class DeleteStopwords(_SpacyBuiltin):
    """
    Delete <url>:stop words:https://en.wikipedia.org/wiki/Stop_word</url>(\
    <url>:WMA:
    https://reference.wolfram.com/language/ref/DeleteStopwords.html</url>\
    )

    <dl>
      <dt>'DeleteStopwords[$list$]'
      <dd>returns the words in $list$ without stopwords.

      <dt>'DeleteStopwords[$string$]'
      <dd>returns $string$ without stopwords.
    </dl>

    ## This has changed since old versions of natlang, and I am
    ## not sure the old behavior was correct.
    >> DeleteStopwords[{"Somewhere", "over", "the", "rainbow"}]
     = ...
    ## = {rainbow}

    >> DeleteStopwords["There was an Old Man of Apulia, whose conduct was very peculiar"]
     = Old Man Apulia, conduct peculiar
    """

    summary_text = "remove stopwords from a text"

    def eval_list(self, li, evaluation: Evaluation, options: dict) -> ListExpression:
        "DeleteStopwords[li_List, OptionsPattern[DeleteStopwords]]"
        is_stop = self._is_stop_lambda(evaluation, options)

        def filter_words(words):
            for w in words:
                s = w.get_string_value()
                if s is not None:
                    yield String(s)
                elif is_stop is not None and is_stop(s) is not None:
                    yield String(s)

        return ListExpression(*list(filter_words(li.elements)))

    def eval_string(self, s: String, evaluation: Evaluation, options: dict):
        "DeleteStopwords[s_String, OptionsPattern[DeleteStopwords]]"
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


class TextCases(_SpacyBuiltin):
    """
    <url>:WMA link:
    https://reference.wolfram.com/language/ref/TextCases.html</url>

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

    summary_text = "list cases of words of a certain form in a text"

    def eval_string_form(
        self, text: String, form, evaluation: Evaluation, options: dict
    ):
        "TextCases[text_String, form_,  OptionsPattern[TextCases]]"
        doc = self._nlp(text.value, evaluation, options)
        if doc:
            return ListExpression(*[String(t.text) for t in _cases(doc, form)])

    def eval_string_form_n(
        self, text: String, form, n: Integer, evaluation: Evaluation, options: dict
    ):
        "TextCases[text_String, form_, n_Integer,  OptionsPattern[TextCases]]"
        doc = self._nlp(text.value, evaluation, options)
        if doc:
            items = islice((t.text for t in _cases(doc, form)), n.value)
            return ListExpression(*(from_python(item) for item in items))


class TextPosition(_SpacyBuiltin):
    """
    <url>:WMA link:
    https://reference.wolfram.com/language/ref/TextPosition.html</url>

    <dl>
      <dt>'TextPosition[$text$, $form$]'
      <dd>returns the positions of elements of type $form$ in $text$ in order of their appearance.
    </dl>

    >> TextPosition["Liverpool and London are two English cities.", "City"]
     = {{1, 9}, {15, 20}}
    """

    summary_text = "list the positions of words of a given form in a text"

    def eval_text_form(self, text: String, form, evaluation: Evaluation, options: dict):
        "TextPosition[text_String, form_,  OptionsPattern[TextPosition]]"
        doc = self._nlp(text.value, evaluation, options)
        if doc:
            return ListExpression(
                *[from_python(_position(t)) for t in _cases(doc, form)]
            )

    def eval_text_form_n(
        self, text: String, form, n: Integer, evaluation: Evaluation, options: dict
    ):
        "TextPosition[text_String, form_, n_Integer,  OptionsPattern[TextPosition]]"
        doc = self._nlp(text.value, evaluation, options)
        if doc:
            items = islice((_position(t) for t in _cases(doc, form)), n.value)
            return ListExpression(*(from_python(item) for item in items))


class TextSentences(_SpacyBuiltin):
    """
    <url>:Sentences:https://en.wikipedia.org/wiki/Sentence_(linguistics)</url>\
    in a text (\
    <url>:WMA:
    https://reference.wolfram.com/language/ref/TextSentences.html</url>\
    )


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

    summary_text = "list the sentences in a text"

    def eval(self, text: String, evaluation: Evaluation, options: dict):
        "TextSentences[text_String, OptionsPattern[TextSentences]]"
        doc = self._nlp(text.value, evaluation, options)
        if doc:
            return ListExpression(*[String(sent.text) for sent in doc.sents])

    def eval_n(self, text: String, n: Integer, evaluation: Evaluation, options: dict):
        "TextSentences[text_String, n_Integer, OptionsPattern[TextSentences]]"
        doc = self._nlp(text.value, evaluation, options)
        if doc:
            return ListExpression(
                *itertools.islice((String(sent.text) for sent in doc.sents), n.value),
            )


class TextStructure(_SpacyBuiltin):
    """
    <url>:WMA link:
    https://reference.wolfram.com/language/ref/TextStructure.html</url>

    <dl>
      <dt>'TextStructure[$text$, $form$]'
      <dd>returns the grammatical structure of $text$ as $form$.
    </dl>

    >> TextStructure["The cat sat on the mat.", "ConstituentString"]
     = {(Sentence, ((Verb Phrase, (Noun Phrase, (Determiner, The), (Noun, cat)), (Verb, sat), (Prepositional Phrase, (Preposition, on), (Noun Phrase, (Determiner, the), (Noun, mat))), (Punctuation, .))))}
    """

    _root_pos = set(i for i, names in _pos_tags.items() if names[1])
    summary_text = "retrieve the grammatical structure of a text"

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
        'TextStructure[text_String, "ConstituentString",  OptionsPattern[TextStructure]]'
        doc = self._nlp(text.value, evaluation, options)
        if doc:
            tree = self._to_tree(list(doc))
            sents = ["(Sentence, (%s))" % self._to_constituent_string(x) for x in tree]
            return ListExpression(*(String(sent) for sent in sents))


class TextWords(_SpacyBuiltin):
    """
    <url>:WMA link:
    https://reference.wolfram.com/language/ref/TextWords.html</url>

    <dl>
      <dt>'TextWords[$string$]'
      <dd>returns the words in $string$.

      <dt>'TextWords[$string$, $n$]'
      <dd>returns the first $n$ words in $string$
    </dl>

    >> TextWords["Hickory, dickory, dock! The mouse ran up the clock."]
     = {Hickory, dickory, dock, The, mouse, ran, up, the, clock}

    >> TextWords["Bruder Jakob, Schläfst du noch?", 2]
     = {Bruder, Jakob}

    """

    summary_text = "list the words in a string"

    def eval(
        self, text: String, evaluation: Evaluation, options: dict
    ) -> Optional[ListExpression]:
        "TextWords[text_String, OptionsPattern[]]"
        doc = self._nlp(text.value, evaluation, options)
        if doc:
            punctuation = spacy.parts_of_speech.PUNCT
            return ListExpression(
                *[String(word.text) for word in doc if word.pos != punctuation],
            )

    def eval_n(self, text: String, n: Integer, evaluation: Evaluation, options: dict):
        "TextWords[text_String, n_Integer, OptionsPattern[]]"
        doc = self._nlp(text.value, evaluation, options)
        if doc:
            punctuation = spacy.parts_of_speech.PUNCT
            return ListExpression(
                *itertools.islice(
                    (String(word.text) for word in doc if word.pos != punctuation),
                    n.value,
                ),
            )
