#!/bin/bash

if [[ $(apt list --installed | grep cuda-nvrtc-dev) ]]; then
    apt-get remove --purge -y --allow-change-held-packages cuda-nvrtc-dev*
fi

curl -fsSLO https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/${MLC_HOST_PLATFORM_FLAVOR}/cuda-keyring_1.1-1_all.deb
test $? -eq 0 || exit 1

dpkg -i cuda-keyring_1.1-1_all.deb
test $? -eq 0 || exit 1

rm cuda-keyring_1.1-1_all.deb

apt-get update
apt-get install -y --no-install-recommends cuda-nvrtc-dev-$MLC_NVRTC_CUDA_VERSION=$MLC_NVRTC_VERSION
test $? -eq 0 || exit 1