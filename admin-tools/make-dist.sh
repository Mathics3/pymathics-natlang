#!/bin/bash
PACKAGE=mathics3_module_nltk

# FIXME put some of the below in a common routine
function finish {
  cd $mathics3_module_nlkt_owd
}

cd $(dirname ${BASH_SOURCE[0]})
mathics3_module_nltk_owd=$(pwd)
trap finish EXIT

if ! source ./pyenv-versions ; then
    exit $?
fi


cd ..
source pymathics/natlang/version.py
echo $__version__

pyversion=3.13
if ! pyenv local $pyversion ; then
    exit $?
fi

pip wheel --wheel-dir=dist .
python -m build --sdist
finish
