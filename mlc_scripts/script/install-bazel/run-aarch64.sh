#!/bin/bash

CUR_DIR=$PWD
echo "******************************************************"

MLC_WGET_URL=${MLC_WGET_URL//"[OS]"/${MLC_HOST_OS_TYPE}}
MLC_WGET_URL=${MLC_WGET_URL//"[PLATFORM]"/arm64}
MLC_WGET_URL=${MLC_WGET_URL//"[VERSION]"/${MLC_VERSION}}
MLC_WGET_URL=${MLC_WGET_URL//"-installer-"/-}
MLC_WGET_URL=${MLC_WGET_URL//".sh"/}
echo "MLC_WGET_URL=${MLC_WGET_URL}" > tmp-run-env.out
BAZEL_SCRIPT="bazel-${MLC_VERSION}-${MLC_HOST_OS_TYPE}-arm64"

INSTALL_DIR=${CUR_DIR}
rm -rf ${INSTALL_DIR}/bin
wget -c ${MLC_WGET_URL}
if [ "${?}" != "0" ]; then exit 1; fi
chmod +x ${BAZEL_SCRIPT}
ln -s ${BAZEL_SCRIPT} bazel
if [ "${?}" != "0" ]; then exit 1; fi

echo "MLC_BAZEL_INSTALLED_PATH=${INSTALL_DIR}" >>tmp-run-env.out
echo "MLC_BAZEL_BIN_WITH_PATH=${INSTALL_DIR}/${BAZEL_SCRIPT}" >>tmp-run-env.out

echo "Bazel is installed to ${INSTALL_DIR} ..."
