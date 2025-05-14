#!/bin/bash
set -e
wget -nc ${MLC_ONEAPI_INSTALL_URL_BASE}/${MLC_ONEAPI_INSTALL_FILENAME}
rm -rf install
mkdir install
cmd="bash ./${MLC_ONEAPI_INSTALL_FILENAME} -a --silent --cli --eula accept  --install-dir ${PWD}/install"

echo $cmd
eval $cmd

if [[ ${MLC_ONEAPI_FORTRAN} == 'yes' ]] then
  wget -nc https://registrationcenter-download.intel.com/akdlm/IRC_NAS/2238465b-cfc7-4bf8-ad04-e55cb6577cba/intel-fortran-essentials-2025.1.1.8_offline.sh
  cmd="bash ./intel-fortran-essentials-2025.1.1.8_offline.sh -a --silent --cli --eula accept --install-dir ${PWD}/install"
  echo $cmd
  eval $cmd
fi
