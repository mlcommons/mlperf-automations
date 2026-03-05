@echo off
setlocal enabledelayedexpansion

rem Benchmark Program - Geekbench (Windows)

if "%MLC_RUN_DIR%" == "" (
  echo MLC_RUN_DIR is not set
  exit /b 1
)

cd /d "%MLC_RUN_DIR%"

echo.
echo ***********************************************************************
echo Running Geekbench benchmark...
echo Command: %MLC_RUN_CMD%
echo ***********************************************************************
echo.

%MLC_RUN_CMD%
set exitstatus=%ERRORLEVEL%

if %exitstatus% NEQ 0 (
  echo.
  echo Geekbench exited with status: %exitstatus%
  exit /b %exitstatus%
)

rem Check if results file was created
if exist "%MLC_GEEKBENCH_RESULTS_FILE%" (
  echo.
  echo Geekbench results saved to: %MLC_GEEKBENCH_RESULTS_FILE%
  echo.
  echo Results summary:
  type "%MLC_GEEKBENCH_RESULTS_FILE%"
  echo.
) else (
  echo.
  echo WARNING: Geekbench results file not found at %MLC_GEEKBENCH_RESULTS_FILE%
)

exit /b 0
