#!/bin/bash

# Install GitHub CLI without sudo by downloading pre-built binary

INSTALL_DIR="${MLC_GH_INSTALL_DIR:-$(pwd)/install}"
mkdir -p "${INSTALL_DIR}"

# Detect architecture
ARCH=$(uname -m)
case "${ARCH}" in
    x86_64)  GH_ARCH="amd64" ;;
    aarch64) GH_ARCH="arm64" ;;
    armv7l)  GH_ARCH="armv6" ;;
    *)
        echo "Unsupported architecture: ${ARCH}"
        exit 1
        ;;
esac

OS=$(uname -s | tr '[:upper:]' '[:lower:]')

# Get latest version from GitHub API
GH_VERSION=$(curl -sL https://api.github.com/repos/cli/cli/releases/latest | grep '"tag_name"' | sed -E 's/.*"v([^"]+)".*/\1/')
if [ -z "${GH_VERSION}" ]; then
    echo "Failed to determine latest gh version"
    exit 1
fi

echo "Downloading gh CLI v${GH_VERSION} for ${OS}_${GH_ARCH}..."

TARBALL="gh_${GH_VERSION}_${OS}_${GH_ARCH}.tar.gz"
DOWNLOAD_URL="https://github.com/cli/cli/releases/download/v${GH_VERSION}/${TARBALL}"

curl -sL "${DOWNLOAD_URL}" -o "${INSTALL_DIR}/${TARBALL}"
test $? -eq 0 || exit 1

# Extract and place binary
tar -xzf "${INSTALL_DIR}/${TARBALL}" -C "${INSTALL_DIR}" --strip-components=1
test $? -eq 0 || exit 1

# Clean up tarball
rm -f "${INSTALL_DIR}/${TARBALL}"

# Verify
if [ -x "${INSTALL_DIR}/bin/gh" ]; then
    echo "gh CLI installed to ${INSTALL_DIR}/bin/gh"
else
    echo "Installation failed: gh binary not found"
    exit 1
fi
