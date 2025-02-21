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
division="closed"
model="resnet50"
device="cpu"
category="edge"
rerun="$rerun"
function run_test() {
  backend=$1
  test_query_count=$2
  implementation=$3
  device=$4
  run "$5"
}
power=' --power=yes --adr.mlperf-power-client.power_server=192.168.0.15 --adr.mlperf-power-client.port=4950 '
power=''

#Add your run commands here...
find_performance_cmd='mlcr generate-run-cmds,inference,_find-performance \
--model=$model --implementation=$implementation --device=$device --backend=$backend \
--category=edge --division=open --scenario=Offline  --quiet --test_query_count=$test_query_count $rerun'

submission_cmd='mlcr generate-run-cmds,inference,_submission,_all-scenarios \
--model=$model --implementation=$implementation --device=$device --backend=$backend \
--category=$category --division=$division  --quiet --results_dir=$HOME/results_dir \
--skip_submission_generation=yes --execution_mode=valid $power'

submission_cmd_scenario='mlcr generate-run-cmds,inference,_submission  --scenario=$scenario \
--model=$model --implementation=$implementation --device=$device --backend=$backend \
--category=$category --division=$division  --quiet --results_dir=$HOME/results_dir \
--skip_submission_generation=yes --execution_mode=valid $power'


# run "$MLC_RUN_CMD"
run_test "onnxruntime" "200" "reference" "cpu" "$find_performance_cmd"
run_test "tf" "200" "reference" "cpu" "$find_performance_cmd"

run_test "onnxruntime" "100" "reference" "cpu" "$submission_cmd"
run_test "tf" "100" "reference" "cpu" "$submission_cmd"
scenario="SingleStream"
run_test "tflite" "100" "tflite-cpp" "cpu" "$submission_cmd_scenario --adr.compiler.tags=gcc"
run_test "tflite" "100" "tflite-cpp" "cpu" "$submission_cmd_scenario --adr.compiler.tags=gcc --adr.mlperf-inference-implementation.compressed_dataset=on"


run_test "onnxruntime" "10000" "reference" "cuda" "$find_performance_cmd"
run_test "tf" "20000" "reference" "cuda" "$find_performance_cmd"
run_test "onnxruntime" "100" "reference" "cuda" "$submission_cmd "
run_test "tf" "100" "reference" "cuda" "$submission_cmd"

