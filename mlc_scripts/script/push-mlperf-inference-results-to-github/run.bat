@echo off

REM Check if MLC_GIT_REPO_CHECKOUT_PATH is set
if not defined MLC_GIT_REPO_CHECKOUT_PATH (
    echo "Error: MLC_GIT_REPO_CHECKOUT_PATH is not set."
    exit /b 1
)

cd /d "%MLC_GIT_REPO_CHECKOUT_PATH%"
if %errorlevel% neq 0 (
    echo "Error: Failed to change directory to %MLC_GIT_REPO_CHECKOUT_PATH%"
    exit /b 1
)

git pull
git add *

REM Check if the MLC_MLPERF_INFERENCE_SUBMISSION_DIR variable is set
if defined MLC_MLPERF_INFERENCE_SUBMISSION_DIR (
    robocopy "%MLC_MLPERF_INFERENCE_SUBMISSION_DIR%" "%MLC_GIT_REPO_CHECKOUT_PATH%" /E /COPYALL /DCOPY:DAT
    git add *
)

REM Check if the previous command was successful
if %errorlevel% neq 0 exit /b %errorlevel%

git commit -a -m "%MLC_MLPERF_RESULTS_REPO_COMMIT_MESSAGE%"

if defined MLC_MLPERF_INFERENCE_SUBMISSION_DIR call %MLC_SET_REMOTE_URL_CMD%

@if errorlevel 1 (
    timeout /t %random:~0,3% /nobreak > nul
    git pull --rebase
    %MLC_GIT_PUSH_CMD%
)


REM Check if the previous command was successful
if %errorlevel% neq 0 exit /b %errorlevel%
