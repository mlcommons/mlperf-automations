#!/bin/bash

CUR_DIR=$PWD
SCRIPT_DIR=${MLC_TMP_CURRENT_SCRIPT_PATH}

echo "******************************************************"
echo "Cloning MLCommons from ${MLC_GIT_URL} with branch ${MLC_GIT_CHECKOUT} ${MLC_GIT_DEPTH} ${MLC_GIT_RECURSE_SUBMODULES} ..."

if [ ! -d "src" ]; then
  if [ -z ${MLC_GIT_SHA} ]; then
    git clone ${MLC_GIT_RECURSE_SUBMODULES} -b "${MLC_GIT_CHECKOUT}" ${MLC_GIT_URL} ${MLC_GIT_DEPTH} src
    cd src
  else
    git clone ${MLC_GIT_RECURSE_SUBMODULES} ${MLC_GIT_URL} ${MLC_GIT_DEPTH} src
    cd src
    git checkout -b "${MLC_GIT_CHECKOUT}"
  fi
  if [ "${?}" != "0" ]; then exit 1; fi
else
    cd src
fi

IFS=',' read -r -a submodules <<< "${MLC_GIT_SUBMODULES}"

for submodule in "${submodules[@]}"
do
    echo "Initializing submodule ${submodule}"
    git submodule update --init "${submodule}"
    if [ "${?}" != "0" ]; then exit 1; fi
done

if [ ${MLC_GIT_PATCH} == "yes" ]; then
  patch_filename=${MLC_GIT_PATCH_FILENAME:-git.patch}
  echo "Applying patch ${SCRIPT_DIR}/patch/$patch_filename"
  git apply ${SCRIPT_DIR}/patch/"$patch_filename"
  if [ "${?}" != "0" ]; then exit 1; fi
fi

cd "$CUR_DIR"
