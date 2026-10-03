#!/bin/bash

# get-phoronix-test-suite: resolve/install the Phoronix Test Suite.
#  - If customize.py already resolved an existing launcher -> nothing to do.
#  - Portable (no-sudo) install into MLC_PHORONIX_INSTALL_PREFIX when requested
#    (works on SLURM compute nodes: downloads the relocatable source tarball plus
#    a prefix-local php via apt-get download, no root required).
#  - Otherwise install the release .deb via apt (needs sudo).

# Keep only absolute POSIX PATH entries (some IDE terminals inject Windows paths).
_clean_path=""
_oldifs="$IFS"; IFS=':'
for _p in $PATH; do
  case "$_p" in /*) ;; *) continue ;; esac
  case "$_p" in *'\'*|*';'*) continue ;; esac
  _clean_path="${_clean_path:+$_clean_path:}$_p"
done
IFS="$_oldifs"
for _sys in /usr/local/sbin /usr/local/bin /usr/sbin /usr/bin /sbin /bin; do
  case ":$_clean_path:" in *":$_sys:"*) ;; *) _clean_path="${_clean_path:+$_clean_path:}$_sys" ;; esac
done
export PATH="$_clean_path"

PTS_VERSION="${MLC_PHORONIX_VERSION:-10.8.4}"

if [ "${MLC_PHORONIX_SKIP_INSTALL}" == "yes" ]; then
  echo "phoronix-test-suite already available; skipping install."
  exit 0
fi

# ---------------------------------------------------------------------------
# No-sudo portable install into a (shared) prefix.
# ---------------------------------------------------------------------------
if [ "${MLC_PHORONIX_DO_PORTABLE_INSTALL}" == "yes" ]; then
  PREFIX="${MLC_PHORONIX_INSTALL_PREFIX}"
  if [ -z "${PREFIX}" ]; then
    echo "ERROR: MLC_PHORONIX_INSTALL_PREFIX is required for the portable install"
    exit 1
  fi
  echo "Portable (no-sudo) install of Phoronix ${PTS_VERSION} into ${PREFIX}"
  rm -rf "${PREFIX}"; mkdir -p "${PREFIX}/php-root" "${PREFIX}/bin"
  B=$(mktemp -d); cd "${B}" || exit 1

  # Relocatable launcher from the GitHub source archive (honours $PHP_BIN,
  # resolves its core dir via readlink - unlike the .deb which hardcodes /usr/share).
  curl -fsSL --max-time 180 -o pts.tgz \
    "https://github.com/phoronix-test-suite/phoronix-test-suite/archive/refs/tags/v${PTS_VERSION}.tar.gz" || {
      echo "ERROR: failed to download phoronix source ${PTS_VERSION}"; exit 1; }
  tar xf pts.tgz
  src=$(find . -maxdepth 1 -type d -name 'phoronix-test-suite-*' | head -1)
  [ -n "${src}" ] || { echo "ERROR: phoronix source dir missing"; exit 1; }
  cp -a "${src}" "${PREFIX}/phoronix-test-suite"

  # Prefix-local php (+ XML/mbstring), no sudo. Download the concrete php
  # packages explicitly (apt-get download fetches even if already installed on the
  # build host) and add any still-missing shared libs via --print-uris.
  mkdir php && cd php
  PHPMM=$(apt-cache depends php-cli 2>/dev/null | grep -oE 'php[0-9]+\.[0-9]+-cli' | head -1 | sed 's/-cli//')
  [ -n "${PHPMM}" ] || PHPMM=php8.3
  PKGS="${PHPMM}-cli ${PHPMM}-common ${PHPMM}-opcache ${PHPMM}-readline ${PHPMM}-xml ${PHPMM}-mbstring"
  echo "php packages: ${PKGS}"
  apt-get download ${PKGS} 2>/dev/null || echo "WARN: some apt-get download failed"
  apt-get install --print-uris -y ${PKGS} 2>/dev/null \
    | grep -oE "https?://[^ ']+\.deb" | sort -u > uris.txt
  while read -r u; do curl -fsSL -O "$u" || echo "WARN: failed $u"; done < uris.txt
  echo "extracting $(ls *.deb 2>/dev/null | wc -l) php .deb(s)"
  for d in *.deb; do dpkg-deb -x "$d" "${PREFIX}/php-root"; done
  cd "${PREFIX}"

  PHPBIN=$(find php-root/usr/bin -maxdepth 1 -name 'php8*' -type f | head -1)
  EXTDIR=$(find php-root/usr/lib/php -maxdepth 1 -type d -name '20*' | head -1)
  if [ -z "${PHPBIN}" ] || [ -z "${EXTDIR}" ]; then
    echo "ERROR: prefix-local php not found after extraction"; exit 1
  fi

  EXT_FLAGS=""
  for e in dom simplexml xml xmlwriter xmlreader mbstring; do
    EXT_FLAGS="${EXT_FLAGS} -d extension=${e}"
  done
  cat > bin/php <<EOF
#!/bin/bash
R="\$(cd "\$(dirname "\$(readlink -f "\$0")")/.." && pwd)"
export LD_LIBRARY_PATH="\$R/php-root/usr/lib/x86_64-linux-gnu:\$R/php-root/lib/x86_64-linux-gnu:\${LD_LIBRARY_PATH:-}"
exec "\$R/${PHPBIN}" -n -d extension_dir="\$R/${EXTDIR}"${EXT_FLAGS} "\$@"
EOF
  chmod +x bin/php

  cat > bin/phoronix-test-suite <<EOF
#!/bin/bash
R="\$(cd "\$(dirname "\$(readlink -f "\$0")")/.." && pwd)"
export PHP_BIN="\$R/bin/php"
exec "\$R/phoronix-test-suite/phoronix-test-suite" "\$@"
EOF
  chmod +x bin/phoronix-test-suite

  "${PREFIX}/bin/phoronix-test-suite" version >/dev/null 2>&1 \
    && echo "Portable install OK: ${PREFIX}/bin/phoronix-test-suite" \
    || { echo "ERROR: portable phoronix launcher failed to run"; exit 1; }
  exit 0
fi

# ---------------------------------------------------------------------------
# System .deb install via apt (needs sudo).
# ---------------------------------------------------------------------------
if command -v phoronix-test-suite &> /dev/null; then
  echo "phoronix-test-suite already on PATH; skipping install."
  exit 0
fi
if [ -z "${MLC_PHORONIX_DEB_PATH}" ] || [ ! -f "${MLC_PHORONIX_DEB_PATH}" ]; then
  echo "ERROR: phoronix-test-suite .deb not found (MLC_PHORONIX_DEB_PATH=${MLC_PHORONIX_DEB_PATH})"
  exit 1
fi
echo "Installing phoronix-test-suite from: ${MLC_PHORONIX_DEB_PATH}"
${MLC_SUDO} DEBIAN_FRONTEND=noninteractive apt-get install -y "${MLC_PHORONIX_DEB_PATH}"
rc=$?
if [ ${rc} -ne 0 ] || ! command -v phoronix-test-suite &> /dev/null; then
  echo "ERROR: Failed to install phoronix-test-suite (status ${rc})"
  exit 1
fi
exit 0
