@echo off

REM Get platform architecture
echo %PROCESSOR_ARCHITECTURE% > tmp-run.out

REM Get system information
systeminfo | findstr /B /C:"OS Name" /C:"OS Version" /C:"System Type" >> tmp-run.out

REM Detect OS details
for /f "tokens=4-7 delims=[.] " %%i in ('ver') do (
    set WIN_VERSION=%%i.%%j
)

REM Get OS caption and version
for /f "tokens=2 delims==" %%i in ('wmic os get Caption /value ^| find "="') do set OS_CAPTION=%%i
for /f "tokens=2 delims==" %%i in ('wmic os get Version /value ^| find "="') do set OS_VERSION=%%i

REM Determine OS flavor
echo %OS_CAPTION% | findstr /i "Windows 11" >nul
if %errorlevel%==0 (
    set OS_FLAVOR=windows11
) else (
    echo %OS_CAPTION% | findstr /i "Windows 10" >nul
    if %errorlevel%==0 (
        set OS_FLAVOR=windows10
    ) else (
        echo %OS_CAPTION% | findstr /i "Server 2022" >nul
        if %errorlevel%==0 (
            set OS_FLAVOR=windowsserver2022
        ) else (
            echo %OS_CAPTION% | findstr /i "Server 2019" >nul
            if %errorlevel%==0 (
                set OS_FLAVOR=windowsserver2019
            ) else (
                set OS_FLAVOR=windows
            )
        )
    )
)

REM Write environment variables to tmp-run-env.out
echo MLC_HOST_OS_FLAVOR=%OS_FLAVOR% > tmp-run-env.out
echo MLC_HOST_OS_FLAVOR_LIKE=windows >> tmp-run-env.out
echo MLC_HOST_OS_VERSION=%OS_VERSION% >> tmp-run-env.out
echo MLC_HOST_OS_KERNEL_VERSION=%OS_VERSION% >> tmp-run-env.out
echo MLC_HOST_PLATFORM_FLAVOR=%PROCESSOR_ARCHITECTURE% >> tmp-run-env.out
