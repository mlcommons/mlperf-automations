rem Download file

rem If MD5 is wrong, download again!

rem Next line allows ERRORLEVEL inside if statements!
setlocal enabledelayedexpansion

if NOT "%MLC_DOWNLOAD_CONFIG_CMD%" == "" (
  echo.
  echo %MLC_DOWNLOAD_CONFIG_CMD%
  echo.
  %MLC_DOWNLOAD_CONFIG_CMD%
  IF !ERRORLEVEL! NEQ 0 EXIT !ERRORLEVEL!
)

set require_download=1

if not "%MLC_DOWNLOAD_LOCAL_FILE_PATH%" == "" (
  set require_download=0
)

if "%MLC_DOWNLOAD_TOOL%" == "mlcutil" (
  set require_download=0
)


if exist "%MLC_DOWNLOAD_DOWNLOADED_PATH%" (
    if "%MLC_DOWNLOAD_CHECKSUM_CMD_USED%" == "YES" (
        echo.
        echo %MLC_DOWNLOAD_CHECKSUM_CMD%
        cmd /c %MLC_DOWNLOAD_CHECKSUM_CMD%
        IF !ERRORLEVEL! NEQ 0 (
           if NOT "%MLC_DOWNLOAD_LOCAL_FILE_PATH%" == "" exit 1
           if "%MLC_DOWNLOAD_CMD_USED%" == "NO" exit 1
        ) else (
           set require_download=0
        )
    )
)

if "!require_download!" == "1" (
    echo.
    cmd /c %MLC_PRE_DOWNLOAD_CLEAN_CMD%
 
    echo.
    echo %MLC_DOWNLOAD_CMD%
    cmd /c %MLC_DOWNLOAD_CMD%
    IF !ERRORLEVEL! NEQ 0 EXIT !ERRORLEVEL!

    if "%MLC_DOWNLOAD_CHECKSUM_CMD_USED%" == "YES" (
      echo.
      echo %MLC_DOWNLOAD_CHECKSUM_CMD%
      cmd /c %MLC_DOWNLOAD_CHECKSUM_CMD%
      IF !ERRORLEVEL! NEQ 0 EXIT 1
    )
)
