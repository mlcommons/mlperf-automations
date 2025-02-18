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
#Add your run commands here...
# run "$MLC_RUN_CMD"

POWER=" --power=yes --adr.mlperf-power-client.power_server=192.168.0.15 --adr.mlperf-power-client.port=4950 "
POWER=" --env.MLC_GET_PLATFORM_DETAILS=no"

#run "mlcr set,system,performance,mode"

run "mlcr generate-run-cmds,inference,_find-performance \
--model=resnet50 --implementation=cpp --device=cuda --backend=onnxruntime \
--adr.compiler.tags=gcc \
--test_query_count=20000 \
--category=edge --division=open --scenario=Offline  --quiet"


#cpp
run "mlcr generate-run-cmds,inference,_find-performance \
--model=resnet50 --implementation=cpp --device=cpu --backend=onnxruntime \
--adr.compiler.tags=gcc \
--category=edge --division=open --scenario=Offline  --quiet --test_query_count=2000 "

run "mlcr generate-run-cmds,inference,_find-performance \
--model=retinanet --implementation=cpp --device=cpu --backend=onnxruntime \
--adr.compiler.tags=gcc \
--category=edge --division=open --scenario=Offline  --quiet"


run "mlcr generate-run-cmds,inference,_submission \
--model=resnet50 --implementation=cpp --device=cpu --backend=onnxruntime \
--scenario=Offline \
--category=edge --division=$division  --quiet \
--adr.compiler.tags=gcc \
--execution_mode=valid \
--skip_submission_generation=yes \
${POWER} \
--results_dir=$HOME/results_dir"

run "mlcr generate-run-cmds,inference,_submission \
--model=retinanet --implementation=cpp --device=cpu --backend=onnxruntime \
--scenario=Offline \
--category=edge --division=$division  --quiet \
--adr.compiler.tags=gcc \
--execution_mode=valid \
--skip_submission_generation=yes \
${POWER} \
--results_dir=$HOME/results_dir"

run "mlcr generate-run-cmds,inference,_submission \
--model=resnet50 --implementation=cpp --device=cpu --backend=onnxruntime \
--scenario=SingleStream \
--category=edge --division=$division  --quiet \
--adr.compiler.tags=gcc \
--execution_mode=valid \
--skip_submission_generation=yes \
${POWER} \
--results_dir=$HOME/results_dir"

run "mlcr generate-run-cmds,inference,_submission \
--model=retinanet --implementation=cpp --device=cpu --backend=onnxruntime \
--scenario=SingleStream \
--category=edge --division=$division  --quiet \
--adr.compiler.tags=gcc \
--execution_mode=valid \
--skip_submission_generation=yes \
${POWER} \
--results_dir=$HOME/results_dir"

# GPU

run "mlcr generate-run-cmds,inference,_find-performance \
--model=resnet50 --implementation=cpp --device=cuda --backend=onnxruntime \
--adr.compiler.tags=gcc \
--test_query_count=20000 \
--category=edge --division=open --scenario=Offline  --quiet"

run "mlcr generate-run-cmds,inference,_find-performance \
--model=retinanet --implementation=cpp --device=cuda --backend=onnxruntime \
--adr.compiler.tags=gcc \
--test_query_count=2000   \
--category=edge --division=open --scenario=Offline  --quiet"


run "mlcr generate-run-cmds,inference,_submission \
--scenario=Offline \
--model=resnet50 --implementation=cpp --device=cuda --backend=onnxruntime \
--category=edge --division=$division  --quiet \
--adr.compiler.tags=gcc \
--execution_mode=valid \
--skip_submission_generation=yes \
${POWER} \
--results_dir=$HOME/results_dir"

run "mlcr generate-run-cmds,inference,_submission \
--model=retinanet --implementation=cpp --device=cuda --backend=onnxruntime \
--scenario=Offline \
--category=edge --division=$division  --quiet \
--adr.compiler.tags=gcc \
--execution_mode=valid \
--skip_submission_generation=yes \
${POWER} \
--results_dir=$HOME/results_dir"


run "mlcr generate-run-cmds,inference,_submission \
--scenario=Offline \
--model=resnet50 --implementation=cpp --device=cuda --backend=onnxruntime \
--scenario=SingleStream \
--category=edge --division=$division  --quiet \
--adr.compiler.tags=gcc \
--execution_mode=valid \
--skip_submission_generation=yes \
${POWER} \
--results_dir=$HOME/results_dir"

run "mlcr generate-run-cmds,inference,_submission \
--model=retinanet --implementation=cpp --device=cuda --backend=onnxruntime \
--scenario=SingleStream \
--category=edge --division=$division  --quiet \
--adr.compiler.tags=gcc \
--execution_mode=valid \
--skip_submission_generation=yes \
${POWER} \
--results_dir=$HOME/results_dir"

#multistream
run "mlcr generate-run-cmds,inference,_submission \
--scenario=Offline \
--model=resnet50 --implementation=cpp --device=cuda --backend=onnxruntime \
--scenario=MultiStream \
--category=edge --division=$division  --quiet \
--adr.compiler.tags=gcc \
--execution_mode=valid \
--skip_submission_generation=yes \
${POWER} \
--results_dir=$HOME/results_dir"

run "mlcr generate-run-cmds,inference,_submission \
--model=retinanet --implementation=cpp --device=cuda --backend=onnxruntime \
--scenario=MultiStream \
--category=edge --division=$division  --quiet \
--adr.compiler.tags=gcc \
--execution_mode=valid \
--skip_submission_generation=yes \
${POWER} \
--results_dir=$HOME/results_dir"
