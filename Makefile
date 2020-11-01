# A GNU Makefile to run various tasks - compatibility for us old-timers.

# Note: This makefile include remake-style target comments.
# These comments before the targets start with #:
# remake --tasks to shows the targets and the comments

GIT2CL ?= admin-tools/git2cl
PYTHON ?= python3
PIP ?= pip3
RM  ?= rm
LANG ?= en

# Size of wordlist used
# sm=small, lg=large, md=medium.
WORDLIST_SIZE ?=md

.PHONY: all build \
   check clean \
   develop dist doc doc-data \
   pytest \
   rmChangeLog \
   test

#: Default target - same as "develop"
all: develop

#: Word-list data. Customize with LANG (and eventually WORDLIST_SIZE) variables
wordlist:
	$(PYTHON) -m nltk.downloader wordnet omw
	$(PYTHON) -m spacy download $(LANG)
#	# $(PYTHON) -m spacy download $(LANG)_core_web_$(WORDLIST_SIZE)

#: build everything needed to install
build:
	$(PYTHON) ./setup.py build

#: Set up to run from the source tree
develop:
	$(PIP) install -e .
	$(MAKE) wordlist

#: Install mathics
install:
	$(PYTHON) setup.py install

check: pytest doctest djangotest gstest

#: Remove derived files
clean: clean-pyc

#: Remove old PYC files
clean-pyc:
	@find . -name "*.pyc" -type f -delete

#: Run py.test tests. Use environment variable "o" for pytest options
pytest:
	py.test test $o


# #: Create data that is used to in Django docs and to build TeX PDF
# doc-data mathics/doc/tex/data: mathics/builtin/*.py mathics/doc/documentation/*.mdoc mathics/doc/documentation/images/*
# 	$(PYTHON) mathics/test.py -ot -k

#: Run tests that appear in docstring in the code.
doctest:
	$(PYTHON) mathics/test.py $o

# #: Make Mathics PDF manual
# doc mathics.pdf: mathics/doc/tex/data
# 	(cd mathics/doc/tex && $(MAKE) mathics.pdf)

#: Remove ChangeLog
rmChangeLog:
	$(RM) ChangeLog || true

#: Create a ChangeLog from git via git log and git2cl
ChangeLog: rmChangeLog
	git log --pretty --numstat --summary | $(GIT2CL) >$@
