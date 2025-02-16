#!/bin/bash

#CM Script location: ${MLC_TMP_CURRENT_SCRIPT_PATH}

#To export any variable
#echo "VARIABLE_NAME=VARIABLE_VALUE" >>tmp-run-env.out

#${MLC_PYTHON_BIN_WITH_PATH} contains the path to python binary if "get,python" is added as a dependency



function exit_if_error() {
  test $? -eq 0 || exit $?
}

function run() {
  echo "Running: "
  echo "$1"
  echo ""
  if [[ ${MLC_FAKE_RUN} != 'yes' ]]; then
    eval "$1"
    exit_if_error
  fi
}
POWER=" --power=yes --adr.mlperf-power-client.power_server=192.168.0.15 --adr.mlperf-power-client.port=4940 "
POWER=""
extra_option=""
extra_tags=""
#extra_option=" --adr.mlperf-inference-implementation.compressed_dataset=on"
#extra_tags=",_only-fp32"


#Add your run commands here...
# run "$MLC_RUN_CMD"
run "mlcr run,mobilenet-models,_tflite,_accuracy-only$extra_tags \
--adr.compiler.tags=gcc \
${extra_option} "

run "mlcr run,mobilenet-models,_tflite,_performance-only$extra_tags \
${POWER} \
--adr.compiler.tags=gcc \
${extra_option}"


run "mlcr run,mobilenet-models,_tflite,_armnn,_neon,_accuracy-only$extra_tags \
--adr.compiler.tags=gcc \
${extra_option} "

run "mlcr run,mobilenet-models,_tflite,_armnn,_neon,_performance-only$extra_tags \
${POWER} \
${extra_option} \
--adr.compiler.tags=gcc"

