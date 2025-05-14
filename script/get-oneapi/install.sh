#!/bin/bash
set -e
exit 0
wget -nc ${MLC_ONEAPI_INSTALL_URL_BASE}/${MLC_ONEAPI_INSTALL_FILENAME}
rm -rf install
mkdir install
cmd="bash ./${MLC_ONEAPI_INSTALL_FILENAME} -a --silent --cli --eula accept  --install-dir ${PWD}/install"

echo $cmd
eval $cmd
