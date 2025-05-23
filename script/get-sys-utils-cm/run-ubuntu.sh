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
    ${MLC_SUDO} DEBIAN_FRONTEND=noninteractive ${MLC_APT_TOOL} install -y --no-install-recommends --ignore-missing \
           apt-utils \
           git \
           wget \
           curl \
           zip \
           unzip \
           bzip2 \
           libz-dev \
           libbz2-dev \
           openssh-client \
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
           python3-venv \
           libtinfo-dev \
           python-is-python3 \
           sudo \
           libgl1 \
           libjpeg9-dev \
           unzip \
           zlib1g-dev

# Install Python deps though preference is to install them 
# via mlcr "get generic-python-lib _package.{Python PIP package name}"
if [[ "${MLC_SKIP_PYTHON_DEPS}" != "yes" ]]; then
 . ${MLC_TMP_CURRENT_SCRIPT_PATH}/do_pip_installs.sh
 test $? -eq 0 || exit $?
fi
