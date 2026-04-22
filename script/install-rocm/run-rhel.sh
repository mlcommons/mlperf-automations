#!/bin/bash

# ROCm Runfile Installer for RHEL/CentOS/Rocky
# Supports ROCm 7.x via runfile, falls back to package manager for older versions

major_version="${MLC_VERSION%%.*}"

if [[ ${major_version} -ge 7 ]]; then
  # ROCm 7.x: Use runfile installer (downloaded via download,file script)
  runfile_path="${MLC_DOWNLOAD_DOWNLOADED_PATH}"
  if [[ -z "${runfile_path}" || ! -f "${runfile_path}" ]]; then
    echo "ERROR: ROCm runfile not found at ${runfile_path}"
    exit 1
  fi

  chmod +x "${runfile_path}"

  # Install ROCm via runfile
  install_prefix="${MLC_ROCM_INSTALL_PREFIX:-/}"
  echo "Installing ROCm ${MLC_VERSION} via runfile to target=${install_prefix} ..."
  if [[ "${install_prefix}" == "/" ]]; then
    sudo bash "${runfile_path}" deps=install target="/" rocm postrocm
  else
    bash "${runfile_path}" deps=install target="${install_prefix}" rocm postrocm
  fi
  test $? -eq 0 || exit 1

else
  # ROCm 5.x/6.x: Use package manager method
  mainversion="${MLC_HOST_OS_VERSION%%.*}"

  repo1="[amdgpu]
name=amdgpu
baseurl=https://repo.radeon.com/amdgpu/${MLC_VERSION}/rhel/${MLC_HOST_OS_VERSION}/main/x86_64
enabled=1
gpgcheck=1
gpgkey=https://repo.radeon.com/rocm/rocm.gpg.key
"
  echo "${repo1}" | sudo tee /etc/yum.repos.d/amdgpu.repo

  repo2="[rocm]
name=rocm
baseurl=https://repo.radeon.com/rocm/rhel${mainversion}/latest/main
enabled=1
priority=50
gpgcheck=1
gpgkey=https://repo.radeon.com/rocm/rocm.gpg.key
"
  echo "${repo2}" | sudo tee /etc/yum.repos.d/rocm.repo

  sudo yum clean all

  sudo yum install -y amdgpu-dkms

  sudo yum install -y rocm-hip-libraries
  test $? -eq 0 || exit 1
fi
