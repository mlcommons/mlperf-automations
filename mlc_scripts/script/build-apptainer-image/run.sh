#!/bin/bash

if [ -f "${MLC_APPTAINERFILE_WITH_PATH}" ]; then

  eval "${MLC_APPTAINER_BUILD_CMD}"
  test $? -eq 0 || exit 1

  echo ""
fi
