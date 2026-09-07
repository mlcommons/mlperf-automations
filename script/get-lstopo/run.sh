#!/bin/bash

set -e

# Where the topology lands. Defaults keep the historical behaviour (topo.xml
# in the caller's cwd) so existing users of get,lstopo are unaffected; callers
# that need a predictable path -- e.g. get-mlperf-single-node-system-info,
# which parks the XML next to the sysinfo JSON so both can be copied back from
# a remote node together -- set these two.
OUT_DIR="${MLC_LSTOPO_OUT_DIR_PATH:-$(pwd)}"
OUT_FILE="${MLC_LSTOPO_OUT_FILE_NAME:-topo.xml}"

mkdir -p "${OUT_DIR}"
OUT_PATH="${OUT_DIR}/${OUT_FILE}"

rm -f "${OUT_PATH}"
lstopo "${OUT_PATH}"
echo "MLC_LSTOPO_XML_FILE_PATH=${OUT_PATH}" > tmp-run-env.out
echo "lstopo topology written to ${OUT_PATH}"
