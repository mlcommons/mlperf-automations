@echo off

set GEEKBENCH_BIN=%MLC_GEEKBENCH_BIN_WITH_PATH%

if not exist "%GEEKBENCH_BIN%" (
  echo ERROR: Geekbench binary not found at %GEEKBENCH_BIN%
  exit /b 1
)

echo Geekbench binary found at: %GEEKBENCH_BIN%

rem Detect version
"%GEEKBENCH_BIN%" --version > tmp-ver.out 2>&1
IF %ERRORLEVEL% NEQ 0 EXIT %ERRORLEVEL%
