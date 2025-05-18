@echo off
setlocal enabledelayedexpansion

REM Save the current directory
set "CUR_DIR=%CD%"
set "SCRIPT_DIR=%MLC_TMP_CURRENT_SCRIPT_PATH%"

REM Change to the specified path
set "path=%MLC_GIT_CHECKOUT_PATH%"
echo cd "%path%"

cd /d "%path%"
if errorlevel 1 (
    echo Failed to change directory to %path%
    exit /b %errorlevel%
)

REM Execute the Git pull command
echo %MLC_GIT_PULL_CMD%
call %MLC_GIT_PULL_CMD%
REM Don't fail if there are local changes
REM if errorlevel 1 exit /b %errorlevel%

REM Return to the original directory
cd /d "%CUR_DIR%"
endlocal
