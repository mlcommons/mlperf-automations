@echo off
setlocal enabledelayedexpansion

rem Benchmark Program - STREAM (Windows)

if "%MLC_RUN_DIR%" == "" (
  echo MLC_RUN_DIR is not set
  exit /b 1
)

cd /d "%MLC_RUN_DIR%"

set RESULTS_DIR=%MLC_STREAM_RESULTS_DIR%
set NUM_RUNS=%MLC_STREAM_NUM_RUNS%

if "%RESULTS_DIR%" == "" set RESULTS_DIR=.
if "%NUM_RUNS%" == "" set NUM_RUNS=3

echo.
echo ***********************************************************************
echo Running STREAM memory bandwidth benchmark
echo   Array size: %MLC_STREAM_ARRAY_SIZE%
echo   NTIMES: %MLC_STREAM_NTIMES%
echo   Number of runs: %NUM_RUNS%
echo ***********************************************************************

for /L %%R in (1,1,%NUM_RUNS%) do (
  echo.
  echo === Run %%R/%NUM_RUNS% ===

  set "OUTPUT_FILE=%RESULTS_DIR%\stream_run%%R.txt"

  if not "%MLC_STREAM_NUM_THREADS%" == "" if not "%MLC_STREAM_NUM_THREADS%" == "0" (
    set OMP_NUM_THREADS=%MLC_STREAM_NUM_THREADS%
  )

  "%MLC_RUN_DIR%\stream.exe" > "!OUTPUT_FILE!"
  set exitstatus=!ERRORLEVEL!

  if !exitstatus! NEQ 0 (
    echo STREAM exited with status: !exitstatus! ^(run %%R^)
    exit /b !exitstatus!
  )

  echo Results saved: !OUTPUT_FILE!
)

echo.
echo ***********************************************************************
echo All %NUM_RUNS% STREAM run^(s^) completed successfully.
echo ***********************************************************************

exit /b 0
