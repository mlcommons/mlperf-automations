@echo off
REM Check if the environment variable MLC_HF_LOGIN_CMD is defined and not empty
IF DEFINED MLC_HF_LOGIN_CMD (
    echo %MLC_HF_LOGIN_CMD%
    call %MLC_HF_LOGIN_CMD%
    IF ERRORLEVEL 1 (
        echo Command failed with error code %ERRORLEVEL%
        exit /b %ERRORLEVEL%
    )
)

REM Run the Hugging Face CLI version command and save output
huggingface-cli version > tmp-ver.out

