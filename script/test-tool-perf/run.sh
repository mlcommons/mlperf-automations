#!/bin/bash
# Functional test for perf: record a short, bounded system-wide profile and
# confirm perf.data was produced and is decodable. Mirrors the run-time use of
# 'perf record -a' so a failure here surfaces broken counter access before a long
# SPEC run starts.

perf_bin=${MLC_PERF_BIN_WITH_PATH}
duration=${MLC_TEST_PROFILER_DURATION:-2}

tmpd=$(mktemp -d)
data="${tmpd}/perf.data"
log="${tmpd}/perf_test.log"

# Profiled workload is a brief, bounded CPU burn (never scans the filesystem);
# trailing ':' guarantees a 0 exit so perf's return code reflects perf itself.
echo "Testing perf: ${perf_bin} record -a -o ${data} -- (${duration}s cpu load)"
"${perf_bin}" record -a -o "${data}" -- sh -c "timeout ${duration} yes > /dev/null 2>&1; :" > "${log}" 2>&1
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
