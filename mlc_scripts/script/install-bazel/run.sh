#!/bin/bash

CUR_DIR=$PWD

echo "******************************************************"

MLC_WGET_URL=${MLC_WGET_URL//"[OS]"/${MLC_HOST_OS_TYPE}}
MLC_WGET_URL=${MLC_WGET_URL//"[PLATFORM]"/${MLC_HOST_PLATFORM_FLAVOR}}
MLC_WGET_URL=${MLC_WGET_URL//"[VERSION]"/${MLC_VERSION}}

echo "MLC_WGET_URL=${MLC_WGET_URL}" >> tmp-run-env.out

BAZEL_SCRIPT="bazel-${MLC_VERSION}-installer-${MLC_HOST_OS_TYPE}-${MLC_HOST_PLATFORM_FLAVOR}.sh"

INSTALL_DIR=${CUR_DIR}

rm -rf ${INSTALL_DIR}/bin

wget -c ${MLC_WGET_URL} --no-check-certificate

if [ "${?}" != "0" ]; then exit 1; fi

chmod +x ${BAZEL_SCRIPT}

./${BAZEL_SCRIPT} --bin=${INSTALL_DIR}"/bin" --base=${INSTALL_DIR}"/install"
if [ "${?}" != "0" ]; then exit 1; fi

echo "Bazel is installed to ${INSTALL_DIR} ..."
