#!/bin/bash

set -e

OUT_DIR="${MLC_MULTI_NODE_INFRAGRAPH_DIR_PATH}"
MERGED_YAML="${OUT_DIR}/dev-multi-node.yaml"

# One translate per node. preprocess() has already placed topo-node-<id>.xml
# in OUT_DIR for every id in MLC_MULTI_NODE_INFRAGRAPH_NODE_IDS.
IFS=',' read -ra NODE_IDS <<< "${MLC_MULTI_NODE_INFRAGRAPH_NODE_IDS}"  # convert string to an array.
for node_id in "${NODE_IDS[@]}"; do
    infragraph translate lstopo \
        --input "${OUT_DIR}/topo-node-${node_id}.xml" \
        --output "${OUT_DIR}/dev-node-${node_id}.yaml"
    echo "dev-node-${node_id}.yaml written to ${OUT_DIR}/dev-node-${node_id}.yaml"
done

"${MLC_PYTHON_BIN_WITH_PATH}" "${MLC_TMP_CURRENT_SCRIPT_PATH}/merge_infragraph.py" \
    --dir "${OUT_DIR}" \
    --node-ids "${MLC_MULTI_NODE_INFRAGRAPH_NODE_IDS}" \
    --output "${MLC_MULTI_NODE_INFRAGRAPH_FILE_PATH}" \
    --merged-yaml "${MERGED_YAML}" \
    --name "${MLC_MULTI_NODE_INFRAGRAPH_NAME}"

echo "MLC_MULTI_NODE_INFRAGRAPH_DEV_YAML_PATH=${MERGED_YAML}" > tmp-run-env.out

if [[ "${MLC_MULTI_NODE_INFRAGRAPH_SKIP_VISUALIZE}" != "True" ]]; then
    echo "Generating visualizer files"
    infragraph visualize \
        --input "${MLC_MULTI_NODE_INFRAGRAPH_FILE_PATH}" \
        --output "${OUT_DIR}/visuals/"
fi
