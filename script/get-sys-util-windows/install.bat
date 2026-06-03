@echo off

REM Install Chocolatey if not present
where choco >nul 2>nul
IF %ERRORLEVEL% NEQ 0 (
  echo Chocolatey not found. Installing...
  powershell -NoProfile -ExecutionPolicy Bypass -Command "iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
  IF %ERRORLEVEL% NEQ 0 EXIT %ERRORLEVEL%
  SET "PATH=%PATH%;%ALLUSERSPROFILE%\chocolatey\bin"
)

choco install %MLC_SYS_UTIL_CHOCO_PACKAGE% -y
IF %ERRORLEVEL% NEQ 0 (
  IF "%MLC_TMP_FAIL_SAFE%"=="yes" (
    echo MLC_GET_GENERIC_SYS_UTIL_INSTALL_FAILED=yes > tmp-run-env.out
    echo Fail-safe enabled, exiting with status 0
    EXIT 0
  )
  EXIT %ERRORLEVEL%
)
