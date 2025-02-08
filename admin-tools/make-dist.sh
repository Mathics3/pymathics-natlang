#!/bin/bash
PACKAGE=pymathics_natlang

# FIXME put some of the below in a common routine
function finish {
  cd $mathics_natlang_owd
}

cd $(dirname ${BASH_SOURCE[0]})
mathics_natlang_owd=$(pwd)
trap finish EXIT

if ! source ./pyenv-versions ; then
    exit $?
fi


cd ..
source pymathics/natlang/version.py
echo $__version__

pyversion=3.12
if ! pyenv local $pyversion ; then
    exit $?
fi

python -m build
finish
