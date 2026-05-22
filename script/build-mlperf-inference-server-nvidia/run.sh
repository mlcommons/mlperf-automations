#!/bin/bash
CUR=$PWD

cd ${MLC_MLPERF_INFERENCE_NVIDIA_CODE_PATH}

if [[ ${BUILD_TRTLLM} == "1" ]]; then
  git lfs install
fi

if [[ ${MLC_MAKE_CLEAN} == "yes" ]]; then
  make clean
fi

if [[ ${MLC_MLPERF_DEVICE} == "inferentia" ]]; then
 echo "inferencia"
 make prebuild
fi


if [[ "${MLC_MLPERF_INFERENCE_VERSION}" =~ ^[5-9]\.[0-9]+(-dev)?$ ]]; then
  echo "Replacing /work/ with ${MLC_MLPERF_INFERENCE_NVIDIA_CODE_PATH} in all files..."
  find . -type f -exec sed -i "s|/work/|${MLC_MLPERF_INFERENCE_NVIDIA_CODE_PATH}/|g" {} +
fi

echo ${MLC_MAKE_BUILD_COMMAND}

# Set CMAKE_PREFIX_PATH for pybind11 discovery from pip-installed package
PYBIND11_CMAKE_DIR=$(${MLC_PYTHON_BIN_WITH_PATH} -c "import pybind11; print(pybind11.get_cmake_dir())" 2>/dev/null)
if [[ -n "${PYBIND11_CMAKE_DIR}" ]]; then
  export CMAKE_PREFIX_PATH="$(dirname $(dirname ${PYBIND11_CMAKE_DIR})):${CMAKE_PREFIX_PATH}"
fi

# Set FFI_UTILS_DIR if not already set (defaults to /opt/ffi_utils in Docker)
if [[ -z "${FFI_UTILS_DIR}" ]]; then
  export FFI_UTILS_DIR="${MLC_MLPERF_INFERENCE_NVIDIA_CODE_PATH}/build/ffi_utils"
  mkdir -p "${FFI_UTILS_DIR}"
fi

# Set LOADGEN paths from MLC cache if available
if [[ -n "${MLC_MLPERF_INFERENCE_LOADGEN_INSTALL_PATH}" ]]; then
  export LOADGEN_INCLUDE_DIR="${MLC_MLPERF_INFERENCE_LOADGEN_INSTALL_PATH}/include"
  export LOADGEN_LIB_DIR="${MLC_MLPERF_INFERENCE_LOADGEN_INSTALL_PATH}/lib"
elif [[ -z "${LOADGEN_INCLUDE_DIR}" ]]; then
  # Try to find loadgen in MLC cache
  LOADGEN_LIB_FILE=$(find ${HOME}/MLC/repos/local/cache -name "libmlperf_loadgen.a" 2>/dev/null | head -1)
  if [[ -n "${LOADGEN_LIB_FILE}" ]]; then
    export LOADGEN_LIB_DIR="$(dirname ${LOADGEN_LIB_FILE})"
    # Headers may be in parent/include or directly in parent (source layout)
    _LOADGEN_PARENT="$(dirname ${LOADGEN_LIB_DIR})"
    if [[ -f "${_LOADGEN_PARENT}/include/loadgen.h" ]]; then
      export LOADGEN_INCLUDE_DIR="${_LOADGEN_PARENT}/include"
    else
      export LOADGEN_INCLUDE_DIR="${_LOADGEN_PARENT}"
    fi
  elif [[ -n "${MLC_MLPERF_INFERENCE_SOURCE}" && -f "${MLC_MLPERF_INFERENCE_SOURCE}/loadgen/loadgen.h" ]]; then
    # Build loadgen from inference source if not already built
    echo "Building loadgen from ${MLC_MLPERF_INFERENCE_SOURCE}/loadgen ..."
    _LOADGEN_SRC="${MLC_MLPERF_INFERENCE_SOURCE}/loadgen"
    _LOADGEN_BUILD="${_LOADGEN_SRC}/build"
    mkdir -p "${_LOADGEN_BUILD}"
    pushd "${_LOADGEN_BUILD}" > /dev/null
    cmake -DCMAKE_BUILD_TYPE=Release "${_LOADGEN_SRC}" && make -j mlperf_loadgen
    popd > /dev/null
    if [[ -f "${_LOADGEN_BUILD}/libmlperf_loadgen.a" ]]; then
      export LOADGEN_LIB_DIR="${_LOADGEN_BUILD}"
      export LOADGEN_INCLUDE_DIR="${_LOADGEN_SRC}"
      echo "Loadgen built successfully."
    fi
  fi
