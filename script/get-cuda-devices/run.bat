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

rem Host interconnect (PCIe gen/width) and GPU topology for postprocess.
rem Optional: without nvidia-smi the files are absent and those fields stay
rem unset.
where nvidia-smi >NUL 2>NUL
IF %ERRORLEVEL% EQU 0 (
  nvidia-smi -q > tmp-nvidia-smi-q.out 2>NUL
  nvidia-smi topo -m > tmp-nvidia-smi-topo.out 2>NUL
)
EXIT /B 0
