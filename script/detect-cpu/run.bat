@echo off
setlocal enabledelayedexpansion

REM Clear output files
if exist tmp-lscpu.out del tmp-lscpu.out
if exist tmp-run-env.out del tmp-run-env.out
if exist tmp-wmic-cpu.csv del tmp-wmic-cpu.csv

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0

REM Try PowerShell script first for comprehensive CPU information
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%detect-cpu.ps1" 2>nul

if %errorlevel% neq 0 (
    echo PowerShell script failed, falling back to WMIC...
    
    REM Fallback to WMIC for older Windows systems
    wmic cpu get Name,Manufacturer,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed,CurrentClockSpeed,L2CacheSize,L3CacheSize,AddressWidth /format:list > tmp-lscpu.out 2>nul
    wmic cpu get /FORMAT:csv > tmp-wmic-cpu.csv 2>nul
    
    REM Get memory capacity using WMIC
    for /f "skip=1 tokens=2 delims=," %%a in ('wmic ComputerSystem get TotalPhysicalMemory /format:csv') do (
        set /a memGB=%%a/1000000000
        echo MLC_HOST_MEMORY_CAPACITY=!memGB!G > tmp-run-env.out
    )
    
    REM Get disk capacity using WMIC
    set totalDisk=0
    for /f "skip=1 tokens=2 delims=," %%a in ('wmic logicaldisk where "DriveType=3" get Size /format:csv') do (
        if not "%%a"=="" (
            set /a totalDisk+=%%a/1000000000
        )
    )
    echo MLC_HOST_DISK_CAPACITY=!totalDisk!G >> tmp-run-env.out
    
    REM CPU details (limited on Windows)
    echo MLC_HOST_CPU_WRITE_PROTECT_SUPPORT=Not Available on Windows >> tmp-run-env.out
    echo MLC_HOST_CPU_MICROCODE=Not Available via WMIC >> tmp-run-env.out
    echo MLC_HOST_CPU_FPU_SUPPORT=Not Available via WMIC >> tmp-run-env.out
    echo MLC_HOST_CPU_FPU_EXCEPTION_SUPPORT=Not Available on Windows >> tmp-run-env.out
    echo MLC_HOST_CPU_BUGS=Not Available on Windows >> tmp-run-env.out
    echo MLC_HOST_CPU_TLB_SIZE=Not Available on Windows >> tmp-run-env.out
    echo MLC_HOST_CPU_CFLUSH_SIZE=Not Available on Windows >> tmp-run-env.out
    echo MLC_HOST_CACHE_ALIGNMENT_SIZE=Not Available via WMIC >> tmp-run-env.out
    echo MLC_HOST_POWER_MANAGEMENT=Not Available via WMIC >> tmp-run-env.out
)

endlocal

