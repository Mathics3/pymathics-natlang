CHANGES
=======

9.0.0
-----

Sept 1, 2025

* Add Python 3.13 support. Drop support for Python 3.8 and Python 3.9
* Update to 9.0.0 Mathics3 API
* Turn Document organization into a Guide section


8.0.1
-----

Feb 8, 2025

Documentation has been revised to make better use of TeX math mode.
Adjust and correct packaging.


8.0.0
-----

Jan 26, 2025

This release tracks the API changes in the Mathics Kernel.


Use the PyPI package ``PatternLite`` instead of the defunct 3.6-ish ``pattern`` (which has now been replaced with something totally different from NLP).



7.0.0
-----

Aug 10, 2025

* Revise for 7.0.0 Mathics3 API; we need to explicilty load builtins


6.0.0
-----

Revise for 6.0.0 Mathics3 APIs and current Mathics3 builtin standards described in `Guidelines for Writing
Documentation <https://mathics-development-guide.readthedocs.io/en/latest/extending/developing-code/extending/documentation-markup.html#guidelines-for-writing-documentation>`_.

This package has undergone a major overhaul. Modules have been split out along into logical groups following the documentation structure.

We have gradually been rolling in more Python type annotations and have been using current Python practices. Tools such as using ``isort``, ``black`` and ``flake8`` are used as well.

Evaluation methods of built-in functions start ``eval_`` not
``apply_``.

There is more refactoring more to do here, bugs that remain, functions needing adding or filling out.

We should assess the landscape for changes in modules that might be used here; there is probably something better maintained than ``langid``.


5.0.0
-----

* Adjust for Mathics3 core 5.0.0 API
* Use Spacy >= 3.4
* Adjust for medium word list dictated by package and newer Spacy

2.2.0
-----

Re-Release to use released Mathics 2.2.0

1.1.0
-----

Re-Release to use released Mathics 1.1.0

* tests added.
* README.rst has been updated with examples.

1.0.0
-----

First public release.
