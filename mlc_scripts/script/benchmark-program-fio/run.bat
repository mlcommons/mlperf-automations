@echo off
setlocal enabledelayedexpansion

rem Benchmark Program - FIO (Windows)

set RESULTS_DIR=%MLC_FIO_RESULTS_DIR%
set NUM_RUNS=%MLC_FIO_NUM_RUNS%

if "%RESULTS_DIR%" == "" set RESULTS_DIR=.
if "%NUM_RUNS%" == "" set NUM_RUNS=3

set TEST_FILE=%MLC_FIO_TEST_FILE%
if "%TEST_FILE%" == "" set TEST_FILE=%RESULTS_DIR%\fio_testfile

echo.
echo ***********************************************************************
echo Running FIO I/O benchmark
echo   Mode: %MLC_FIO_RW%
echo   Block size: %MLC_FIO_BS%
echo   Number of runs: %NUM_RUNS%
echo ***********************************************************************

for /L %%R in (1,1,%NUM_RUNS%) do (
  echo.
  echo === Run %%R/%NUM_RUNS% ===

  set "JSON_FILE=%RESULTS_DIR%\fio_run%%R.json"

  fio --name=mlc_benchmark --rw=%MLC_FIO_RW% --bs=%MLC_FIO_BS% --size=%MLC_FIO_SIZE% --numjobs=%MLC_FIO_NUMJOBS% --iodepth=%MLC_FIO_IODEPTH% --runtime=%MLC_FIO_RUNTIME% --time_based --direct=%MLC_FIO_DIRECT% --group_reporting --output-format=json --output="!JSON_FILE!" --filename="!TEST_FILE!" %MLC_FIO_EXTRA_ARGS%
  set exitstatus=!ERRORLEVEL!

  if !exitstatus! NEQ 0 (
    echo FIO exited with status: !exitstatus! ^(run %%R^)
    exit /b !exitstatus!
  )

  echo Results saved: !JSON_FILE!
)

del /f /q "%TEST_FILE%" 2>nul

echo.
echo ***********************************************************************
echo All %NUM_RUNS% FIO run^(s^) completed successfully.
echo ***********************************************************************

exit /b 0
