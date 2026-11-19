#!/bin/bash

CUR_DIR=$PWD

echo "******************************************************"

echo ${MLC_GCC_SRC_REPO_PATH}

# Clean source if requested (stale src/ from cancelled builds can break configure)
if [ "${MLC_CLEAN_BUILD}" = "yes" ] && [ -d "src" ]; then
  echo "[install-gcc-src] Clean build: removing stale src/"
  rm -rf src
fi

if [ ! -d "src" ]; then
  # Keep timestamps so generated files (e.g. gmp.info) are not rebuilt, which needs makeinfo.
  cp -r --preserve=timestamps ${MLC_GCC_SRC_REPO_PATH} src
  test $? -eq 0 || exit $?
fi

# libstdc++ target default: typeinfo names are unique, so compare type_info by address
# (applies to libsupc++ and, via the installed bits/os_defines.h, to all user code).
if [ "${MLC_GCC_MERGED_TYPEINFO_NAMES}" = "yes" ]; then
  OS_DEFINES=src/libstdc++-v3/config/os/gnu-linux/os_defines.h
  if ! grep -q "define __GXX_MERGED_TYPEINFO_NAMES" "${OS_DEFINES}"; then
    [ "$(tail -n1 "${OS_DEFINES}")" = "#endif" ] || { echo "Unexpected end of ${OS_DEFINES}"; exit 1; }
    sed -i '$i #define __GXX_MERGED_TYPEINFO_NAMES 1\n' "${OS_DEFINES}"
  fi
  echo "[install-gcc-src] ${OS_DEFINES}: $(grep "define __GXX_MERGED_TYPEINFO_NAMES" "${OS_DEFINES}")"
fi

INSTALL_DIR="${MLC_GCC_INSTALLED_PATH:-${CUR_DIR}/install}"
if [ -z "${MLC_GCC_INSTALL_PREFIX}" ]; then
  rm -rf install
fi
BUILD_DIR="${MLC_GCC_BUILD_DIR:-build}"
rm -rf "${BUILD_DIR}"

mkdir -p "${INSTALL_DIR}"
mkdir -p "${BUILD_DIR}"

echo "******************************************************"
cd src
export TAR_OPTIONS="--no-same-owner"
# Reused/copied trees can carry skewed timestamps that make autotools regenerate files:
# re-extract bundled prerequisites from their tarballs and re-touch GCC's generated files.
for pkg in gmp mpfr mpc isl gettext; do
  if [ -L "${pkg}" ] && ls "${pkg}"-[0-9]*.tar.* >/dev/null 2>&1; then
    rm -rf "${pkg}" "${pkg}"-[0-9]*/
  fi
done
./contrib/download_prerequisites
test $? -eq 0 || exit $?
./contrib/gcc_update --touch
cd "${CUR_DIR}/${BUILD_DIR}" 2>/dev/null || cd "${BUILD_DIR}" 


# Without makeinfo, stale .info files in the prerequisites (e.g. gmp) fail the build; docs are not needed.
MAKEINFO_ARG=""
if ! command -v makeinfo >/dev/null 2>&1; then
  export MAKEINFO=true
  MAKEINFO_ARG="MAKEINFO=true"
fi

cmd="${CUR_DIR}/src/configure --prefix="${INSTALL_DIR}" ${MLC_GCC_TARGET_STRING} ${MLC_GCC_HOST_STRING} ${MLC_GCC_BUILD_STRING} ${MLC_GCC_SYSROOT_STRING} ${MLC_GCC_EXTRA_CONFIGURE_STRING}  --with-gcc-major-version-only"
echo $cmd
eval $cmd

test $? -eq 0 || exit $?

echo "******************************************************"
MLC_MAKE_CORES=${MLC_MAKE_CORES:-${MLC_HOST_CPU_TOTAL_CORES}}
MLC_MAKE_CORES=${MLC_MAKE_CORES:-2}

make -j${MLC_MAKE_CORES} ${MAKEINFO_ARG}
test $? -eq 0 || exit $?

make install ${MAKEINFO_ARG}
test $? -eq 0 || exit $?

# Clean build directory (too large)
cd ${CUR_DIR}
rm -rf "${BUILD_DIR}" build

echo "******************************************************"
echo "GCC was built and installed to ${INSTALL_DIR} ..."
