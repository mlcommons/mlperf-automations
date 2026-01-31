@echo off

REM Get platform architecture
echo %PROCESSOR_ARCHITECTURE% > tmp-run.out

REM Get system information
systeminfo | findstr /B /C:"OS Name" /C:"OS Version" /C:"System Type" >> tmp-run.out

REM Detect OS details
for /f "tokens=4-7 delims=[.] " %%i in ('ver') do (
    set WIN_VERSION=%%i.%%j
)

REM Get OS caption and version from systeminfo output
for /f "tokens=2* delims=:" %%i in ('systeminfo ^| findstr /B /C:"OS Name"') do set "OS_CAPTION=%%j"
for /f "tokens=2* delims=:" %%i in ('systeminfo ^| findstr /B /C:"OS Version"') do set "OS_VERSION=%%j"

REM Trim leading spaces
if defined OS_CAPTION for /f "tokens=* delims= " %%i in ("%OS_CAPTION%") do set "OS_CAPTION=%%i"
if defined OS_VERSION for /f "tokens=* delims= " %%i in ("%OS_VERSION%") do set "OS_VERSION=%%i"

REM Set default flavor
set "OS_FLAVOR=windows"

REM Determine OS flavor
if defined OS_CAPTION (
    echo %OS_CAPTION% | findstr /i "Windows 11" >nul
    if not errorlevel 1 set "OS_FLAVOR=windows11"
    
    echo %OS_CAPTION% | findstr /i "Windows 10" >nul
    if not errorlevel 1 set "OS_FLAVOR=windows10"
    
    echo %OS_CAPTION% | findstr /i "Server 2022" >nul
    if not errorlevel 1 set "OS_FLAVOR=windowsserver2022"
    
    echo %OS_CAPTION% | findstr /i "Server 2019" >nul
    if not errorlevel 1 set "OS_FLAVOR=windowsserver2019"
    
    echo %OS_CAPTION% | findstr /i "Server 2016" >nul
    if not errorlevel 1 set "OS_FLAVOR=windowsserver2016"
)

REM Write environment variables to tmp-run-env.out
echo MLC_HOST_OS_FLAVOR=%OS_FLAVOR% > tmp-run-env.out
echo MLC_HOST_OS_FLAVOR_LIKE=windows >> tmp-run-env.out
echo MLC_HOST_OS_VERSION=%OS_VERSION% >> tmp-run-env.out
echo MLC_HOST_OS_KERNEL_VERSION=%OS_VERSION% >> tmp-run-env.out
echo MLC_HOST_PLATFORM_FLAVOR=%PROCESSOR_ARCHITECTURE% >> tmp-run-env.out
