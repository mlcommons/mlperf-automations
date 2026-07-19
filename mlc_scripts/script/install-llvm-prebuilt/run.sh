#!/bin/bash

echo ""
echo "Unarchiving ${MLC_LLVM_PACKAGE} ..."

tar --strip 1 -xf ${MLC_LLVM_PACKAGE}
test $? -eq 0 || exit 1

rm -f ${MLC_LLVM_PACKAGE}
test $? -eq 0 || exit 1
