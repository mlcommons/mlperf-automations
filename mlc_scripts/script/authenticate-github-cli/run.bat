@echo off
echo Running gh auth:
REM Not printing MLC_RUN_CMD as it can contain secret
REM echo %MLC_RUN_CMD%
echo.

REM Check if MLC_FAKE_RUN is not equal to "yes"
if not "%MLC_FAKE_RUN%"=="yes" (
    
    REM Execute the command stored in MLC_RUN_CMD
    REM %MLC_RUN_CMD%
    echo %MLC_GH_AUTH_TOKEN% | gh auth login --with-token
    
    REM Check the exit code and exit with error if non-zero
    if %ERRORLEVEL% neq 0 (
        exit /b 1
    )
)

