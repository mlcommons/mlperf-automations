rem native script

%MLC_PYTHON_BIN_WITH_PATH% %MLC_TMP_CURRENT_SCRIPT_PATH%\code.py
IF %ERRORLEVEL% NEQ 0 EXIT %ERRORLEVEL%