fi
echo "LOADGEN_INCLUDE_DIR=${LOADGEN_INCLUDE_DIR}"
echo "LOADGEN_LIB_DIR=${LOADGEN_LIB_DIR}"

# Rebuild loadgen with -fPIC if needed (FFIUtils links it into a shared library)
if [[ -n "${LOADGEN_LIB_DIR}" && -n "${LOADGEN_INCLUDE_DIR}" ]]; then
  _LOADGEN_SRC_DIR="${LOADGEN_INCLUDE_DIR}"
  if [[ -f "${_LOADGEN_SRC_DIR}/loadgen.h" && -f "${_LOADGEN_SRC_DIR}/CMakeLists.txt" ]]; then
    echo "Rebuilding loadgen with -fPIC for shared library linking..."
    pushd "${LOADGEN_LIB_DIR}" > /dev/null
    cmake -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DCMAKE_BUILD_TYPE=Release "${_LOADGEN_SRC_DIR}" && make -j mlperf_loadgen
    popd > /dev/null
  fi
fi

# Set CUDA architectures for cmake if GPU is detected
if [[ -n "${MLC_CUDA_DEVICE_PROP_GPU_COMPUTE_CAPABILITY}" ]]; then
  export CUDA_ARCHITECTURES="${MLC_CUDA_DEVICE_PROP_GPU_COMPUTE_CAPABILITY}"
elif [[ -z "${CUDA_ARCHITECTURES}" ]]; then
  export CUDA_ARCHITECTURES="89"
fi

# Set PYTHONPATH to include NVIDIA code root for setup.py imports
export PYTHONPATH="${MLC_MLPERF_INFERENCE_NVIDIA_CODE_PATH}:${PYTHONPATH}"

# Ensure CUDA include path is visible to the compiler (needed for CMake 3.27+ where FindCUDA is removed)
if [[ -n "${MLC_CUDA_PATH_INCLUDE}" ]]; then
  export CPATH="${MLC_CUDA_PATH_INCLUDE}:${CPATH}"
elif [[ -d "/usr/local/cuda/include" ]]; then
  export CPATH="/usr/local/cuda/include:${CPATH}"
fi

# For v6.0+, build only necessary harness targets to avoid nvmitten dependency in py_harness_default
if [[ "${MLC_MLPERF_INFERENCE_VERSION}" =~ ^[6-9]\.[0-9]+(-dev)?$ ]]; then
  # Build and install loadgen Python binding (mlperf_loadgen)
  if ! ${MLC_PYTHON_BIN_WITH_PATH} -c "import mlperf_loadgen" 2>/dev/null; then
    echo "Installing mlperf_loadgen Python binding..."
    _LOADGEN_SRC="${LOADGEN_INCLUDE_DIR}"
    if [[ -f "${_LOADGEN_SRC}/setup.py" ]]; then
      pushd "${_LOADGEN_SRC}" > /dev/null
      PIP_EXTRA=$(${MLC_PYTHON_BIN_WITH_PATH} -c "import importlib.metadata; print(' --break-system-packages ' if int(importlib.metadata.version('pip').split('.')[0]) >= 23 else '')")
      ${MLC_PYTHON_BIN_WITH_PATH} -m pip install . ${PIP_EXTRA}
      popd > /dev/null
    fi
  fi

  SKIP_DRIVER_CHECK=1 make link_dirs

  # Copy BERT harness source if not already present
  BERT_HARNESS_DIR="${MLC_MLPERF_INFERENCE_NVIDIA_CODE_PATH}/code/harness/harness_bert"
  if [[ ! -d "${BERT_HARNESS_DIR}" ]]; then
    # Look for bert harness source in the repo (e.g. from Lenovo submission)
    BERT_SRC=$(find "${MLC_MLPERF_INFERENCE_NVIDIA_CODE_PATH}/../" -path "*/harness/harness_bert/main_bert.cc" -exec dirname {} \; 2>/dev/null | head -1)
    if [[ -n "${BERT_SRC}" && -d "${BERT_SRC}" ]]; then
      echo "Copying BERT harness source from ${BERT_SRC}..."
      cp -r "${BERT_SRC}" "${BERT_HARNESS_DIR}"
    fi
  fi

  # Append harness_bert target to CMakeLists.txt if source exists and target not yet added
  HARNESS_CMAKE="${MLC_MLPERF_INFERENCE_NVIDIA_CODE_PATH}/code/harness/CMakeLists.txt"
  if [[ -d "${BERT_HARNESS_DIR}" ]] && ! grep -q "harness_bert" "${HARNESS_CMAKE}"; then
    cat >> "${HARNESS_CMAKE}" << 'EOF'

