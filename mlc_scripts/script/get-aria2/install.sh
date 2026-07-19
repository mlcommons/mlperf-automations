#!/bin/bash

echo ""

if [[ "${MLC_ARIA2_BUILD_FROM_SRC}" == "True" ]]; then

  echo "Building from sources ..."
  echo ""

  rm -rf ${MLC_ARIA2_DOWNLOAD_FILE}
  rm -rf ${MLC_ARIA2_DOWNLOAD_FILE2}

  wget --no-check-certificate ${MLC_ARIA2_DOWNLOAD_URL}
  test $? -eq 0 || exit $?

  bzip2 -d ${MLC_ARIA2_DOWNLOAD_FILE}
  test $? -eq 0 || exit $?

  tar xvf ${MLC_ARIA2_DOWNLOAD_FILE2}
  test $? -eq 0 || exit $?

  cd ${MLC_ARIA2_DOWNLOAD_DIR}
  test $? -eq 0 || exit $?

  ./configure --prefix=$PWD/bin
  test $? -eq 0 || exit $?

  make
  test $? -eq 0 || exit $?

  make install
  test $? -eq 0 || exit $?

else
  echo "Installing binary via sudo ..."
  echo ""

  cmd="sudo ${MLC_HOST_OS_PACKAGE_MANAGER} install aria2"
  echo "$cmd"

  $cmd
  test $? -eq 0 || exit $?

  path_to_bin=`which aria2c`
  echo "MLC_ARIA2_BIN_WITH_PATH=$path_to_bin" > tmp-run-env.out

fi
