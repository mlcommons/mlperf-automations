#!/bin/bash

# Compile

BIN_NAME=${MLC_BIN_NAME:-run.out}
RUN_DIR="${MLC_RUN_DIR:-.}"
echo "RUN_DIR=$RUN_DIR"

if [[ ${MLC_SKIP_RECOMPILE} == "yes" ]]; then
  if [ -f "${RUN_DIR}/${BIN_NAME}" ]; then
    exit 0
  fi
fi

rm -f "${RUN_DIR}/${BIN_NAME}"

if [ -z "${MLC_SOURCE_FOLDER_PATH}" ]; then
  echo "No source directory (MLC_SOURCE_FOLDER_PATH} specified"
  exit 1
fi

if [[ -z "${MLC_C_SOURCE_FILES}"  && -z "${MLC_CXX_SOURCE_FILES}" && -z "${MLC_F_SOURCE_FILES}" ]]; then
  echo "No source files (MLC_C_SOURCE_FILES or MLC_CXX_SOURCE_FILES or MLC_F_SOURCE_FILES) specified"
  exit 1
fi

echo ""
echo "Checking compiler version ..."
echo ""

"${MLC_C_COMPILER_WITH_PATH}" ${MLC_C_COMPILER_FLAG_VERSION}

echo ""
echo "Compiling source files ..."
echo ""

cd "${MLC_SOURCE_FOLDER_PATH}"
test $? -eq 0 || exit 1

IFS=';' read -ra FILES <<< "${MLC_C_SOURCE_FILES}"
for file in "${FILES[@]}"; do
  base="$(basename -- $file)"
  base_name=${base%.*}
  echo $base
  echo $basename
  MLCD="${MLC_C_COMPILER_WITH_PATH} -c ${MLC_C_COMPILER_FLAGS} ${MLC_C_INCLUDE_PATH} $file ${MLC_C_COMPILER_FLAG_OUTPUT}$base_name.o"
  echo $CMD
  eval $CMD
  test $? -eq 0 || exit 1
done

IFS=';' read -ra FILES <<< "${MLC_CXX_SOURCE_FILES}"
for file in "${FILES[@]}"; do
  base="$(basename -- $file)"
  base_name=${base%.*}
  echo $base
  echo $basename
  MLCD="${MLC_CXX_COMPILER_WITH_PATH} -c ${MLC_CXX_COMPILER_FLAGS} ${MLC_CPLUS_INCLUDE_PATH} $file ${MLC_CXX_COMPILER_FLAG_OUTPUT}$base_name.o"
  echo $CMD
  eval $CMD
  test $? -eq 0 || exit 1
done


echo ""
echo "Linking ..."
echo ""
CMD="${MLC_LINKER_WITH_PATH} ${MLC_LINKER_COMPILE_FLAGS}  *.o -o \"${RUN_DIR}/${BIN_NAME}\" ${MLC_LD_LIBRARY_PATH} ${MLC_LINKER_FLAGS}"
echo $CMD
eval $CMD

test $? -eq 0 || exit 1
