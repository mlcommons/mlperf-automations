#!/bin/bash
perf_bin=${MLC_PERF_BIN_WITH_PATH}
${perf_bin} --version > tmp-ver.out
test $? -eq 0 || exit $?

# Lightweight capability probe (no counter collection): confirm the kernel
# perf_events subsystem is present and this perf build can enumerate hardware
# events. Actual counter access / paranoid relaxation happens later in the run,
# so we avoid a real record/stat that could false-fail before that setup.
if [ ! -e /proc/sys/kernel/perf_event_paranoid ]; then
    echo "ERROR: kernel perf_events subsystem not present (/proc/sys/kernel/perf_event_paranoid missing); perf cannot profile on this host." >&2
    exit 1
fi
${perf_bin} list hw > tmp-list.out 2>&1
if [ $? -ne 0 ]; then
    echo "ERROR: 'perf list hw' failed; this perf build cannot enumerate hardware events:" >&2
    cat tmp-list.out >&2
    exit 1
fi
echo "perf capability probe passed."
