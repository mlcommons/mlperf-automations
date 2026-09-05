#!/bin/bash
# Functional test for AMD uProf: run a short system-wide collection and confirm
# it produces output. AMDuProfSys is a background/system-wide collector stopped
# via SIGINT (it does not launch a target command), so we start it, exercise the
# CPU briefly with a small command, then stop and verify session data was written.

uprof_bin=${MLC_UPROF_BIN_WITH_PATH}
config=${MLC_UPROF_PROFILE:-core}

tmpd=$(mktemp -d)
outdir="${tmpd}/uprof_test"
log="${tmpd}/uprof_test.log"

echo "Testing uProf: ${uprof_bin} collect --config ${config} -a -o ${outdir}"
"${uprof_bin}" collect --config "${config}" -a -o "${outdir}" > "${log}" 2>&1 &
upid=$!

sleep 2
if ! kill -0 "${upid}" 2>/dev/null; then
    echo "ERROR: uProf failed to start:" >&2
    cat "${log}" >&2
    rm -rf "${tmpd}"
    exit 1
fi

# Brief CPU activity for uProf to sample.
ls -laR / > /dev/null 2>&1

# Graceful stop; SIGINT lets AMDuProfSys finalize and write its data files.
kill -INT "${upid}" 2>/dev/null
for _ in $(seq 1 30); do
    kill -0 "${upid}" 2>/dev/null || break
    sleep 1
done
kill -0 "${upid}" 2>/dev/null && kill -KILL "${upid}" 2>/dev/null
wait "${upid}" 2>/dev/null

if [ -z "$(ls -A "${outdir}" 2>/dev/null)" ]; then
    echo "ERROR: uProf test produced no output in ${outdir}:" >&2
    cat "${log}" >&2
    rm -rf "${tmpd}"
    exit 1
fi

echo "uProf functional test passed (output in ${outdir})."
rm -rf "${tmpd}"
