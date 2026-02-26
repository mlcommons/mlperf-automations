#!/bin/bash

# Execute config command if it exists
if [[ -n ${MLC_DOWNLOAD_CONFIG_CMD} ]]; then
  echo -e "\nExecuting: ${MLC_DOWNLOAD_CONFIG_CMD}"
  eval "${MLC_DOWNLOAD_CONFIG_CMD}" || exit $?
fi

# Assume download is required by default
require_download=1

# No download needed if a local file path is specified or the tool is 'mlcutil'
if [[ -n "${MLC_DOWNLOAD_LOCAL_FILE_PATH}" || ${MLC_DOWNLOAD_TOOL} == "mlcutil" ]]; then
  require_download=0
fi

# If the file exists, check the checksum if necessary
if [[ -e "${MLC_DOWNLOAD_DOWNLOADED_PATH}" && -n "${MLC_DOWNLOAD_CHECKSUM_CMD}" ]]; then
  echo -e "\nChecking checksum: ${MLC_DOWNLOAD_CHECKSUM_CMD}"
  eval "${MLC_DOWNLOAD_CHECKSUM_CMD}"
  
  if [[ $? -ne 0 ]]; then
    # If the checksum fails, handle errors based on whether the file is local
    if [[ -n "${MLC_DOWNLOAD_LOCAL_FILE_PATH}" ]]; then
      echo "Checksum failed for local file. Exiting."
      exit 1
    else
      echo "Checksum failed. Marking for re-download."
      MLC_PRE_DOWNLOAD_CLEAN=true
    fi
  else
    # If checksum succeeds, no download is required
    require_download=0
  fi
fi

# Perform download if required
if [[ ${require_download} == 1 ]]; then
  echo ""

  # If a pre-download clean command is specified and needed, execute it
  if [[ -n "${MLC_PRE_DOWNLOAD_CLEAN}" && "${MLC_PRE_DOWNLOAD_CLEAN,,}" != "false" ]]; then
    echo "Executing pre-download clean: ${MLC_PRE_DOWNLOAD_CLEAN_CMD}"
    eval "${MLC_PRE_DOWNLOAD_CLEAN_CMD}" || exit $?
  fi

  # Execute the download command with retry logic
  retry_count=${MLC_DOWNLOAD_RETRY_COUNT:-1}
  attempt=1
  download_success=0
  
  while [[ $attempt -le $retry_count ]]; do
    if [[ $attempt -gt 1 ]]; then
      echo "Retry attempt $attempt of $retry_count"
    fi
    
    echo "Downloading: ${MLC_DOWNLOAD_CMD}"
    eval "${MLC_DOWNLOAD_CMD}"
    
    if [[ $? -eq 0 ]]; then
      download_success=1
      break
    else
      if [[ $attempt -lt $retry_count ]]; then
        echo "Download failed. Retrying..."
      fi
      ((attempt++))
    fi
  done
  
  if [[ $download_success -eq 0 ]]; then
    echo "Download failed after $retry_count attempt(s)."
    exit 1
  fi
fi

# Verify checksum again if necessary
if [[ "${MLC_DOWNLOAD_MODE}" != "dry" && ( "${MLC_DOWNLOAD_TOOL}" == "mlcutil" || ${require_download} == 1 ) ]]; then
  if [[ -n "${MLC_DOWNLOAD_CHECKSUM_CMD}" ]]; then
    echo -e "\nVerifying checksum after download: ${MLC_DOWNLOAD_CHECKSUM_CMD}"
    eval "${MLC_DOWNLOAD_CHECKSUM_CMD}" || exit $?
  fi
fi
