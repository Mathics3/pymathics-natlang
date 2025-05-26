# -*- coding: utf-8 -*-

import os
import sys

from setuptools import setup
from setuptools.command.egg_info import egg_info

# Full package name with two-letter language code, e.g. fr, zh
lang = os.environ.get("lang", "en_core_web_md")

# Size of wordlist used
# sm=small, lg=large, md=medium.
WORDLIST_SIZE = os.environ.get("WORDLIST_SIZE", "md")

SPACY_DOWNLOAD = os.environ.get("SPACY_DOWNLOAD", lang)


class CustomCommands(egg_info):
    """This runs as part of building an sdist"""

    def finalize_options(self):
        """Run program to create JSON tables"""
        os.system(f"{sys.executable} -m spacy download {lang}")
        os.system(f"{sys.executable} -m nltk.downloader 'wordnet2022 omw")
        super().finalize_options()


# FIXME:
# consider using langid3 and pyenchant

setup(
    cmdclass={"egg_info": CustomCommands},
    zip_safe=False,
)
