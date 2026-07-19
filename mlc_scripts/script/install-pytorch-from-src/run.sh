#!/bin/bash

gcc()
{
  ${MLC_GCC_BIN_WITH_PATH} "$@"
}
export -f gcc

CUR_DIR=$PWD
if [[ ! -e pytorch/dist/torch*.whl ]]; then
  rm -rf pytorch
  cp -r ${MLC_PYTORCH_SRC_REPO_PATH} pytorch
  cd pytorch
  git submodule sync
  git submodule update --init --recursive
  rm -rf build

  ${MLC_PYTHON_BIN_WITH_PATH} -m pip install -r requirements.txt
  test $? -eq 0 || exit $?
  ${MLC_PYTHON_BIN_WITH_PATH} setup.py bdist_wheel
  test $? -eq 0 || exit $?
else
  cd pytorch
fi

cd dist
${MLC_PYTHON_BIN_WITH_PATH} -m pip install torch-2.*linux_x86_64.whl
test $? -eq 0 || exit $?
