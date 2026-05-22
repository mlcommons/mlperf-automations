@echo off
setlocal enabledelayedexpansion

rem Benchmark Program - CoreMark (Windows)

if "%MLC_RUN_DIR%" == "" (
  echo MLC_RUN_DIR is not set
  exit /b 1
)

cd /d "%MLC_RUN_DIR%"

set RESULTS_DIR=%MLC_COREMARK_RESULTS_DIR%
set NUM_RUNS=%MLC_COREMARK_NUM_RUNS%

if "%RESULTS_DIR%" == "" set RESULTS_DIR=.
if "%NUM_RUNS%" == "" set NUM_RUNS=3

set COREMARK_DIR=%MLC_RUN_DIR%\coremark

if not exist "%COREMARK_DIR%" (
  echo Cloning CoreMark repository...
  git clone https://github.com/eembc/coremark.git "%COREMARK_DIR%"
  if !ERRORLEVEL! NEQ 0 (
    echo ERROR: Failed to clone CoreMark
    exit /b 1
  )
)

cd /d "%COREMARK_DIR%"

echo.
echo ***********************************************************************
echo Running CoreMark CPU benchmark
echo   Threads: %MLC_COREMARK_NUM_THREADS%
echo   Number of runs: %NUM_RUNS%
echo ***********************************************************************

for /L %%R in (1,1,%NUM_RUNS%) do (
  echo.
  echo === Run %%R/%NUM_RUNS% ===

  set "OUTPUT_FILE=%RESULTS_DIR%\coremark_run%%R.txt"

  coremark.exe > "!OUTPUT_FILE!" 2>&1
  set exitstatus=!ERRORLEVEL!

  if !exitstatus! NEQ 0 (
    echo CoreMark exited with status: !exitstatus! ^(run %%R^)
    exit /b !exitstatus!
  )

  echo Results saved: !OUTPUT_FILE!
)

echo.
echo ***********************************************************************
echo All %NUM_RUNS% CoreMark run^(s^) completed successfully.
echo ***********************************************************************

exit /b 0
