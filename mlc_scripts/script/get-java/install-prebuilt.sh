#!/bin/bash

rm -f ${MLC_JAVA_PREBUILT_FILENAME}.tar.gz
rm -f ${MLC_JAVA_PREBUILT_FILENAME}.tar

wget --no-check-certificate ${MLC_JAVA_PREBUILT_URL}${MLC_JAVA_PREBUILT_FILENAME}.tar.gz
test $? -eq 0 || exit 1

gzip -d ${MLC_JAVA_PREBUILT_FILENAME}.tar.gz
test $? -eq 0 || exit 1

tar xvf ${MLC_JAVA_PREBUILT_FILENAME}.tar
test $? -eq 0 || exit 1

rm -f ${MLC_JAVA_PREBUILT_FILENAME}.tar
