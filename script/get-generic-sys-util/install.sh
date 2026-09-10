#!/bin/bash
# Safe execution of a command stored in a variable
cmd="${MLC_SYS_UTIL_INSTALL_CMD}"
echo "$cmd"

max_retries=2
retry_count=0

while true; do
    output=$(eval "$cmd" 2>&1)
    exit_status=$?
    echo "$output"

    if [[ $exit_status -eq 0 ]]; then
        exit 0
    fi

    # Check for package manager lock errors
    if echo "$output" | grep -q -i -E "Could not get lock|Unable to acquire|dpkg.*lock|is locked by another|held by another|waiting for.*lock|another app.*holding.*lock|Failed to lock"; then
        retry_count=$((retry_count + 1))
        if [[ $retry_count -le $max_retries ]]; then
            delay=$((RANDOM % 6 + 5))
            echo "Package manager lock detected. Retrying in ${delay}s (attempt ${retry_count}/${max_retries})..."
            sleep $delay
            continue
        else
            echo "Package manager lock still held after ${max_retries} retries."
        fi
    fi

    # Not a lock error or retries exhausted
    if [[ "${MLC_TMP_FAIL_SAFE}" == 'yes' ]]; then
        echo "MLC_GET_GENERIC_SYS_UTIL_INSTALL_FAILED=yes" > tmp-run-env.out
        echo "Fail-safe is enabled, exiting with status 0"
        exit 0
    else
        exit $exit_status
    fi
done
