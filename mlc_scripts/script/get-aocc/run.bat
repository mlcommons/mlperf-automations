if defined MLC_AOCC_FORCE_VERSION (
    exit /b 0
)

%MLC_AOCC_BIN_WITH_PATH% --version > tmp-ver.out
IF %ERRORLEVEL% NEQ 0 EXIT %ERRORLEVEL%

