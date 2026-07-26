#!/bin/bash

eval "${MLC_REDFISH_CMD}"
EXIT_CODE=$?
test ${EXIT_CODE} -eq 0 || exit ${EXIT_CODE}
