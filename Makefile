# A GNU Makefile to run various tasks - compatibility for us old-timers.

# Note: This makefile include remake-style target comments.
# These comments before the targets start with #:
# remake --tasks to shows the targets and the comments

GIT2CL ?= admin-tools/git2cl
PYTHON ?= python3
PIP ?= $(PYTHON) -m pip
RM  ?= rm

# Two-letter language code, e.g. fr, zh
lang ?= en

# Size of wordlist used
# sm=small, lg=large, md=medium.
WORDLIST_SIZE ?= md
SPACY_DOWNLOAD ?= $(lang)_core_web_$(WORDLIST_SIZE)

.PHONY: all build \
   check clean \
   develop dist doc doc-data \
   pypi-setup \
   pytest \
   rmChangeLog \
   test

#: Default target - same as "develop"
all: develop

#: Word-list data. Customize with lang and eventually WORDLIST_SIZE variables
wordlist:
	$(PYTHON) -m nltk.downloader wordnet omw-1.4
	$(PYTHON) -m spacy download $(SPACY_DOWNLOAD)

#: build everything needed to install
build: pypi-setup
	$(PYTHON) ./setup.py build

#: Check Python version, and install PyPI dependencies
pypi-setup:
	$(PIP) install -e .

#: Set up to run from the source tree
develop: pypi-setup
	$(MAKE) wordlist

#: Install pymathics.natlang
install: pypi-setup
	$(PYTHON) setup.py install

#: Run tests
test check: pytest doctest

#: Remove derived files
clean: clean-pyc

#: Remove old PYC files
clean-pyc:
	@find . -name "*.pyc" -type f -delete

#: Run py.test tests. Use environment variable "o" for pytest options
pytest:
	$(PYTHON) -m pytest test $o


# #: Create data that is used to in Django docs and to build TeX PDF
# doc-data mathics/doc/tex/data: mathics/builtin/*.py mathics/doc/documentation/*.mdoc mathics/doc/documentation/images/*
# 	$(PYTHON) mathics/test.py -ot -k

#: Run tests that appear in docstring in the code.


doctest:
	MATHICS_CHARACTER_ENCODING="ASCII" $(PYTHON) -m mathics.docpipeline -l pymathics.natlang $o


# #: Make Mathics PDF manual
# doc mathics.pdf: mathics/doc/tex/data
# 	(cd mathics/doc/tex && $(MAKE) mathics.pdf)

#: Remove ChangeLog
rmChangeLog:
	$(RM) ChangeLog || true

#: Create a ChangeLog from git via git log and git2cl
ChangeLog: rmChangeLog
	git log --pretty --numstat --summary | $(GIT2CL) >$@

#: Run pytest consistency and style checks
check-consistency-and-style:
	MATHICS_LINT=t $(PYTHON) -m pytest test/consistency-and-style
