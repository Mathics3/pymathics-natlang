Natural Language Tookkit module.

To use this module, you will need to install nltk and spacy,
Python modules and then install some data from English words:

::

   $ make develop

If you would like to install works for another language set the
variable ``LANG``. For example:

::

   $ make develop LANG=fr

In order to use the Extended Open Multilingual Wordnet with NLTK and
use even more languages, you need to install them manually. Go to
`<http://compling.hss.ntu.edu.sg/omw/summx.html>`_, download the data,
and then create a new folder under
``$HOME/nltk_data/corpora/omw/your_language`` where you put the file
from wiki/wn-wikt-your_language.tab, and rename it to
wn-data-your_language.tab.
