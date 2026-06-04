#!/bin/bash
# Safe execution of a command stored in a variable
cmd="${MLC_SYS_UTIL_INSTALL_CMD}"
echo "$cmd"

# set the max number of retries as well as the delay between the retries
max_retries=3
delay_in_retry=3

for ((i=1; i<=max_retries; i++)); do
    echo "Attempting to install ${MLC_SYS_UTIL_NAME} - $i of $max_retries..."
    output=$(eval "$cmd" 2>&1)
    echo "$output"
    exit_status=$?

    if [[ $exit_status -eq 0 ]] && ! echo "$output" | grep -q -E "Temporary failure resolving|Unable to fetch some archives"; then
        echo "Successfully installed ${MLC_SYS_UTIL_NAME}."
        exit 0
    fi

    # Check for package manager lock errors
    if echo "$output" | grep -q -i -E "Could not get lock|Unable to acquire|dpkg.*lock|is locked by another|held by another|waiting for.*lock|another app.*holding.*lock|Failed to lock"; then
        delay=$((RANDOM % 6 + 5))
        echo "Package manager lock detected, retrying in ${delay}s..."
        sleep $delay
        continue
    fi

    # Check for network-related errors
    if echo "$output" | grep -q -E "Could not resolve|Temporary failure resolving|Unable to fetch some archives"; then
        echo "Network issue detected, retrying in $delay_in_retry seconds..."
        sleep $delay_in_retry
        continue
    fi

    # Non-recoverable error
    if [[ "${MLC_TMP_FAIL_SAFE}" == 'yes' ]]; then
        echo "MLC_GET_GENERIC_SYS_UTIL_INSTALL_FAILED=yes" > tmp-run-env.out
        echo "Fail-safe is enabled, exiting with status 0."
        exit 0
    else
        echo "Fail-safe is not enabled, exiting with error status $exit_status."
        exit $exit_status
    fi
done

# All retries exhausted
echo "Installation failed after $max_retries attempts."
if [[ "${MLC_TMP_FAIL_SAFE}" == 'yes' ]]; then
    exit 0
else
    exit 1
fi
