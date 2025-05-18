#!/bin/bash

if [[ ${MLC_SUDO_USER} == "yes" ]]; then
  ${MLC_SUDO} dmidecode -t memory > ${MLC_MEMINFO_FILE}
fi
test $? -eq 0 || echo "Warning: Memory info is not recorded"
