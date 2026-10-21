@echo off
if not "%MLC_RUN_CMD%"=="" (
  echo %MLC_RUN_CMD%
  call %MLC_RUN_CMD%
  if errorlevel 1 exit /b %errorlevel%
)
