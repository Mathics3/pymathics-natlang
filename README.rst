|Pypi Installs| |Latest Version| |Supported Python Versions|

Mathics Natural Language Toolkit module.


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
   Out[3]= {I}

More examples can be found in the `test file <https://github.com/Mathics3/pymathics-natlang/blob/master/test/test_natlang.py>`_.

Installing and Running
----------------------

To use build module, you will need to install Python module `nltk
<https://pypi.org/project/nltk/>`_ and `spacy
<https://pypi.org/project/spacy/>`_, and then install some data from
Language-specific words:

::

   $ make develop  # or make install

The above ``make`` command uses defaults the language to English. If
you would like to install for another language set the variable
``LANG``. For example:

::

   $ make develop LANG=fr

In order to use the Extended Open Multilingual Wordnet with NLTK and
use even more languages, you need to install them manually. Go to
`<http://compling.hss.ntu.edu.sg/omw/summx.html>`_, download the data,
and then create a new folder under
``$HOME/nltk_data/corpora/omw/your_language`` where you put the file
from wiki/wn-wikt-your_language.tab, and rename it to
wn-data-your_language.tab.

If you get the message

::

   OSError: [E050] Can't find model 'en'. It doesn't seem to be a shortcut link, a Python package or a valid path to a data directory.

There is a problem with the ``spacy`` the library for advanced Natural Language Processing in Python.

You might be able to fix this running:

::

   python -m spacy download en

Adjust "python" and "en" (the language you want) above as needed.

.. |Latest Version| image:: https://badge.fury.io/py/pymathics-natlang.svg
		 :target: https://badge.fury.io/py/pymathics-natlang
.. |Pypi Installs| image:: https://pepy.tech/badge/pymathics-natlang
.. |Supported Python Versions| image:: https://img.shields.io/pypi/pyversions/pymathics-natlang.svg
.. |Packaging status| image:: https://repology.org/badge/vertical-allrepos/pymathics-natlang.svg
			    :target: https://repology.org/project/pymathics-natlang/versions
