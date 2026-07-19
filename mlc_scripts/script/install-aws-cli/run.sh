#!/bin/bash

CUR_DIR=$PWD
echo "******************************************************"
echo $MLC_CURL_URL
MLC_CURL_URL=${MLC_CURL_URL//"[OS]"/${MLC_HOST_OS_TYPE}}
MLC_CURL_URL=${MLC_CURL_URL//"[PLATFORM]"/${MLC_HOST_PLATFORM_FLAVOR}}
echo $MLC_CURL_URL
echo "MLC_CURL_URL=${MLC_CURL_URL}" >> tmp-run-env.out
FILE="awscliv2.zip"
rm -rf ${FILE}
curl "${MLC_CURL_URL}" -o "${FILE}"
unzip ${FILE}
sudo ./aws/install
