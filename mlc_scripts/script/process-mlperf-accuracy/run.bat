echo Running command:
echo.
echo %MLC_RUN_CMDS%
echo.

%MLC_RUN_CMDS%

IF %ERRORLEVEL% NEQ 0 EXIT %ERRORLEVEL%
