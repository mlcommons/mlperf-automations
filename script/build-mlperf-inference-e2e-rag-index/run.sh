#!/bin/bash

set -e

CACHE_DIR="$PWD"
E2E_DIR="${MLC_MLPERF_INFERENCE_E2E_SOURCE}/e2e"

CHUNK_LEN="${MLC_E2E_INGEST_CHUNK_LEN:-768}"
CHUNK_OVERLAP="${MLC_E2E_INGEST_CHUNK_OVERLAP:-32}"
DB_NAME="vector_html_hnsw_len${CHUNK_LEN}_ov${CHUNK_OVERLAP}_word"

# Check if already built (handles re-runs if cache wasn't invalidated)
if [ -f "${CACHE_DIR}/${DB_NAME}.db" ]; then
    echo "Vector database already exists at ${CACHE_DIR}/${DB_NAME}.db — skipping ingestion."
    exit 0
fi

# Resolve the HTML documents directory
# MLC_DATASET_FRAMES_DOCS_DIR can override the default location
if [ -n "${MLC_DATASET_FRAMES_DOCS_DIR}" ]; then
    DOC_DIR="${MLC_DATASET_FRAMES_DOCS_DIR}"
elif [ -d "${MLC_DATASET_FRAMES_PATH}/doc_html" ]; then
    DOC_DIR="${MLC_DATASET_FRAMES_PATH}/doc_html"
elif [ -d "${MLC_DATASET_FRAMES_PATH}" ]; then
    # Fallback: dataset path itself might be the doc_html directory
    DOC_DIR="${MLC_DATASET_FRAMES_PATH}"
else
    echo "ERROR: Cannot find HTML documents directory."
    echo "  Set MLC_DATASET_FRAMES_DOCS_DIR to the path of the HTML documents directory,"
    echo "  or ensure MLC_DATASET_FRAMES_PATH points to the FRAMES benchmark dataset root."
    exit 1
fi

echo "=== E2E RAG Vector Database Ingestion ==="
echo "  E2E source directory: ${E2E_DIR}"
echo "  HTML documents:       ${DOC_DIR}"
echo "  Retriever model:      ${MLC_ML_MODEL_E5_BASE_V2_PATH}"
echo "  Device:               ${MLC_E2E_INGEST_DEVICE:-cpu}"
echo "  Embedding devices:    ${MLC_E2E_INGEST_NUM_DEVICES:-1}"
echo "  Chunk size:           ${CHUNK_LEN}"
echo "  Chunk overlap:        ${CHUNK_OVERLAP}"
echo "  Output directory:     ${CACHE_DIR}"
echo ""

export INGESTION_RETRIEVER_MODEL="${MLC_ML_MODEL_E5_BASE_V2_PATH}"
export INGESTION_DEVICE="${MLC_E2E_INGEST_DEVICE:-cpu}"
export INGESTION_EMBEDDING_DEVICE="${MLC_E2E_INGEST_DEVICE:-cpu}"
export INGESTION_NUM_EMBEDDING_DEVICES="${MLC_E2E_INGEST_NUM_DEVICES:-1}"
export INGESTION_CHUNK_LEN="${CHUNK_LEN}"
export INGESTION_CHUNK_OVERLAP="${CHUNK_OVERLAP}"
export INGESTION_DOC_DIR="${DOC_DIR}"
export INGESTION_PASSAGES_JSON="${CACHE_DIR}/passages/doc_html_len${CHUNK_LEN}_ov${CHUNK_OVERLAP}_word.json"
export INGESTION_DB="${CACHE_DIR}/${DB_NAME}"

mkdir -p "${CACHE_DIR}/passages"

cd "${E2E_DIR}"
bash scripts/run_ingestion.sh
test $? -eq 0 || exit $?

echo ""
echo "=== Ingestion complete ==="
echo "  Database: ${CACHE_DIR}/${DB_NAME}.db"
