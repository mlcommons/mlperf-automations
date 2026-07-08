#!/bin/bash

set -e
lstopo topo.xml
echo "MLC_LSTOPO_XML_FILE_PATH=$(pwd)/topo.xml" > tmp-run-env.out
echo "topo.xml written to $(pwd)/topo.xml"
