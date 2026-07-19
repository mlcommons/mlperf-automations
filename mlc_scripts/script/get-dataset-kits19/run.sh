#!/bin/bash

CUR_DIR=$PWD
SCRIPT_DIR=${MLC_TMP_CURRENT_SCRIPT_PATH}

echo "******************************************************"
echo "Cloning kits19 from ${MLC_GIT_URL} with branch ${MLC_GIT_CHECKOUT} ${MLC_GIT_DEPTH} ${MLC_GIT_RECURSE_SUBMODULES}..."

if [ ! -d "kits19" ]; then
  if [ -z ${MLC_GIT_SHA} ]; then
    cmd="git clone ${MLC_GIT_RECURSE_SUBMODULES} -b ${MLC_GIT_CHECKOUT} ${MLC_GIT_URL} ${MLC_GIT_DEPTH} kits19"
    echo $cmd
    eval $cmd
    cd kits19
  else
    git clone ${MLC_GIT_RECURSE_SUBMODULES} ${MLC_GIT_URL} ${MLC_GIT_DEPTH} kits19
    cd kits19
    git checkout -b "${MLC_GIT_CHECKOUT}"
  fi
  if [ "${?}" != "0" ]; then exit 1; fi
else
  cd kits19
fi

if [ ${MLC_GIT_PATCH} == "yes" ]; then
  patch_filename=${MLC_GIT_PATCH_FILENAME}
  if [ ! -n ${MLC_GIT_PATCH_FILENAMES} ]; then
    patchfile=${MLC_GIT_PATCH_FILENAME:-"git.patch"}
    MLC_GIT_PATCH_FILENAMES=$patchfile
  fi
  IFS=', ' read -r -a patch_files <<< ${MLC_GIT_PATCH_FILENAMES}
  for patch_filename in "${patch_files[@]}"
  do
    echo "Applying patch ${SCRIPT_DIR}/patch/$patch_filename"
    git apply ${SCRIPT_DIR}/patch/"$patch_filename"
    if [ "${?}" != "0" ]; then exit 1; fi
  done
fi
cd ${CUR_DIR}/kits19
${MLC_PYTHON_BIN_WITH_PATH} -m starter_code.get_imaging
cd data
cp -rf case_00185 case_00400
cd "$CUR_DIR"
