#!/bin/bash

echo ""
echo "Unarchiving ${MLC_CMAKE_PACKAGE} ..."

tar --strip 1 -xf ${MLC_CMAKE_PACKAGE}
test $? -eq 0 || exit 1

rm -f ${MLC_CMAKE_PACKAGE}
test $? -eq 0 || exit 1
