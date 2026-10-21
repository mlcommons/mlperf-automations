#!/bin/bash
# Build llama.cpp (llama-server target) with a caller-selected compiler.
# Inputs via environment:
#   LLAMA_CPP_SRC_PATH  (required)  llama.cpp checkout
#   LLAMA_BUILD_DIR     (optional)  build tree, default $SRC/build
#   CC / CXX            (optional)  compiler drivers, default cc / c++
#   LLAMA_CMAKE_FLAGS   (optional)  extra -D... flags
#   BUILD_JOBS          (optional)  parallel jobs, default nproc
#   LLAMA_FORCE_BUILD   (optional)  'true' to rebuild even if binary exists
set -euo pipefail

SRC="${LLAMA_CPP_SRC_PATH:?LLAMA_CPP_SRC_PATH is required}"
BUILD_DIR="${LLAMA_BUILD_DIR:-$SRC/build}"
JOBS="${BUILD_JOBS:-$(nproc 2>/dev/null || echo 4)}"
CC_BIN="${CC:-cc}"
CXX_BIN="${CXX:-c++}"
EXTRA_FLAGS="${LLAMA_CMAKE_FLAGS:-}"
# LLAMA_CMAKE_FLAGS_ARR (newline-delimited) preserves multi-word -D values
# (e.g. -DCMAKE_C_FLAGS="-flto -mllvm -inline-threshold=2000"); preferred when set.
EXTRA_ARR=()
if [[ -n "${LLAMA_CMAKE_FLAGS_ARR:-}" ]]; then
  while IFS= read -r _line; do [[ -n "$_line" ]] && EXTRA_ARR+=("$_line"); done <<< "$LLAMA_CMAKE_FLAGS_ARR"
else
  read -r -a EXTRA_ARR <<< "$EXTRA_FLAGS"
fi
SERVER_BIN="$BUILD_DIR/bin/llama-server"

if [[ "${LLAMA_FORCE_BUILD:-false}" != "true" && -x "$SERVER_BIN" ]]; then
  echo "llama-server already built (use --force_build to rebuild): $SERVER_BIN"
  exit 0
fi

echo "== Building llama.cpp =="
echo "  src   : $SRC"
echo "  build : $BUILD_DIR"
echo "  CC    : $CC_BIN"
echo "  CXX   : $CXX_BIN"
echo "  jobs  : $JOBS"

# LLAMA_CURL=OFF: we serve a local GGUF, so no libcurl dependency is needed.
cmake -S "$SRC" -B "$BUILD_DIR" \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_C_COMPILER="$CC_BIN" \
  -DCMAKE_CXX_COMPILER="$CXX_BIN" \
  -DLLAMA_CURL=OFF \
  -DGGML_NATIVE=ON \
  $EXTRA_FLAGS

cmake --build "$BUILD_DIR" --config Release -j "$JOBS" --target llama-server llama-bench

test -x "$SERVER_BIN" || { echo "ERROR: build finished but $SERVER_BIN is missing"; exit 1; }
echo "Built: $SERVER_BIN"
[ -x "$BUILD_DIR/bin/llama-bench" ] && echo "Built: $BUILD_DIR/bin/llama-bench" || echo "NOTE: llama-bench not built (reproducible prefill will be skipped)"