######### BERT HARNESS ########
execute_process(COMMAND echo "Building BERT harness...")
add_executable(harness_bert
    harness_bert/main_bert.cc
    harness_bert/bert_server.cc
    harness_bert/bert_core_vs.cc
    common/logger.cpp
)

target_link_libraries(harness_bert
    nvinfer
    nvinfer_plugin
    gflags
    glog
    ${CUDA_LIBRARIES}
    lwis
    ${LOADGEN_LIB}
    numa
)

target_include_directories(harness_bert
    PUBLIC
        ${CUDA_INCLUDE_DIRS}
        ${LOADGEN_INCLUDE_DIR}
        ${LWIS_INCLUDE_DIR}
        common
        harness_bert
)
EOF
  fi

  # Build TensorRT plugins (NMSOptPlugin, retinanetConcatPlugin, DLRMv2EmbeddingLookupPlugin)
  # These are needed by retinanet and dlrm-v2 during preprocessing and engine building.
  PLUGIN_DIR="${MLC_MLPERF_INFERENCE_NVIDIA_CODE_PATH}/code/plugin"
  if [[ -d "${PLUGIN_DIR}" ]]; then
    # Patch NMSOptPlugin for CUDA 13+ (cub::Sum removed in CCCL 3.0)
    _NMS_GATHER="${PLUGIN_DIR}/NMSOptPlugin/src/gatherTopDetectionsOpt.cu"
    if [[ -f "${_NMS_GATHER}" ]] && grep -q 'cub::Sum()' "${_NMS_GATHER}"; then
      echo "Patching NMSOptPlugin for CUDA 13+ compatibility..."
      sed -i 's/cub::Sum()/::cuda::std::plus<>{}/' "${_NMS_GATHER}"
      grep -q 'cuda/std/functional' "${_NMS_GATHER}" || sed -i '1i #include <cuda/std/functional>' "${_NMS_GATHER}"
    fi
    for _plugin_src in "${PLUGIN_DIR}"/*/CMakeLists.txt; do
      _plugin_name="$(basename "$(dirname "${_plugin_src}")")"
      _plugin_build="${MLC_MLPERF_INFERENCE_NVIDIA_CODE_PATH}/build/plugins/${_plugin_name}"
      mkdir -p "${_plugin_build}"
      echo "Building plugin ${_plugin_name}..."
      pushd "${_plugin_build}" > /dev/null
      CUDA_INC_DIR=/usr/local/cuda/include CPLUS_INCLUDE_PATH=/usr/local/cuda/include cmake -DCMAKE_BUILD_TYPE=Release "$(dirname "${_plugin_src}")" && CPLUS_INCLUDE_PATH=/usr/local/cuda/include make -j
      popd > /dev/null
    done
    echo "Finished building plugins."
  fi

  mkdir -p ${MLC_MLPERF_INFERENCE_NVIDIA_CODE_PATH}/build/harness
  cd ${MLC_MLPERF_INFERENCE_NVIDIA_CODE_PATH}/build/harness
  cmake -DPYTHON3_CMD=${MLC_PYTHON_BIN_WITH_PATH} \
    -DCMAKE_BUILD_TYPE=Release \
    -DLOADGEN_INCLUDE_DIR=${LOADGEN_INCLUDE_DIR} \
    -DLOADGEN_LIB_DIR=${LOADGEN_LIB_DIR} \
    -DFFI_UTILS_DIR=${FFI_UTILS_DIR} \
    -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
    ${MLC_MLPERF_INFERENCE_NVIDIA_CODE_PATH}/code/harness
  test $? -eq 0 || exit $?

  BUILD_TARGETS="harness_default harness_dlrm_v2 FFIUtils lwis"
  if [[ -d "${BERT_HARNESS_DIR}" ]]; then
    BUILD_TARGETS="${BUILD_TARGETS} harness_bert"
  fi
  make -j ${BUILD_TARGETS}
  test $? -eq 0 || exit $?
  echo "Finished building harness."
else
  SKIP_DRIVER_CHECK=1 make ${MLC_MAKE_BUILD_COMMAND}
fi

test $? -eq 0 || exit $?
