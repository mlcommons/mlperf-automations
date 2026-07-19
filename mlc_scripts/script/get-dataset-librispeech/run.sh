#!/bin/bash

wget -nc ${MLC_WGET_URL} --no-check-certificate
test $? -eq 0 || exit 1

tar -x --skip-old-files -vf ${MLC_DATASET_ARCHIVE}
test $? -eq 0 || exit 1

