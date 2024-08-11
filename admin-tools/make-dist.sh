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

pyversion=3.11
if ! pyenv local $pyversion ; then
    exit $?
fi

python setup.py bdist_wheel --universal
mv -v dist/${PACKAGE}-${__version__}-{py2.,}py3-none-any.whl
python ./setup.py sdist
finish
