#!/bin/bash
if [[ -z ${MLC_GIT_REPO_CHECKOUT_PATH} ]]; then
    echo "Git repository not found!"
    exit 1
fi
cd ${MLC_GIT_REPO_CHECKOUT_PATH}
scons -j${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES} --aocl_utils_install_path=${MLC_AOCL_UTILS_INSTALL_PATH}
test $? -eq 0 || exit $?
