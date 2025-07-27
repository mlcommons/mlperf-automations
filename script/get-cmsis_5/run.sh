#!/bin/bash

CUR_DIR=$PWD
SCRIPT_DIR=${MLC_TMP_CURRENT_SCRIPT_PATH}

echo "******************************************************"

if [ ! -d "cmsis" ]; then
  if [ -z ${MLC_GIT_SHA} ]; then
    echo "Cloning MLCSIS_5 from ${MLC_GIT_URL} with branch ${MLC_GIT_CHECKOUT} ${MLC_GIT_DEPTH} ${MLC_GIT_RECURSE_SUBMODULES}..."
    git clone ${MLC_GIT_RECURSE_SUBMODULES} -b "${MLC_GIT_CHECKOUT}" ${MLC_GIT_URL} ${MLC_GIT_DEPTH} cmsis
    if [ "${?}" != "0" ]; then exit 1; fi
  else
    echo "Cloning MLCSIS_5 from ${MLC_GIT_URL} with default branch and checkout ${MLC_GIT_CHECKOUT} ${MLC_GIT_DEPTH} ${MLC_GIT_RECURSE_SUBMODULES}..."
    git clone ${MLC_GIT_RECURSE_SUBMODULES} ${MLC_GIT_URL} ${MLC_GIT_DEPTH} cmsis
    if [ "${?}" != "0" ]; then exit 1; fi
    cd cmsis
    git checkout "${MLC_GIT_CHECKOUT}"
    if [ "${?}" != "0" ]; then exit 1; fi
  fi
fi
