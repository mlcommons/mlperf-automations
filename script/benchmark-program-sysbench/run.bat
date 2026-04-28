@echo off
setlocal enabledelayedexpansion

rem Benchmark Program - Sysbench (Windows)

set RESULTS_DIR=%MLC_SYSBENCH_RESULTS_DIR%
set NUM_RUNS=%MLC_SYSBENCH_NUM_RUNS%
set TEST=%MLC_SYSBENCH_TEST%

if "%RESULTS_DIR%" == "" set RESULTS_DIR=.
if "%NUM_RUNS%" == "" set NUM_RUNS=3
if "%TEST%" == "" set TEST=cpu

echo.
echo ***********************************************************************
echo Running Sysbench benchmark
echo   Test: %TEST%
echo   Threads: %MLC_SYSBENCH_NUM_THREADS%
echo   Number of runs: %NUM_RUNS%
echo ***********************************************************************

set BASE_ARGS=--threads=%MLC_SYSBENCH_NUM_THREADS% --time=%MLC_SYSBENCH_TIME%

if "%TEST%" == "cpu" (
  set TEST_ARGS=cpu --cpu-max-prime=%MLC_SYSBENCH_CPU_MAX_PRIME%
) else if "%TEST%" == "memory" (
  set TEST_ARGS=memory --memory-block-size=%MLC_SYSBENCH_MEMORY_BLOCK_SIZE% --memory-total-size=%MLC_SYSBENCH_MEMORY_TOTAL_SIZE%
) else (
  set TEST_ARGS=%TEST%
)

for /L %%R in (1,1,%NUM_RUNS%) do (
  echo.
  echo === Run %%R/%NUM_RUNS% ===

  set "OUTPUT_FILE=%RESULTS_DIR%\sysbench_run%%R.txt"

  sysbench !TEST_ARGS! %BASE_ARGS% %MLC_SYSBENCH_EXTRA_ARGS% run > "!OUTPUT_FILE!" 2>&1
  set exitstatus=!ERRORLEVEL!

  if !exitstatus! NEQ 0 (
    echo Sysbench exited with status: !exitstatus! ^(run %%R^)
    exit /b !exitstatus!
  )

  echo Results saved: !OUTPUT_FILE!
)

echo.
echo ***********************************************************************
echo All %NUM_RUNS% Sysbench run^(s^) completed successfully.
echo ***********************************************************************

exit /b 0
