@echo off
setlocal enabledelayedexpansion

rem Benchmark Program - stress-ng (Windows)

set RESULTS_DIR=%MLC_STRESSNG_RESULTS_DIR%
set NUM_RUNS=%MLC_STRESSNG_NUM_RUNS%
set STRESSOR=%MLC_STRESSNG_STRESSOR%
set WORKERS=%MLC_STRESSNG_WORKERS%
set TIMEOUT=%MLC_STRESSNG_TIMEOUT%

if "%RESULTS_DIR%" == "" set RESULTS_DIR=.
if "%NUM_RUNS%" == "" set NUM_RUNS=3
if "%STRESSOR%" == "" set STRESSOR=cpu
if "%WORKERS%" == "" set WORKERS=0
if "%TIMEOUT%" == "" set TIMEOUT=60

echo.
echo ***********************************************************************
echo Running stress-ng benchmark
echo   Stressor: %STRESSOR%
echo   Workers: %WORKERS%
echo   Timeout: %TIMEOUT%s
echo   Number of runs: %NUM_RUNS%
echo ***********************************************************************

for /L %%R in (1,1,%NUM_RUNS%) do (
  echo.
  echo === Run %%R/%NUM_RUNS% ===

  set "OUTPUT_FILE=%RESULTS_DIR%\stressng_run%%R.txt"

  stress-ng --%STRESSOR% %WORKERS% --timeout %TIMEOUT%s --metrics-brief %MLC_STRESSNG_EXTRA_ARGS% > "!OUTPUT_FILE!" 2>&1
  set exitstatus=!ERRORLEVEL!

  if !exitstatus! NEQ 0 (
    echo stress-ng exited with status: !exitstatus! ^(run %%R^)
    exit /b !exitstatus!
  )

  echo Results saved: !OUTPUT_FILE!
)

echo.
echo ***********************************************************************
echo All %NUM_RUNS% stress-ng run^(s^) completed successfully.
echo ***********************************************************************

exit /b 0
