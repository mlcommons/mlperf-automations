#!/bin/bash
# Skip build for binary download
if [[ "${MLC_AOCL_BINARY_DOWNLOAD}" == "yes" ]]; then
    echo "Binary download mode - skipping build"
    exit 0
fi

if [[ -z ${MLC_GIT_REPO_CHECKOUT_PATH} ]]; then
    echo "Git repository not found!"
    exit 1
fi
cd ${MLC_GIT_REPO_CHECKOUT_PATH}
scons -j${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES} --aocl_utils_install_path=${MLC_AOCL_UTILS_INSTALL_PATH}
test $? -eq 0 || exit $?

# Copy fast libs from subdirectory and create compatibility symlinks
LIB_DIR="${MLC_GIT_REPO_CHECKOUT_PATH}/build/aocl-release/src"
cd "${LIB_DIR}"
cp -f fast/libalmfast.so . 2>/dev/null || true
cp -f fast/libalmfast.a . 2>/dev/null || true
ln -sf libalm.so libamdlibm.so
ln -sf libalm.a libamdlibm.a
ln -sf libalmfast.so libamdlibmfast.so
ln -sf libalmfast.a libamdlibmfast.a
