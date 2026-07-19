#!/bin/bash

#MLC Script location: ${MLC_TMP_CURRENT_SCRIPT_PATH}

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
run "mlcr generate-run-cmds,inference,_find-performance \
--model=resnet50 --implementation=reference --device=cpu --backend=onnxruntime \
--category=edge --division=open --scenario=Offline  --quiet --test_query_count=100"

run "mlcr generate-run-cmds,inference,_find-performance \
--model=rnnt --implementation=reference --device=cpu --backend=pytorch \
--category=edge --division=open --scenario=Offline  --quiet"

run "mlcr generate-run-cmds,inference,_find-performance \
--model=retinanet --implementation=reference --device=cpu --backend=pytorch \
--category=edge --division=open --scenario=Offline  --quiet"

run "mlcr generate-run-cmds,inference,_find-performance \
--model=bert-99 --implementation=reference --device=cpu --backend=pytorch \
--category=edge --division=open --scenario=Offline  --quiet"

run "mlcr generate-run-cmds,inference,_find-performance \
--model=3d-unet-99 --implementation=reference --device=cpu --backend=pytorch \
--category=edge --division=open --scenario=Offline  --quiet"

run "mlcr generate-run-cmds,inference,_submission,_all-scenarios \
--model=resnet50 --implementation=reference --device=cpu --backend=onnxruntime \
--category=edge --division=$division  --quiet"

run "mlcr generate-run-cmds,inference,_submission,_all-scenarios \
--model=rnnt --implementation=reference --device=cpu --backend=pytorch \
--category=edge --division=$division  --quiet"

run "mlcr generate-run-cmds,inference,_submission,_all-scenarios \
--model=retinanet --implementation=reference --device=cpu --backend=pytorch \
--category=edge --division=$division  --quiet"

run "mlcr generate-run-cmds,inference,_submission,_all-scenarios \
--model=bert-99 --implementation=reference --device=cpu --backend=pytorch \
--category=edge --division=$division  --quiet"

run "mlcr generate-run-cmds,inference,_submission,_all-scenarios \
--model=3d-unet-99 --implementation=reference --device=cpu --backend=pytorch \
--category=edge --division=$division  --quiet"

