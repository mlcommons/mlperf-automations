rem Compile

del a.exe

echo.
echo NVCC path: %MLC_NVCC_BIN_WITH_PATH%
echo.

echo.
echo Checking compiler version ...
echo.

"%MLC_NVCC_BIN_WITH_PATH%" -V

echo.
echo Compiling program ...
echo.

"%MLC_NVCC_BIN_WITH_PATH%" %MLC_TMP_CURRENT_SCRIPT_PATH%\print_cuda_devices.cu -allow-unsupported-compiler -DWINDOWS
IF %ERRORLEVEL% NEQ 0 EXIT %ERRORLEVEL%

rem Return to the original path obtained in CM

echo.
echo Running program ...
echo.

.\a.exe > tmp-run.out
IF %ERRORLEVEL% NEQ 0 EXIT %ERRORLEVEL%
