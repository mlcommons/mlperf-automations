#!/bin/bash

MLC_TMP_CURRENT_SCRIPT_PATH=${MLC_TMP_CURRENT_SCRIPT_PATH:-$PWD}
MLC_PYTHON_BIN_WITH_PATH=${MLC_PYTHON_BIN_WITH_PATH:-python3}

CUR=`pwd`

if [ "${?}" != "0" ]; then exit 1; fi

if [ ! -d "zephyr" ]; then
  west init --mr ${MLC_ZEPHYR_VERSION}-branch $CUR
  if [ "${?}" != "0" ]; then exit 1; fi
fi

cd $CUR/zephyr
west update
if [ "${?}" != "0" ]; then exit 1; fi
west zephyr-export
if [ "${?}" != "0" ]; then exit 1; fi
${MLC_PYTHON_BIN_WITH_PATH} -m pip install -r $CUR/zephyr/scripts/requirements.txt
if [ "${?}" != "0" ]; then exit 1; fi

