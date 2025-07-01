#!/bin/bash
#set -e

function run() {
  CMD=$1
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
rm -rf install
mkdir install
CMD="bash ./${MLC_ONEAPI_INSTALL_FILENAME} -a --silent --cli --eula accept  --install-dir ${PWD}/install"
run "$CMD"

if [[ ${MLC_ONEAPI_FORTRAN} == 'yes' ]] then
  wget -nc https://registrationcenter-download.intel.com/akdlm/IRC_NAS/2238465b-cfc7-4bf8-ad04-e55cb6577cba/intel-fortran-essentials-2025.1.1.8_offline.sh
  test $? -eq 0 || exit $?
  CMD="bash ./intel-fortran-essentials-2025.1.1.8_offline.sh -a --silent --cli --eula accept --install-dir ${PWD}/install"
  run "$CMD"
fi
