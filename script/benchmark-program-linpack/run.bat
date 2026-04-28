@echo off
setlocal enabledelayedexpansion

rem Benchmark Program - Linpack (Windows)

if "%MLC_RUN_DIR%" == "" (
  echo MLC_RUN_DIR is not set
  exit /b 1
)

cd /d "%MLC_RUN_DIR%"

set RESULTS_DIR=%MLC_LINPACK_RESULTS_DIR%
set NUM_RUNS=%MLC_LINPACK_NUM_RUNS%

if "%RESULTS_DIR%" == "" set RESULTS_DIR=.
if "%NUM_RUNS%" == "" set NUM_RUNS=3

echo.
echo ***********************************************************************
echo Running HPL/Linpack benchmark
echo   Problem size: %MLC_LINPACK_PROBLEM_SIZE%
echo   Number of runs: %NUM_RUNS%
echo ***********************************************************************

for /L %%R in (1,1,%NUM_RUNS%) do (
  echo.
  echo === Run %%R/%NUM_RUNS% ===

  set "OUTPUT_FILE=%RESULTS_DIR%\linpack_run%%R.txt"

  %MLC_LINPACK_RUN_CMD% > "!OUTPUT_FILE!" 2>&1
  set exitstatus=!ERRORLEVEL!

  if !exitstatus! NEQ 0 (
    echo Linpack exited with status: !exitstatus! ^(run %%R^)
    exit /b !exitstatus!
  )

  echo Results saved: !OUTPUT_FILE!
)

echo.
echo ***********************************************************************
echo All %NUM_RUNS% Linpack run^(s^) completed successfully.
echo ***********************************************************************

exit /b 0
