#!/bin/bash

# Skip when user-provided library path is supplied (path.# variation)
if [[ "${MLC_AOCL_LIB_PATH_PROVIDED}" == "yes" ]]; then
    echo "User-provided library path mode - skipping build"
    exit 0
fi
# Skip build for binary download
if [[ "${MLC_AOCL_BINARY_DOWNLOAD}" == "yes" ]]; then
    echo "Binary download mode - skipping build"
    exit 0
fi


# Determine install prefix
AOCL_VERSION="${MLC_AOCL_LIBM_VERSION:-${MLC_GIT_CHECKOUT:-unknown}}"
if [[ -n "${MLC_OUTDIRNAME}" ]]; then
    INSTALL_PREFIX="${MLC_OUTDIRNAME}/aocl-libm/${AOCL_VERSION}"
else
    INSTALL_PREFIX="${MLC_AOCL_LIBM_SRC_PATH}/install"
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

# If MLC_OUTDIRNAME is set, copy built libraries and headers there
if [[ -n "${MLC_OUTDIRNAME}" ]]; then
    mkdir -p "${INSTALL_PREFIX}/lib" "${INSTALL_PREFIX}/include"
    cp -f "${LIB_DIR}"/*.so "${INSTALL_PREFIX}/lib/" 2>/dev/null || true
    cp -f "${LIB_DIR}"/*.a "${INSTALL_PREFIX}/lib/" 2>/dev/null || true
    # Copy symlinks too
    cp -af "${LIB_DIR}"/libamdlibm* "${INSTALL_PREFIX}/lib/" 2>/dev/null || true
    # Copy headers if available
    if [[ -d "${MLC_GIT_REPO_CHECKOUT_PATH}/include" ]]; then
        cp -rf "${MLC_GIT_REPO_CHECKOUT_PATH}/include/"* "${INSTALL_PREFIX}/include/" 2>/dev/null || true
    fi
    echo "Installed aocl-libm to ${INSTALL_PREFIX}"
fi
