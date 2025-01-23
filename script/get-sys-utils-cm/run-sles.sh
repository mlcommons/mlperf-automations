#!/bin/bash

echo "***************************************************"
echo "Installing some system dependencies via sudo zypper"


if [[ "$MLC_QUIET" != "yes" ]]; then 
 echo "Enter skip to skip this step or press enter to continue:"
 read DUMMY

 if [[ "$DUMMY" == "skip" ]]; then exit 0; fi
fi

MLC_PACKAGE_TOOL=${MLC_PACKAGE_TOOL:-zypper}

${MLC_SUDO} ${MLC_PACKAGE_TOOL} install -t pattern devel_basis
${MLC_SUDO} ${MLC_PACKAGE_TOOL} update && \
    ${MLC_SUDO} ${MLC_PACKAGE_TOOL}  install -y \
           bzip2-devel bzip2 \
           ca-certificates curl  cmake \
           gcc git \
           libtool libffi-devel \
           zlib-devel \
           libbz2-devel \
           openssh-client \
           make \
           patch python3 python3-pip python3-devel \
           openssl-devel \
           rsync \
           tar \
           unzip \
           vim \
           wget which \
           xz \
           zip 

# Install Python deps though preference is to install them 
# via mlcr "get generic-python-lib _package.{Python PIP package name}"
if [[ "${MLC_SKIP_PYTHON_DEPS}" != "yes" ]]; then
 . ${MLC_TMP_CURRENT_SCRIPT_PATH}/do_pip_installs.sh
 test $? -eq 0 || exit $?
fi
