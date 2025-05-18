#!/bin/bash

# function to safely exit the background process
safe_exit() {
  if [[ "${MLC_POST_RUN_CMD}" != "" ]]; then
    eval ${MLC_POST_RUN_CMD}
    if [ $? -eq 0 ]; then
      exit 0
    else
      exit $?
    fi
  fi
}

# trap signals to redirect the execution flow to safe_exit
trap safe_exit SIGINT SIGTERM

if [[ ${MLC_MLPERF_POWER} == "yes" && ${MLC_MLPERF_LOADGEN_MODE} == "performance" ]]; then
    exit 0
fi

# Run
if [ -z "${MLC_RUN_DIR}" ]; then
  echo "MLC_RUN_DIR is not set"
  exit 1
fi

cd "${MLC_RUN_DIR}"

if [[ "${MLC_DEBUG_SCRIPT_BENCHMARK_PROGRAM}" == "True" ]]; then
  echo "*****************************************************"
  echo "You are now in Debug shell with pre-set CM env and can run the following command line manually:"

  echo ""
  if [[ "${MLC_RUN_CMD0}" != "" ]]; then
    echo "${MLC_RUN_CMD0}"
  else
    echo "${MLC_RUN_CMD}"
  fi

  echo ""
  echo "Type exit to return to CM script."
  echo ""
#  echo "You can also run . ./debug-script-benchmark-program.sh to reproduce and customize run."
#  echo ""
#
#  cp -f tmp-run.sh debug-script-benchmark-program.sh
#
#  sed -e 's/MLC_DEBUG_SCRIPT_BENCHMARK_PROGRAM="True"/MLC_DEBUG_SCRIPT_BENCHMARK_PROGRAM="False"/g' -i debug-script-benchmark-program.sh

  bash

  # do not re-run command below to pick up manual run!
  exit 0
fi

echo $MLC_PRE_RUN_CMD
eval ${MLC_PRE_RUN_CMD}

# Function to run command and check exit status
run_command() {
  local cmd="$1"
  
  if [[ -n "$cmd" ]]; then
    echo "$cmd"
    eval "$cmd"
    exitstatus=$?

    # If 'exitstatus' file exists, overwrite the exit status with its content
    if [[ -e exitstatus ]]; then
      exitstatus=$(cat exitstatus)
    fi

    # If exitstatus is non-zero, exit with that status
    if [[ $exitstatus -ne 0 ]]; then
      exit $exitstatus
    fi
  fi
}

# Run MLC_RUN_CMD0 if it exists, otherwise run MLC_RUN_CMD
if [[ -n "$MLC_RUN_CMD0" ]]; then
    run_command "$MLC_RUN_CMD0"
fi

run_command "$MLC_RUN_CMD"


# Run post-run command if it exists
if [[ -n "$MLC_POST_RUN_CMD" ]]; then
  eval "$MLC_POST_RUN_CMD"
  post_exitstatus=$?
  # Exit if post-run command fails
  if [[ $post_exitstatus -ne 0 ]]; then
    exit $post_exitstatus
  fi
fi

# Final check for exitstatus and exit with the appropriate code
if [[ $exitstatus -ne 0 ]]; then
  exit $exitstatus
fi
