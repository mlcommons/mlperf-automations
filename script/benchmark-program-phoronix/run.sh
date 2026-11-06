#!/bin/bash

# Benchmark Program - Phoronix Test Suite (non-interactive / batch)

set -o pipefail

# --- Sanitize PATH ------------------------------------------------------------
# The phoronix-test-suite launcher is a /bin/sh (dash) wrapper that shells out to
# coreutils (dirname, readlink, mktemp, sh, ...). A PATH polluted with non-POSIX
# entries (e.g. Windows "c:\...;" paths injected by some IDE terminals) makes
# dash fail to resolve them. Keep only absolute POSIX dirs and guarantee the
# standard system locations are present.
_clean_path=""
_oldifs="$IFS"; IFS=':'
for _p in $PATH; do
  case "$_p" in
    /*) ;;                      # keep absolute POSIX paths only
    *) continue ;;
  esac
  case "$_p" in *'\'*|*';'*) continue ;; esac
  _clean_path="${_clean_path:+$_clean_path:}$_p"
done
IFS="$_oldifs"
for _sys in /usr/local/sbin /usr/local/bin /usr/sbin /usr/bin /sbin /bin; do
  case ":$_clean_path:" in
    *":$_sys:"*) ;;
    *) _clean_path="${_clean_path:+$_clean_path:}$_sys" ;;
  esac
done
export PATH="$_clean_path"

# --- Resolve the launcher provided by the get,phoronix-test-suite dep ----------
PTS="${MLC_PHORONIX_TEST_SUITE_BIN_WITH_PATH:-phoronix-test-suite}"
if ! command -v "${PTS}" &> /dev/null && [ ! -x "${PTS}" ]; then
  echo "ERROR: phoronix-test-suite launcher not found (expected from the get,phoronix-test-suite dependency; MLC_PHORONIX_TEST_SUITE_BIN_WITH_PATH=${MLC_PHORONIX_TEST_SUITE_BIN_WITH_PATH})"
  exit 1
fi

if [ -z "${MLC_PHORONIX_TEST}" ]; then
  echo "MLC_PHORONIX_TEST is not set"
  exit 1
fi

RESULTS_DIR=${MLC_PHORONIX_RESULTS_DIR:-.}
RESULT_ID=${MLC_PHORONIX_RESULT_IDENTIFIER:-mlc-benchmark}
mkdir -p "${RESULTS_DIR}"

# --- Seed a non-interactive config (skips the first-run EULA / anonymous-usage
# prompts and makes `batch-benchmark` fully unattended). Only written when
# absent so an existing user configuration is respected. ----------------------
PTS_USER_DIR="${HOME}/.phoronix-test-suite"
if [ ! -f "${PTS_USER_DIR}/user-config.xml" ]; then
  mkdir -p "${PTS_USER_DIR}"
  cat > "${PTS_USER_DIR}/user-config.xml" <<'XML_EOF'
<?xml version="1.0"?>
<PhoronixTestSuite>
  <Options>
    <OpenBenchmarking>
      <AnonymousUsageReporting>FALSE</AnonymousUsageReporting>
      <AnonymousSoftwareReporting>FALSE</AnonymousSoftwareReporting>
      <AnonymousHardwareReporting>FALSE</AnonymousHardwareReporting>
      <AllowResultUploadsToOpenBenchmarking>FALSE</AllowResultUploadsToOpenBenchmarking>
    </OpenBenchmarking>
    <General>
      <UsePhodeviCache>TRUE</UsePhodeviCache>
    </General>
    <Installation>
      <RemoveDownloadFiles>FALSE</RemoveDownloadFiles>
      <SearchMediaForCache>TRUE</SearchMediaForCache>
      <PromptForDownloadMirror>FALSE</PromptForDownloadMirror>
    </Installation>
    <Testing>
      <SaveSystemLogs>TRUE</SaveSystemLogs>
      <SaveInstallationLogs>TRUE</SaveInstallationLogs>
      <SaveTestLogs>TRUE</SaveTestLogs>
      <AlwaysUploadResultsToOpenBenchmarking>FALSE</AlwaysUploadResultsToOpenBenchmarking>
    </Testing>
    <TestResultValidation>
      <DynamicRunCount>TRUE</DynamicRunCount>
      <LimitDynamicToTestLength>20</LimitDynamicToTestLength>
      <TimesToRunEmptyResults>2</TimesToRunEmptyResults>
      <MinimalTestTime>2</MinimalTestTime>
      <DropNoisyResults>FALSE</DropNoisyResults>
    </TestResultValidation>
    <BatchMode>
      <SaveResults>TRUE</SaveResults>
      <OpenBrowser>FALSE</OpenBrowser>
      <UploadResults>FALSE</UploadResults>
      <PromptForTestIdentifier>FALSE</PromptForTestIdentifier>
      <PromptForTestDescription>FALSE</PromptForTestDescription>
      <PromptSaveName>FALSE</PromptSaveName>
      <RunAllTestCombinations>TRUE</RunAllTestCombinations>
      <Configured>TRUE</Configured>
    </BatchMode>
    <Networking>
      <NoNetworkCommunication>FALSE</NoNetworkCommunication>
      <Timeout>20</Timeout>
    </Networking>
  </Options>
</PhoronixTestSuite>
XML_EOF
  echo "Wrote non-interactive PTS config: ${PTS_USER_DIR}/user-config.xml"
fi

# Pre-answer the result save prompts (used when PromptSaveName etc. are FALSE).
export TEST_RESULTS_NAME="${RESULT_ID}"
export TEST_RESULTS_IDENTIFIER="${RESULT_ID}"
export TEST_RESULTS_DESCRIPTION="MLC automated benchmark run"

# Number of runs per test.
if [ -n "${MLC_PHORONIX_NUM_RUNS}" ]; then
  export FORCE_TIMES_TO_RUN=${MLC_PHORONIX_NUM_RUNS}
fi

# Compiler toolchain is taken from the environment (e.g. set by run-phoronix-amd).
# PTS honours CC/CXX/CFLAGS/CXXFLAGS when it compiles tests from source.
echo ""
echo "Compiler environment:"
echo "  CC=${CC:-<system default>}"
echo "  CXX=${CXX:-<system default>}"
echo "  FC=${FC:-<system default>}"
echo "  CFLAGS=${CFLAGS}"
echo "  CXXFLAGS=${CXXFLAGS}"

echo ""
echo "***********************************************************************"
echo "Running Phoronix Test Suite"
echo "  Test: ${MLC_PHORONIX_TEST}"
echo "  Runs: ${MLC_PHORONIX_NUM_RUNS}"
echo "  Batch mode: ${MLC_PHORONIX_BATCH_MODE}"
echo "  Result id: ${RESULT_ID}"
echo "***********************************************************************"

# Install the test (compiles from source using CC/CXX when applicable).
echo ""
echo "Installing test: ${MLC_PHORONIX_TEST}"
"${PTS}" install "${MLC_PHORONIX_TEST}"
rc=$?
if [ ${rc} -ne 0 ]; then
  echo "ERROR: phoronix-test-suite install failed (status ${rc})"
  exit ${rc}
fi

OUTPUT_FILE="${RESULTS_DIR}/phoronix_output.txt"
echo ""
echo "Running benchmark..."
if [ "${MLC_PHORONIX_BATCH_MODE}" == "yes" ]; then
  "${PTS}" batch-benchmark ${MLC_PHORONIX_EXTRA_ARGS} "${MLC_PHORONIX_TEST}" 2>&1 | tee "${OUTPUT_FILE}"
else
  "${PTS}" benchmark ${MLC_PHORONIX_EXTRA_ARGS} "${MLC_PHORONIX_TEST}" 2>&1 | tee "${OUTPUT_FILE}"
fi
exitstatus=${PIPESTATUS[0]}

if [ ${exitstatus} -ne 0 ]; then
  echo "Phoronix Test Suite exited with status: ${exitstatus}"
  exit ${exitstatus}
fi

# Export results. PTS sanitizes the save identifier (strips dots/spaces),
# so discover the actual saved result directory (most recently modified) rather
# than assuming it equals RESULT_ID.
pts_results_root="${HOME}/.phoronix-test-suite/test-results"
saved_name=""
if [ -d "${pts_results_root}" ]; then
  saved_name=$(ls -1t "${pts_results_root}" 2>/dev/null | head -1)
fi

if [ -n "${saved_name}" ]; then
  # Archive the raw composite.xml.
  if [ -f "${pts_results_root}/${saved_name}/composite.xml" ]; then
    cp -f "${pts_results_root}/${saved_name}/composite.xml" "${RESULTS_DIR}/phoronix_composite.xml"
  fi
  # `result-file-to-json` writes a file and prints "Saved Output To: <path>"
  # (with ANSI colour codes) instead of emitting JSON on stdout.
  json_msg=$("${PTS}" result-file-to-json "${saved_name}" 2>/dev/null)
  saved_json=$(printf '%s\n' "$json_msg" \
    | sed -r 's/\x1B\[[0-9;]*[mK]//g' \
    | sed -n 's/.*Saved Output To:[[:space:]]*//p' | tr -d '\r' | tail -1)
  if [ -n "${saved_json}" ] && [ -f "${saved_json}" ]; then
    cp -f "${saved_json}" "${RESULTS_DIR}/phoronix_results.json"
  fi
fi

echo ""
echo "***********************************************************************"
echo "Phoronix Test Suite completed successfully."
echo "***********************************************************************"
