#!/bin/bash
uprof_bin=${MLC_UPROF_BIN_WITH_PATH}
echo "${uprof_bin} --version"
${uprof_bin} --version > tmp-ver.out
test $? -eq 0 || exit $?

# Lightweight capability probe (no data collection): uProf samples core PMCs/IBS
# through the kernel perf_events subsystem, so confirm it is present. Actual
# counter access (NMI watchdog off, perf_event_paranoid relaxed) is arranged
# later by the run script, so we deliberately do NOT run a full collection here.
if [ ! -e /proc/sys/kernel/perf_event_paranoid ]; then
    echo "ERROR: kernel perf_events subsystem not present (/proc/sys/kernel/perf_event_paranoid missing); uProf cannot sample hardware counters on this host." >&2
    exit 1
fi
echo "uProf capability probe passed."
