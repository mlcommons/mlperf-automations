#!/bin/bash

# Check if MLC_GIT_REPO_CHECKOUT_PATH is set
if [ -z "${MLC_GIT_REPO_CHECKOUT_PATH}" ]; then
    echo "Error: MLC_GIT_REPO_CHECKOUT_PATH is not set."
    exit 1
fi

cd "${MLC_GIT_REPO_CHECKOUT_PATH}"
git pull
git add *

if [[ -n ${MLC_MLPERF_INFERENCE_SUBMISSION_DIR} ]]; then
    rsync -avz "${MLC_MLPERF_INFERENCE_SUBMISSION_DIR}/" "${MLC_GIT_REPO_CHECKOUT_PATH}/"
    git add *
fi
test $? -eq 0 || exit $?

git commit -a -m "${MLC_MLPERF_RESULTS_REPO_COMMIT_MESSAGE}"

echo ${MLC_GIT_PUSH_CMD}
${MLC_GIT_PUSH_CMD}

test $? -eq 0 || (sleep $((RANDOM % 200 + 1)) && git pull && ${MLC_GIT_PUSH_CMD})

test $? -eq 0 || exit $?
