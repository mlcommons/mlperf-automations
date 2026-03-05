@echo off
setlocal enabledelayedexpansion

rem Benchmark Program - Geekbench (Windows)

if "%MLC_RUN_DIR%" == "" (
  echo MLC_RUN_DIR is not set
  exit /b 1
)

cd /d "%MLC_RUN_DIR%"

rem Register license if key is provided
if not "!MLC_GEEKBENCH_LICENSE_KEY!" == "" (
  echo.
  echo Registering Geekbench license...
  "!MLC_GEEKBENCH_BIN_WITH_PATH!" --unlock !MLC_GEEKBENCH_LICENSE_EMAIL! !MLC_GEEKBENCH_LICENSE_KEY!
  if !ERRORLEVEL! NEQ 0 (
    echo WARNING: Geekbench license registration failed, continuing anyway
  ) else (
    echo Geekbench license registered successfully.
  )
)

echo.
echo ***********************************************************************
echo Running Geekbench benchmark...
echo Command: !MLC_RUN_CMD!
echo ***********************************************************************
echo.

!MLC_RUN_CMD!
set exitstatus=!ERRORLEVEL!

if !exitstatus! NEQ 0 (
  echo.
  echo Geekbench exited with status: !exitstatus!
  exit /b !exitstatus!
)

rem Check if results file was created
if exist "!MLC_GEEKBENCH_RESULTS_FILE!" (
  echo.
  echo Geekbench results saved to: !MLC_GEEKBENCH_RESULTS_FILE!
  echo.
  echo Results summary:
  type "!MLC_GEEKBENCH_RESULTS_FILE!"
  echo.
) else (
  echo.
  echo WARNING: Geekbench results file not found at !MLC_GEEKBENCH_RESULTS_FILE!
)
