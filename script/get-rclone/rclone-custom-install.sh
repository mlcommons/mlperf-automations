# This script is based on Rclone's original install script:
# https://github.com/rclone/rclone/blob/master/docs/content/install.sh
#
# Rclone is licensed under the MIT License:
# https://github.com/rclone/rclone/blob/master/COPYING
#
# Copyright (C) 2019 by Nick Craig-Wood https://www.craig-wood.com/nick/

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

#!/usr/bin/env bash

# error codes
# 0 - exited without problems
# 1 - parameters not supported were used or some unexpected error occurred
# 2 - OS not supported by this script
# 3 - installed version of rclone is up to date
# 4 - supported unzip tools are not available

set -e

# When adding a tool to the list, make sure to also add its corresponding command further in the script
unzip_tools_list=('unzip' '7z' 'busybox')

usage() { echo "Usage: sudo -v ; curl https://rclone.org/install.sh | sudo bash [-s beta] [--version VERSION] [--force]" 1>&2; exit 1; }

# Check for flags
install_beta=""
custom_version=""
force_flag=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --beta)
            install_beta="beta "
            shift
            ;;
        --version)
            custom_version="$2"
            shift 2
            ;;
        --force)
            force_flag="--force"
            shift
            ;;
        *)
            usage
            ;;
    esac
done

# Create temp directory and move to it with macOS compatibility fallback
tmp_dir=$(mktemp -d 2>/dev/null || mktemp -d -t 'rclone-install.XXXXXXXXXX')
cd "$tmp_dir"

# Make sure unzip tool is available and choose one to work with
set +e
for tool in ${unzip_tools_list[*]}; do
    trash=$(hash "$tool" 2>>errors)
    if [ "$?" -eq 0 ]; then
        unzip_tool="$tool"
        break
    fi
done  
set -e

# Exit if no unzip tools available
if [ -z "$unzip_tool" ]; then
    printf "\nNone of the supported tools for extracting zip archives (${unzip_tools_list[*]}) were found. "
    printf "Please install one of them and try again.\n\n"
    exit 4
fi

# Make sure we don't create a root owned .config/rclone directory #2127
export XDG_CONFIG_HOME=config

# === Determine Current Version ===
if command -v rclone &>/dev/null; then
  current_installed=$(rclone --version | head -n1 | awk '{print $2}')
else
  current_installed=""
fi

# Check installed version of rclone to determine if update is necessary
version=$(rclone --version 2>>errors | head -n 1)
if [ -z "$custom_version" ]; then
    if [ -z "$install_beta" ]; then
        current_version=$(curl -fsS https://downloads.rclone.org/version.txt)
    else
        current_version=$(curl -fsS https://beta.rclone.org/version.txt)
        current_version=$(echo "$current_version" | grep -o 'v[0-9]\+\.[0-9]\+\.[0-9]\+-[a-zA-Z0-9.-]\+')
    fi
else
    current_version="$custom_version"
fi

# Check if the version is already up to date
if [ "$version" -eq "$current_version" ] && [ -z "$force_flag" ]; then
    printf "\nThe ${install_beta}version of rclone ${version} is already installed.\n\n"
    exit 3
fi

if [ -n "$current_installed" ] && [ -z "$force_flag" ]; then
  echo "Rclone version ${current_installed} is installed. Replace with version ${version}? (yes/no)"
  read -r answer
  if [ "$answer" != "yes" ]; then
    echo "Aborted."
    exit 0
  fi
fi

# Detect the platform
OS="$(uname)"
case $OS in
  Linux)
    OS='linux'
    ;;
  FreeBSD)
    OS='freebsd'
    ;;
  NetBSD)
    OS='netbsd'
    ;;
  OpenBSD)
    OS='openbsd'
    ;;  
  Darwin)
    OS='osx'
    binTgtDir=/usr/local/bin
    man1TgtDir=/usr/local/share/man/man1
    ;;
  SunOS)
    OS='solaris'
    echo 'OS not supported'
    exit 2
    ;;
  *)
    echo 'OS not supported'
    exit 2
    ;;
esac

OS_type="$(uname -m)"
case "$OS_type" in
  x86_64|amd64)
    OS_type='amd64'
    ;;
  i?86|x86)
    OS_type='386'
    ;;
  aarch64|arm64)
    OS_type='arm64'
    ;;
  armv7*)
    OS_type='arm-v7'
    ;;
  armv6*)
    OS_type='arm-v6'
    ;;
  arm*)
    OS_type='arm'
    ;;
  *)
    echo 'OS type not supported'
    exit 2
    ;;
esac

# Download and unzip
if [ -z "$install_beta" ]; then
    download_link="https://downloads.rclone.org/v${current_version}/rclone-v${current_version}-${OS}-${OS_type}.zip"
    rclone_zip="rclone-v${current_version}-${OS}-${OS_type}.zip"
else
    download_link="https://beta.rclone.org/${current_version}/rclone-${current_version}-${OS}-${OS_type}.zip"
    rclone_zip="rclone-${current_version}-${OS}-${OS_type}.zip"
fi

echo "$download_link"
curl -O "$download_link"
unzip_dir="tmp_unzip_dir_for_rclone"

# Unzip with the selected tool
case "$unzip_tool" in
  'unzip')
    unzip -a "$rclone_zip" -d "$unzip_dir"
    ;;
  '7z')
    7z x "$rclone_zip" "-o$unzip_dir"
    ;;
  'busybox')
    mkdir -p "$unzip_dir"
    busybox unzip "$rclone_zip" -d "$unzip_dir"
    ;;
esac

cd $unzip_dir/*

# Mounting rclone to environment
case "$OS" in
  'linux')
    # Binary
    cp rclone /usr/bin/rclone.new
    chmod 755 /usr/bin/rclone.new
    chown root:root /usr/bin/rclone.new
    mv /usr/bin/rclone.new /usr/bin/rclone
    # Manual
    if ! [ -x "$(command -v mandb)" ]; then
        echo 'mandb not found. The rclone man docs will not be installed.'
    else 
        mkdir -p /usr/local/share/man/man1
        cp rclone.1 /usr/local/share/man/man1/
        mandb
    fi
    ;;
  'freebsd'|'openbsd'|'netbsd')
    # Binary
    cp rclone /usr/bin/rclone.new
    chown root:wheel /usr/bin/rclone.new
    mv /usr/bin/rclone.new /usr/bin/rclone
    # Manual
    mkdir -p /usr/local/man/man1
    cp rclone.1 /usr/local/man/man1/
    makewhatis
    ;;
  'osx')
    # Binary
    mkdir -m 0555 -p ${binTgtDir}
    cp rclone ${binTgtDir}/rclone.new
    mv ${binTgtDir}/rclone.new ${binTgtDir}/rclone
    chmod a=x ${binTgtDir}/rclone
    # Manual
    mkdir -m 0555 -p ${man1TgtDir}
    cp rclone.1 ${man1TgtDir}    
    chmod a=r ${man1TgtDir}/rclone.1
    ;;
  *)
    echo 'OS not supported'
    exit 2
esac

# Update version variable post-install
version=$(rclone --version 2>>errors | head -n 1)

# Cleanup
rm -rf "$tmp_dir"

printf "\n${version} has successfully installed."
printf '\nNow run "rclone config" for setup. Check https://rclone.org/docs/ for more details.\n\n'
exit 0