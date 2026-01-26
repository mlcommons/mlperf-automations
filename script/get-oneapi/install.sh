#!/bin/bash
#set -e

function run() {
  CMD=$1
  echo "$CMD"
  # Run the install command and capture both output and exit code
  OUTPUT=$(eval "$CMD" 2>&1)
  STATUS=$?

  # Check if it was already installed
  if echo "$OUTPUT" | grep -q "already installed"; then
     echo "OneAPI is already installed. Exiting."
     exit 0
  fi

  if [ $STATUS -ne 0 ]; then
    echo "Installer failed with status $STATUS"
    echo "$OUTPUT"
    exit $STATUS
  fi
}

wget -nc ${MLC_ONEAPI_INSTALL_URL_BASE}/${MLC_ONEAPI_INSTALL_FILENAME}
test $? -eq 0 || exit $?

if [[ ${MLC_CLEAN_INSTALL} == yes ]]; then
  rm -rf $HOME/intel
fi

rm -rf install
mkdir install

CMD="bash ./${MLC_ONEAPI_INSTALL_FILENAME} -a --silent --cli --eula accept  --install-dir ${PWD}/install"
run "$CMD"

if [[ ${MLC_ONEAPI_CXX} == 'yes' ]]; then
  wget -nc ${MLC_ONEAPI_CXX_COMPILER_URL_BASE}/${MLC_ONEAPI_CXX_COMPILER_FILENAME}
  test $? -eq 0 || exit $?
  CMD="bash ./${MLC_ONEAPI_CXX_COMPILER_FILENAME} -a --silent --cli --eula accept --install-dir ${PWD}/install"
  run "$CMD"
fi

if [[ ${MLC_ONEAPI_FORTRAN} == 'yes' ]]; then
  wget -nc ${MLC_ONEAPI_FORTRAN_COMPILER_URL_BASE}/${MLC_ONEAPI_FORTRAN_COMPILER_FILENAME}
  test $? -eq 0 || exit $?
  CMD="bash ./${MLC_ONEAPI_FORTRAN_COMPILER_FILENAME} -a --silent --cli --eula accept --install-dir ${PWD}/install"
  run "$CMD"
fi
