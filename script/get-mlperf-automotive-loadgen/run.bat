@echo off

echo =======================================================

set CUR_DIR=%cd%
echo Current path in CM script: %CUR_DIR%

if "%MLC_MLPERF_AUTOMOTIVE_LOADGEN_DOWNLOAD%" == "YES" (
  set MLC_MLPERF_AUTOMOTIVE_SOURCE=%MLC_EXTRACT_EXTRACTED_PATH%
)

set INSTALL_DIR=%CUR_DIR%\install

echo.
echo Switching to %MLC_MLPERF_AUTOMOTIVE_SOURCE%\loadgen

cd %MLC_MLPERF_AUTOMOTIVE_SOURCE%\loadgen
IF %ERRORLEVEL% NEQ 0 EXIT %ERRORLEVEL%

echo.
echo Running %MLC_PYTHON_BIN% setup.py develop

%MLC_PYTHON_BIN% setup.py develop
IF %ERRORLEVEL% NEQ 0 EXIT %ERRORLEVEL%

echo =======================================================
cmake ^
    -DCMAKE_INSTALL_PREFIX=%INSTALL_DIR% ^
     %MLC_MLPERF_AUTOMOTIVE_SOURCE%\loadgen ^
     -DPYTHON_EXECUTABLE:FILEPATH=%MLC_PYTHON_BIN_WITH_PATH%
IF %ERRORLEVEL% NEQ 0 EXIT %ERRORLEVEL%

echo =======================================================
cmake --build . --target install
IF %ERRORLEVEL% NEQ 0 EXIT %ERRORLEVEL%

del /Q /S build

echo =======================================================
