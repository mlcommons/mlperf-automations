MLC_SUDO=${MLC_SUDO:-sudo}
${MLC_SUDO} apt install -y --allow-downgrades libnccl2=2.18.3-1+cuda${MLC_CUDA_VERSION} libnccl-dev=2.18.3-1+cuda${MLC_CUDA_VERSION}
