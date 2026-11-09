#!/bin/bash

if [ -f "${MLC_APPTAINERFILE_WITH_PATH}" ]; then

  # mksquashfs opens one fd per CPU; on >1024-core nodes the default soft nofile limit is too low.
  ulimit -n "$(ulimit -Hn)" 2>/dev/null || true
  eval "${MLC_APPTAINER_BUILD_CMD}"
  test $? -eq 0 || exit 1

  echo ""
fi
