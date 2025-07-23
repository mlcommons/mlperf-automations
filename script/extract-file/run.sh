#!/bin/bash

if [ -e "${MLC_EXTRACT_EXTRACTED_FILENAME}" ] ; then
  CMD=${MLC_EXTRACT_EXTRACTED_CHECKSUM_CMD}
  echo ""
  echo "${CMD}"
  eval "${CMD}"
  test $? -eq 0 && exit 0
fi

CMD=${MLC_EXTRACT_CMD}
echo ""
echo "${CMD}"
eval "${CMD}"
test $? -eq 0 || exit $?
  
CMD=${MLC_EXTRACT_EXTRACTED_CHECKSUM_CMD}
echo ""
echo "${CMD}"
eval "${CMD}"
test $? -eq 0 || exit $?
