rem Detect version

%MLC_ARIA2_BIN_WITH_PATH% --version > tmp-ver.out
IF %ERRORLEVEL% NEQ 0 EXIT %ERRORLEVEL%
