import glob
import importlib
import os
import os.path as osp
import pkgutil

import pytest

from types import ModuleType
from typing import Dict

from mathics.core.load_builtin import name_is_builtin_symbol
from mathics.core.builtin import Builtin
from mathics.doc.gather import skip_doc

from pymathics.natlang import __file__ as module_initfile_path

# Get file system path name for mathics.builtin
module_path = osp.dirname(module_initfile_path)
module_builtins_path = module_path

CHECK_GRAMMAR = False

local_vocabulary = (
    "Mathics",
    "$Aborted",
    "Chebyshev",
    "Pochhammer",
    "Hankel",
    "Glaiser",
    "kth",
    "Struvel",
    "Polygamma",
    "Stieltjes",
    "Gegenbauer",
    "Bessel",
    "Laguerre",
    "Airy",
    "polygamma",
    "ker",
    "kei",
    "ber",
    "bei",
    "n-th",
    "i-th",
    "q-th",
    "th",
    "downvalues",
    "upvalues",
    "ownvalue",
    "subvalues",
    "machine-precision",
    "CompiledFunction",
    "CompiledObject",
    "ExactNumberQ",
    "quantile",
    "BeginPackage",
    "SetDirectory",
    "Begin",
    "sympy",
)

language_tool = None
if CHECK_GRAMMAR:
    try:
        import language_tool_python  # type: ignore[import-not-found]

        language_tool = language_tool_python.LanguageToolPublicAPI("en-US")
        # , config={ 'cacheSize': 1000, 'pipelineCaching': True })
    except Exception:
        pass

module_subdirs = tuple()

__py_files__ = [
    osp.basename(f[0:-3]) for f in glob.glob(osp.join(module_path, "[a-z]*.py"))
]


def import_module(module_name: str):
    try:
        module = importlib.import_module("pymathics.natlang." + module_name)
    except Exception as e:
        print(e)
        return None

    modules[module_name] = module


# exclude_files = set(("codetables", "base"))
module_names = [f for f in __py_files__]


for subdir in module_subdirs:
    import_name = f"pymathics.natlang.{subdir}"
    builtin_module = importlib.import_module(import_name)
    for importer, modname, ispkg in pkgutil.iter_modules(builtin_module.__path__):
        module_names.append(f"{subdir}.{modname}")


modules: Dict[str, ModuleType] = dict()
for module_name in module_names:
    import_module(module_name)

# modules = {"compilation": modules["compilation"],}


def check_grammar(text: str):
    assert language_tool is not None
    matches = language_tool.check(text)
    filtered_matches = []
    if matches:
        for m in matches:
            if m.message == "Possible spelling mistake found.":
                offset = m.offset
                sentence = m.sentence
                length = m.errorLength
                word = sentence[offset : offset + length]
                if word in local_vocabulary:
                    continue
                print(f"<<{word}>> misspelled? not in {local_vocabulary}")
            filtered_matches.append(m)
    if not filtered_matches:
        return True
    for msg in filtered_matches:
        print("\t", msg)
    return False


def check_well_formatted_docstring(docstr: str, instance: Builtin, module_name: str):
    assert (
        docstr.count("<dl>") >= 1
    ), f"missing <dl> </dl> tags in {instance.get_name()} from {module_name}"
    assert docstr.count("</dl>") == docstr.count(
        "<dl>"
    ), f"unbalanced <dl> </dl> tags in {instance.get_name()} from {module_name}"
    assert (
        docstr.count("<dt>") > 0
    ), f"missing <dt> field {instance.get_name()} from {module_name}"
    assert (
        docstr.count("<dd>") > 0
    ), f"missing <dd> field {instance.get_name()} from {module_name}"
    assert (
        docstr.count("</dt>") == 0
    ), f"unnecessary </dt> {instance.get_name()} from {module_name}"
    assert (
        docstr.count("</dd>") == 0
    ), f"unnecessary </dd> field {instance.get_name()} from {module_name}"

    assert (
        docstr.count("<url>") > 0
    ), f"missing <url> field {instance.get_name()} from {module_name}"
    assert docstr.count("<url>") == docstr.lower().count(
        "</url>"
    ), f"unbalanced <url> </url> tags in {instance.get_name()} from {module_name}"


@pytest.mark.skipif(
    not os.environ.get("MATHICS_LINT"),
    reason="Checking done only when MATHICS_LINT=t specified",
)
@pytest.mark.parametrize(
    ("module_name",),
    [(module_name,) for module_name in modules],
)
# @pytest.mark.skip("not ready")
def test_summary_text_available(module_name):
    """
    Checks that each Builtin has its summary_text property.
    """
    grammar_OK = True
    module = modules[module_name]
    if hasattr(module, "no_doc") and module.no_doc is True:
        return
    vars = dir(module)
    for name in vars:
        var = name_is_builtin_symbol(module, name)
        if var is None:
            continue
        print("processing ", [module, name, var])
        instance = var(expression=False)
        if not isinstance(instance, Builtin):
            continue

        if skip_doc(instance.__class__):
            continue

        # For private / internal symbols,
        # the documentation is optional.
        if "Internal`" in instance.context or "Private`" in instance.context:
            continue

        # check for a summary text
        assert hasattr(instance, "summary_text"), (
            f"{var.__name__} in {module_name} " "does not have a summary_text property"
        )
        # Check for docstrings
        docstring = instance.__doc__
        assert (
            docstring is not None
        ), f"empty docstring in {instance.get_name()} from {module_name}"
        check_well_formatted_docstring(docstring, instance, module_name)

        if language_tool and CHECK_GRAMMAR:
            full_summary_text = instance.summary_text.strip()
            full_summary_text = full_summary_text[0].upper() + full_summary_text[1:]
            full_summary_text = full_summary_text + "."
            full_summary_text = full_summary_text.replace(" n ", " two ")
            if not check_grammar(full_summary_text):
                grammar_OK = False
    assert grammar_OK
