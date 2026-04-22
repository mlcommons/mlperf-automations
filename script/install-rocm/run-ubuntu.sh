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
  # ROCm 7.x: Use runfile installer
  runfile_base_url="https://repo.radeon.com/rocm/installer/rocm-runfile-installer/rocm-rel-${MLC_VERSION}/ubuntu/${ubuntu_ver}/"

  # Get the runfile name from the directory listing
  runfile_name=$(wget -q -O - "${runfile_base_url}" | grep -oP 'rocm-installer[^"]+\.run' | head -1)
  if [[ -z "${runfile_name}" ]]; then
    echo "ERROR: Could not find ROCm runfile installer at ${runfile_base_url}"
    exit 1
  fi

  echo "Downloading ROCm ${MLC_VERSION} runfile installer: ${runfile_name}"
  wget -q "${runfile_base_url}${runfile_name}" -O /tmp/${runfile_name}
  test $? -eq 0 || exit 1
  chmod +x /tmp/${runfile_name}

  # Install ROCm via runfile
  install_prefix="${MLC_ROCM_INSTALL_PREFIX:-/}"
  echo "Installing ROCm ${MLC_VERSION} via runfile to target=${install_prefix} ..."
  if [[ "${install_prefix}" == "/" ]]; then
    sudo bash /tmp/${runfile_name} deps=install target="/" rocm postrocm
  else
    bash /tmp/${runfile_name} deps=install target="${install_prefix}" rocm postrocm
  fi
  test $? -eq 0 || exit 1

  rm -f /tmp/${runfile_name}

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

  sudo apt install -y rocm-hip-libraries
  test $? -eq 0 || exit 1
fi
