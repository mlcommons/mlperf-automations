@echo off
setlocal enabledelayedexpansion

rem get-geekbench run script (Windows)
rem Download is handled by the download-and-extract prehook dependency.
rem This script runs the setup installer silently and exports the installed path.

if not "%MLC_GEEKBENCH_INSTALLED_PATH%" == "" (
  exit /b 0
)

if "%MLC_GEEKBENCH_DOWNLOAD_PATH%" == "" (
  echo MLC_GEEKBENCH_DOWNLOAD_PATH is not set
  exit /b 1
)

set SETUP_EXE=%MLC_GEEKBENCH_DOWNLOAD_PATH%

if not exist "%SETUP_EXE%" (
  echo Setup exe not found: %SETUP_EXE%
  exit /b 1
)

rem Install into the cache directory
set INSTALL_DIR=%cd%\Geekbench

echo.
echo Installing Geekbench from %SETUP_EXE% ...
echo Install directory: %INSTALL_DIR%
echo.

rem Run the NSIS installer silently with /S and /D for install dir
"%SETUP_EXE%" /S /D=%INSTALL_DIR%
set exitstatus=%ERRORLEVEL%

if %exitstatus% NEQ 0 (
  echo.
  echo Geekbench installer exited with status: %exitstatus%
  exit /b %exitstatus%
)

rem Verify installation and find geekbench exe
set "GEEKBENCH_BIN="
for %%f in ("%INSTALL_DIR%\geekbench6*.exe") do (
  if "!GEEKBENCH_BIN!" == "" (
    set "GEEKBENCH_BIN=%%f"
  )
)

if "!GEEKBENCH_BIN!" == "" (
  echo WARNING: Could not find geekbench exe in %INSTALL_DIR%
  echo Contents of install directory:
  dir "%INSTALL_DIR%"
  exit /b 1
)

echo Geekbench installed successfully: !GEEKBENCH_BIN!

rem Export env vars via tmp-run-env.out
echo MLC_GEEKBENCH_WINDOWS_INSTALL_DIR=%INSTALL_DIR%> tmp-run-env.out
echo MLC_GEEKBENCH_BIN_WITH_PATH=!GEEKBENCH_BIN!>> tmp-run-env.out
