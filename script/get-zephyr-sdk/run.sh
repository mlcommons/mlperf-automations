#!/bin/bash
MLC_TMP_CURRENT_SCRIPT_PATH=${MLC_TMP_CURRENT_SCRIPT_PATH:-$PWD}
version=${MLC_ZEPHYR_SDK_VERSION}
os=${MLC_HOST_OS_TYPE}
if [ $os == "darwin" ]; then
  os=${MLC_HOST_OS_FLAVOR}
fi
platform=${MLC_HOST_OS_MACHINE}
if [ $platform == "arm64" ]; then
  platform=aarch64
fi

file=zephyr-sdk-${version}-${os}-${platform}-setup.run
url=https://github.com/zephyrproject-rtos/sdk-ng/releases/download/v${version}/$file
wget -nc "${url}"
if [ "${?}" != "0" ]; then exit 1; fi
chmod +x $file
./$file -- -d $PWD/zephyr-sdk-$version -y

if [ "${?}" != "0" ]; then exit 1; fi

