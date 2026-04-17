if defined MLC_GCC_FORCE_VERSION (
    exit /b 0
)

%MLC_GCC_BIN_WITH_PATH% --version > tmp-ver.out
IF %ERRORLEVEL% NEQ 0 EXIT %ERRORLEVEL%

