#!/bin/bash

CUR_DIR=$PWD

INSTALL_DIR="${MLC_LLVM_INSTALLED_PATH}"
echo "INSTALL_DIR=${INSTALL_DIR}"

if [[ ${MLC_LLVM_CONDA_ENV} != "yes" ]]; then
    cmd="rm -rf ${INSTALL_DIR}"
    echo "$cmd"
    eval "$cmd"
else
    export PATH=${MLC_CONDA_BIN_PATH}:$PATH
fi

if [[ ${MLC_CLEAN_BUILD} == "yes" ]]; then
    cmd="rm -rf build"
    echo "$cmd"
    eval "$cmd"
fi

mkdir -p build

# If install exist, then configure was done 
if [ ! -d "${INSTALL_DIR}" ] || [ ${MLC_LLVM_CONDA_ENV} == "yes" ]; then
    echo "******************************************************"

    cd build
    test $? -eq 0 || exit $?

    echo "${MLC_LLVM_CMAKE_CMD}"
    eval "${MLC_LLVM_CMAKE_CMD}"
    
    # Auto-calculate parallel jobs: use MLC_LLVM_BUILD_JOBS if set,
    # otherwise min(nproc, available_memory_GB / 4) to prevent OOM
    if [ -n "${MLC_LLVM_BUILD_JOBS}" ]; then
        NINJA_JOBS="${MLC_LLVM_BUILD_JOBS}"
    else
        CPUS=$(nproc)
        MEM_AVAIL_GB=$(awk '/MemAvailable/{printf "%d", $2/1048576}' /proc/meminfo 2>/dev/null || echo 0)
        if [ "${MEM_AVAIL_GB}" -gt 0 ] 2>/dev/null; then
            MEM_JOBS=$((MEM_AVAIL_GB / 4))
            [ "${MEM_JOBS}" -lt 1 ] && MEM_JOBS=1
            NINJA_JOBS=$((MEM_JOBS < CPUS ? MEM_JOBS : CPUS))
        else
            NINJA_JOBS=${CPUS}
        fi
    fi
    echo "[install-llvm-src] Using ninja -j${NINJA_JOBS} (cpus=$(nproc), mem=${MEM_AVAIL_GB:-?}GB)"
    cmd="ninja -j${NINJA_JOBS} ${MLC_LLVM_CHECK_ALL}"
    echo $cmd
    eval $cmd
    test $? -eq 0 || exit $?
    
    cmd="ninja -j${NINJA_JOBS} install"
    echo $cmd
    eval $cmd
    test $? -eq 0 || exit $?

fi

# Clean build directory (too large)
cd ${CUR_DIR}
rm -rf build

echo "******************************************************"
echo "LLVM is built and installed to ${INSTALL_DIR} ..."
