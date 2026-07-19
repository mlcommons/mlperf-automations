@echo off
setlocal enabledelayedexpansion

rem Benchmark Program - pyperformance (Windows)

set RESULTS_DIR=%MLC_PYPERFORMANCE_RESULTS_DIR%
set NUM_RUNS=%MLC_PYPERFORMANCE_NUM_RUNS%

if "%RESULTS_DIR%" == "" set RESULTS_DIR=.
if "%NUM_RUNS%" == "" set NUM_RUNS=1

set PYTHON=%MLC_PYPERFORMANCE_PYTHON%
if "%PYTHON%" == "" set PYTHON=python

rem Install pyperformance if not available
%PYTHON% -m pyperformance --help > nul 2>&1
if !ERRORLEVEL! NEQ 0 (
  echo Installing pyperformance...
  %PYTHON% -m pip install pyperformance
)

set SPEED_ARGS=
if "%MLC_PYPERFORMANCE_FAST%" == "yes" set SPEED_ARGS=--fast
if "%MLC_PYPERFORMANCE_RIGOROUS%" == "yes" set SPEED_ARGS=--rigorous

echo.
echo ***********************************************************************
echo Running pyperformance benchmark suite
echo   Python: %PYTHON%
echo   Number of runs: %NUM_RUNS%
echo ***********************************************************************

for /L %%R in (1,1,%NUM_RUNS%) do (
  echo.
  echo === Run %%R/%NUM_RUNS% ===

  set "JSON_FILE=%RESULTS_DIR%\pyperformance_run%%R.json"

  %PYTHON% -m pyperformance run --output "!JSON_FILE!" %SPEED_ARGS% %MLC_PYPERFORMANCE_EXTRA_ARGS% > "%RESULTS_DIR%\pyperformance_run%%R.txt" 2>&1
  set exitstatus=!ERRORLEVEL!

  if !exitstatus! NEQ 0 (
    echo pyperformance exited with status: !exitstatus! ^(run %%R^)
    exit /b !exitstatus!
  )

  if exist "!JSON_FILE!" (
    echo JSON results saved: !JSON_FILE!
  )
)

echo.
echo ***********************************************************************
echo All %NUM_RUNS% pyperformance run^(s^) completed successfully.
echo ***********************************************************************

exit /b 0
