#!/bin/bash
# Functional test for perf: record a short system-wide profile of a small command
# and confirm perf.data was produced and is readable. Mirrors the run-time use of
# 'perf record -a' so a failure here surfaces broken counter access before a long
# SPEC run starts.

perf_bin=${MLC_PERF_BIN_WITH_PATH}

tmpd=$(mktemp -d)
data="${tmpd}/perf.data"
log="${tmpd}/perf_test.log"

echo "Testing perf: ${perf_bin} record -a -o ${data} -- ls -laR /"
"${perf_bin}" record -a -o "${data}" -- ls -laR / > "${log}" 2>&1
rc=$?
if [ ${rc} -ne 0 ]; then
    echo "ERROR: 'perf record' test failed (rc=${rc}):" >&2
    cat "${log}" >&2
    rm -rf "${tmpd}"
    exit ${rc}
fi

if [ ! -s "${data}" ]; then
    echo "ERROR: perf produced no data at ${data}:" >&2
    cat "${log}" >&2
    rm -rf "${tmpd}"
    exit 1
fi

# Confirm the recorded data is decodable (counters actually captured samples).
if ! "${perf_bin}" report -i "${data}" --stdio > /dev/null 2>>"${log}"; then
    echo "ERROR: recorded perf.data could not be decoded:" >&2
    cat "${log}" >&2
    rm -rf "${tmpd}"
    exit 1
fi

echo "perf functional test passed (data at ${data})."
rm -rf "${tmpd}"
