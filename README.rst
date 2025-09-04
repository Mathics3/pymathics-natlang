|Pypi Installs| |Latest Version| |Supported Python Versions|

Mathics3 Natural Language Toolkit module.


Example Session
---------------

::

   $ mathicsscript
   In[1]:= LoadModule["pymathics.natlang"]
   Out[1]= pymathics.natlang
   In[2]= Pluralize["try"]
   Out[2]= tries
   In[3]= WordFrequency["Apple Tree and apple", "apple", IgnoreCase -> True]
   Out[3]= 0.5
   In[4] = TextCases["I was in London last year.", "Pronoun"]
   Out[4]= {I}
   In[5] = LanguageIdentify["eins zwei drei"]
   Out[4]= "German"

More examples can be found in the `test file <https://github.com/Mathics3/Mathics3-Module-nltk/blob/master/test/test_nltk.py>`_.

Installing and Running
----------------------

To build this Mathics3 module, you will need to install the Python module `nltk
<https://pypi.org/project/nltk/>`_ and `spacy
<https://pypi.org/project/spacy/>`_, and then install some data from
Language-specific words:

::

   $ make develop  # or make install

The above ``make`` command defaults to the English. If
you would like to install for another language, set the variable
``LANG``. For example:

::

   $ make develop LANG=fr

To use the Extended Open Multilingual Wordnet with NLTK and use even more languages, you need to install them manually. Go to
`<http://compling.hss.ntu.edu.sg/omw/summx.html>`_, download the data,
and then create a new folder under
``$HOME/nltk_data/corpora/omw/your_language`` where you put the file
from wiki/wn-wikt-your_language.tab, and rename it to
wn-data-your_language.tab.

If you get the message

::

   OSError: [E050] Can't find model 'en'. It doesn't seem to be a shortcut link, a Python package or a valid path to a data directory.

There is a problem with the ``spacy``library for advanced Natural Language Processing in Python.

You might be able to fix this by running:

::

   python -m spacy download en

Adjust "python" and "en" (the language you want) above as needed.


User customization
------------------

.. reinstate after this is fixed in the code
.. For nltk, use the environment variable ``NLTK_DATA`` to specify a custom data path (instead of $HOME/.nltk).  For spacy, set 'MATHICS3_SPACY_DATA', a Mathics3-specific variable.

To use the Extended Open Multilingual Wordnet (OMW) with 'NLTK' and use even more languages, you need to install them manually.

Go to http://compling.hss.ntu.edu.sg/omw/summx.html, download the data, and then create a new folder under
``$HOME/nltk_data/corpora/omw/your_language`` where you put the file from
wiki/wn-wikt-your_language.tab, and rename it to
wn-data-your_language.tab.

Adding more languages to Open Multilingual Wordnet:

To use the Extended Open Multilingual Wordnet with NLTK and use even more languages, you need to install them manually. Go to
http://compling.hss.ntu.edu.sg/omw/summx.html, download the data, and then create a new folder under
$HOME/nltk_data/corpora/omw/your_language where you put the file from
wiki/wn-wikt-your_language.tab, and rename it to
wn-data-your_language.tab.



.. |Latest Version| image:: https://badge.fury.io/py/Mathics3-Module-nltk.svg
		 :target: https://badge.fury.io/py/Mathics3-Module-nltk
.. |Pypi Installs| image:: https://pepy.tech/badge/Mathics3-Module-nltk
.. |Supported Python Versions| image:: https://img.shields.io/pypi/pyversions/Mathics3-Module-nltk.svg
.. |Packaging status| image:: https://repology.org/badge/vertical-allrepos/Mathics3-Module-nltk.svg
			    :target: https://repology.org/project/Mathics3-Module-nltk/versions
