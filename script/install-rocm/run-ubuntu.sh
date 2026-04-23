#!/bin/bash

# ROCm Runfile Installer for Ubuntu
# Supports ROCm 7.x via runfile, falls back to package manager for older versions

ubuntuflavor="jammy"
ubuntu_ver="${MLC_HOST_OS_VERSION}"
if [[ ${ubuntu_ver} == "24.04" ]]; then
  ubuntuflavor="noble"
elif [[ ${ubuntu_ver} == "22.04" ]]; then
  ubuntuflavor="jammy"
elif [[ ${ubuntu_ver} == "20.04" ]]; then
  ubuntuflavor="focal"
fi

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

  # Determine install args based on compiler-only flag
  if [[ "${MLC_ROCM_COMPILER_ONLY}" == "yes" ]]; then
    rocm_install_args="rocm packages=rocm-llvm,rocm-llvm-dev,rocm-core,rocm-device-libs,rocminfo,comgr,openmp-extras-dev,openmp-extras-runtime,rocm-cmake"
  else
    rocm_install_args="rocm"
  fi

  echo "Installing ROCm ${MLC_VERSION} via runfile to target=${install_prefix} (args: ${rocm_install_args}) ..."
  if [[ "${install_prefix}" == "/" ]]; then
    sudo bash "${runfile_path}" deps=install target="/" ${rocm_install_args} postrocm
  else
    bash "${runfile_path}" deps=install target="${install_prefix}" ${rocm_install_args} postrocm
  fi
  test $? -eq 0 || exit 1

else
  # ROCm 5.x/6.x: Use package manager method
  sudo mkdir --parents --mode=0755 /etc/apt/keyrings
  wget https://repo.radeon.com/rocm/rocm.gpg.key -O - | \
      gpg --dearmor | sudo tee /etc/apt/keyrings/rocm.gpg > /dev/null

  deb1="deb [arch=amd64 signed-by=/etc/apt/keyrings/rocm.gpg] https://repo.radeon.com/amdgpu/${MLC_VERSION}/ubuntu ${ubuntuflavor} main"
  echo $deb1 | sudo tee /etc/apt/sources.list.d/amdgpu.list

  deb2="deb [arch=amd64 signed-by=/etc/apt/keyrings/rocm.gpg] https://repo.radeon.com/rocm/apt/debian ${ubuntuflavor} main"
  echo $deb2 | sudo tee /etc/apt/sources.list.d/rocm.list

  echo -e 'Package: *\nPin: release o=repo.radeon.com\nPin-Priority: 600' | sudo tee /etc/apt/preferences.d/rocm-pin-600

  sudo apt update

  if dpkg -l | grep -q "linux-headers-$(uname -r)" 2>/dev/null; then
    sudo apt install -y amdgpu-dkms
  fi

  if [[ "${MLC_ROCM_COMPILER_ONLY}" == "yes" ]]; then
    sudo apt install -y rocm-llvm rocm-device-libs rocminfo
  else
    sudo apt install -y rocm-hip-libraries
  fi
  test $? -eq 0 || exit 1
fi
