#!/bin/bash

echo ""

if [[ ${MLC_GENERIC_PYTHON_PACKAGE_VARIANT} == "nvidia-apex-depreciated" ]]; then
  cd ${MLC_GIT_REPO_CHECKOUT_PATH}
  cmd="${MLC_PYTHON_BIN_WITH_PATH} -m pip install -v --disable-pip-version-check --global-option=\"--cpp_ext\" --global-option=\"--cuda_ext\" ./"
  echo $cmd
  if [[ -n ${MLC_PIP_ERROR_SKIP} ]]; then
    eval $cmd
  else
    eval $cmd
    test $? -eq 0 || exit $?
  fi
  exit 0
fi

if [[ ${MLC_GENERIC_PYTHON_PACKAGE_NAME}  == "tensorflow_old" ]]; then
    if [[ ${MLC_HOST_OS_FLAVOR} == "macos" ]]; then
        if [[ -n ${MLC_PIP_ERROR_SKIP} ]]; then
            . ${MLC_TMP_CURRENT_SCRIPT_PATH}/tensorflow/run-macos.sh
	else
            . ${MLC_TMP_CURRENT_SCRIPT_PATH}/tensorflow/run-macos.sh
            test $? -eq 0 || exit $?
        fi
        exit 0
    fi
    if [[ ${MLC_HOST_PLATFORM_FLAVOR} == "aarch64" ]]; then
        if [[ -n ${MLC_PIP_ERROR_SKIP} ]]; then
            . ${MLC_TMP_CURRENT_SCRIPT_PATH}/tensorflow/run-aarch64.sh
	else
            . ${MLC_TMP_CURRENT_SCRIPT_PATH}/tensorflow/run-aarch64.sh
            test $? -eq 0 || exit $?
        fi
        exit 0
    fi
fi

if [[ -n ${MLC_GENERIC_PYTHON_PIP_URL} ]]; then
    cmd="${MLC_PYTHON_BIN_WITH_PATH} -m pip install \"${MLC_GENERIC_PYTHON_PIP_URL}\" ${MLC_GENERIC_PYTHON_PIP_EXTRA}"
    echo $cmd
    if [[ -n ${MLC_PIP_ERROR_SKIP} ]]; then
        eval $cmd
    else
        eval $cmd
        test $? -eq 0 || exit $?
    fi
    exit 0
fi

cmd="${MLC_PYTHON_BIN_WITH_PATH} -m pip install \"${MLC_GENERIC_PYTHON_PACKAGE_NAME}${MLC_TMP_PIP_VERSION_STRING}\" ${MLC_GENERIC_PYTHON_PIP_EXTRA}"
echo $cmd

if [[ -n ${MLC_PIP_ERROR_SKIP} ]]; then
    eval $cmd
else
    eval $cmd
    test $? -eq 0 || exit $?
fi
exit 0
