@echo off
setlocal enabledelayedexpansion

rem Benchmark Program - Phoronix Test Suite (Windows)

if "%MLC_PHORONIX_TEST%" == "" (
  echo MLC_PHORONIX_TEST is not set
  exit /b 1
)

set RESULTS_DIR=%MLC_PHORONIX_RESULTS_DIR%
if "%RESULTS_DIR%" == "" set RESULTS_DIR=.

set RESULT_ID=%MLC_PHORONIX_RESULT_IDENTIFIER%
if "%RESULT_ID%" == "" set RESULT_ID=mlc-benchmark

set TEST_RESULTS_NAME=%RESULT_ID%
set TEST_RESULTS_IDENTIFIER=%RESULT_ID%
set TEST_RESULTS_DESCRIPTION=MLC automated benchmark run

if "%MLC_PHORONIX_BATCH_MODE%" == "yes" (
  set PRESET_OPTIONS=TRUE
  set BATCH_FLAGS=--batch-run
) else (
  set BATCH_FLAGS=
)

if not "%MLC_PHORONIX_NUM_RUNS%" == "" (
  set FORCE_TIMES_TO_RUN=%MLC_PHORONIX_NUM_RUNS%
)

echo.
echo ***********************************************************************
echo Running Phoronix Test Suite
echo   Test: %MLC_PHORONIX_TEST%
echo   Runs: %MLC_PHORONIX_NUM_RUNS%
echo ***********************************************************************

phoronix-test-suite install "%MLC_PHORONIX_TEST%"

set "OUTPUT_FILE=%RESULTS_DIR%\phoronix_output.txt"
phoronix-test-suite %BATCH_FLAGS% benchmark %MLC_PHORONIX_EXTRA_ARGS% "%MLC_PHORONIX_TEST%" > "!OUTPUT_FILE!" 2>&1
set exitstatus=!ERRORLEVEL!

if !exitstatus! NEQ 0 (
  echo Phoronix Test Suite exited with status: !exitstatus!
  exit /b !exitstatus!
)

phoronix-test-suite result-file-to-json "%RESULT_ID%" > "%RESULTS_DIR%\phoronix_results.json" 2>nul

echo.
echo ***********************************************************************
echo Phoronix Test Suite completed successfully.
echo ***********************************************************************

exit /b 0
