@echo off

if "%MLC_RUN_DIR%" == "" (
  echo MLC_RUN_DIR is not set
  exit 1
)

cd "%MLC_RUN_DIR%"

if "%MLC_DEBUG_SCRIPT_BENCHMARK_PROGRAM%" == "True" (
  echo *****************************************************
  echo You are now in Debug shell with pre-set CM env and can run the following command line manually:

  echo.
  if not "%MLC_RUN_CMD0%" == "" (
    echo %MLC_RUN_CMD0%
  ) else (
    echo %MLC_RUN_CMD%
  )

  echo.
  echo Type exit to return to CM script.
  echo.

  cmd

  exit 0
)

rem Check MLC_RUN_CMD0
if not "%MLC_RUN_CMD0%" == "" (
  echo.
  %MLC_RUN_CMD0%
) else (
  echo.
  %MLC_RUN_CMD%
)

IF %ERRORLEVEL% NEQ 0 EXIT %ERRORLEVEL%
