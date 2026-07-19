#!/bin/bash

# Runs the inference-endpoint benchmark assembled in customize.py. When the
# --echo-server variation is active, the bundled echo server is launched first
# (for self-contained local testing) and torn down on exit.

VENV_PYTHON="${MLC_MLPERF_ENDPOINTS_PYTHON_BIN}"

ECHO_PID=""
cleanup() {
  if [[ -n "${ECHO_PID}" ]]; then
    kill "${ECHO_PID}" 2>/dev/null
    wait "${ECHO_PID}" 2>/dev/null
  fi
}
trap cleanup EXIT

if [[ "${MLC_MLPERF_ENDPOINT_USE_ECHO_SERVER}" == "yes" ]]; then
  PORT="${MLC_MLPERF_ENDPOINT_ECHO_SERVER_PORT}"
  ECHO_LOG="${MLC_MLPERF_ENDPOINT_REPORT_DIR}/echo_server.log"
  echo ""
  echo "Starting bundled echo server on port ${PORT}"
  "${VENV_PYTHON}" -m inference_endpoint.testing.echo_server \
    --port "${PORT}" > "${ECHO_LOG}" 2>&1 &
  ECHO_PID=$!
  # Poll until the server accepts connections (robust under load — a fixed
  # sleep races the benchmark against a not-yet-bound port).
  READY=""
  for _ in $(seq 1 60); do
    if ! kill -0 "${ECHO_PID}" 2>/dev/null; then
      echo "Echo server exited early. Log:"; cat "${ECHO_LOG}"; exit 1
    fi
    if "${VENV_PYTHON}" -c "import socket,sys; s=socket.socket(); s.settimeout(0.5); sys.exit(0 if s.connect_ex(('127.0.0.1', ${PORT}))==0 else 1)" 2>/dev/null; then
      READY="yes"; break
    fi
    sleep 0.5
  done
  if [[ -z "${READY}" ]]; then
    echo "Echo server did not become ready on port ${PORT}. Log:"; cat "${ECHO_LOG}"
    exit 1
  fi
fi

echo ""
echo "${MLC_MLPERF_ENDPOINT_CMD}"
echo ""
eval "${MLC_MLPERF_ENDPOINT_CMD}"
EXIT_CODE=$?

test ${EXIT_CODE} -eq 0 || exit ${EXIT_CODE}
