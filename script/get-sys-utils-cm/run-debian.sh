#!/bin/bash

echo "************************************************"
echo "Installing some system dependencies via sudo apt"


if [[ "$MLC_QUIET" != "yes" ]]; then 
 echo "Enter skip to skip this step or press enter to continue:"
 read DUMMY

 if [[ "$DUMMY" == "skip" ]]; then exit 0; fi
fi

MLC_APT_TOOL=${MLC_APT_TOOL:-apt-get}

${MLC_SUDO} ${MLC_APT_TOOL} update && \
    ${MLC_SUDO} ${MLC_APT_TOOL} install -y --no-install-recommends \
           apt-utils \
           git \
           wget \
           curl \
           zip \
           unzip \
           bzip2 \
           zlib1g-dev \
           libbz2-dev \
           openssh-client \
           kmod \
           libmesa-dev \
           libssl-dev \
           vim \
           mc \
           tree \
           gcc \
           g++ \
           tar \
           autoconf \
           autogen \
           libtool \
           make \
           cmake \
           libc6-dev \
           build-essential \
           libbz2-dev \
           libffi-dev \
           liblzma-dev \
           python3 \
           python3-pip \
           python3-dev \
           libtinfo-dev \
           sudo \
           libgl1 \
           libncurses5

# Install Python deps though preference is to install them 
# via mlcr "get generic-python-lib _package.{Python PIP package name}"
if [[ "${MLC_SKIP_PYTHON_DEPS}" != "yes" ]]; then
 . ${MLC_TMP_CURRENT_SCRIPT_PATH}/do_pip_installs.sh
 test $? -eq 0 || exit $?
fi
