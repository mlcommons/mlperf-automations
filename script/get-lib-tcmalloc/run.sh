#!/bin/bash

set -e

#Add your run commands here...
# run "$MLC_RUN_CMD"
CUR=$PWD

cd ${MLC_TCMALLOC_SRC_PATH}

# Check if "libtcmalloc.so" exists in the BUILD file
if ! grep -q "libtcmalloc.so" tcmalloc/BUILD; then
    echo '
cc_binary(
    name = "libtcmalloc.so",
    deps = [":tcmalloc"],
    linkshared = 1,
)' >> tcmalloc/BUILD
    echo "Added libtcmalloc.so target to tcmalloc/BUILD"
else
    echo "libtcmalloc.so target already exists in tcmalloc/BUILD, skipping..."
fi

# Build with optimizations for your specific architecture
# Define the compilation mode
COMP_MODE="opt"

# Build with opt
bazel build -c $COMP_MODE --copt=-march=native //tcmalloc:libtcmalloc.so

# Get the path for THAT SPECIFIC mode
BIN_DIR=$(bazel info -c $COMP_MODE bazel-bin)

cd $CUR
echo "Correct path: $BIN_DIR"
echo "MLC_TCMALLOC_BAZEL_BIN_DIR=$BIN_DIR" > tmp-run-env.out
