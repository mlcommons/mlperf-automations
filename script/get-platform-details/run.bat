@echo off
setlocal enabledelayedexpansion

set "OUTPUT_FILE=%MLC_PLATFORM_DETAILS_RAW_FILE_PATH%"

:: Initialize empty JSON via Python
python -c "import json; json.dump({}, open(r'%OUTPUT_FILE%', 'w'), indent=2)"

:: Helper: run a command and add its output to the JSON file using Python
:: Usage: call :add_entry KEY "COMMAND"
:: We use Python to safely handle JSON escaping

call :add_entry "kernel_and_arch" "ver"
call :add_entry "current_user" "whoami"
call :add_entry "operating_system" "echo %MLC_HOST_OS_TYPE%-%MLC_HOST_OS_FLAVOR%-%MLC_HOST_OS_VERSION%"

:: CPU info via PowerShell
call :add_entry "cpu_info" "powershell -NoProfile -Command \"Get-CimInstance Win32_Processor | Format-List Name,Manufacturer,MaxClockSpeed,CurrentClockSpeed,NumberOfCores,NumberOfLogicalProcessors,L2CacheSize,L3CacheSize,Architecture,Caption,DeviceID,SocketDesignation,AddressWidth,VirtualizationFirmwareEnabled\""

:: OS info via PowerShell
call :add_entry "os_info" "powershell -NoProfile -Command \"Get-CimInstance Win32_OperatingSystem | Format-List Caption,Version,BuildNumber,OSArchitecture,TotalVisibleMemorySize,FreePhysicalMemory,InstallDate,LastBootUpTime,SystemDirectory\""

:: systeminfo
call :add_entry "systeminfo" "systeminfo"

:: Memory DIMMs via PowerShell
call :add_entry "memory_info" "powershell -NoProfile -Command \"Get-CimInstance Win32_PhysicalMemory | Format-List Capacity,Manufacturer,PartNumber,Speed,MemoryType,FormFactor,BankLabel,DeviceLocator,SerialNumber\""

:: Disk info via PowerShell
call :add_entry "disk_info" "powershell -NoProfile -Command \"Get-CimInstance Win32_DiskDrive | Format-List Model,Size,MediaType,InterfaceType,SerialNumber,Caption\""

:: Network adapters
call :add_entry "network_adapters" "powershell -NoProfile -Command \"Get-NetAdapter | Format-List Name,InterfaceDescription,Status,LinkSpeed,MacAddress\""

:: Environment variables (selected)
call :add_entry "env_info" "powershell -NoProfile -Command \"Get-ChildItem Env: | Where-Object { $_.Name -match 'PROCESSOR|NUMBER_OF_PROCESSORS|OS|COMPUTERNAME|USERNAME|USERDOMAIN' } | Format-List\""

:: BIOS info via PowerShell
call :add_entry "bios_info" "powershell -NoProfile -Command \"Get-CimInstance Win32_BIOS | Format-List Manufacturer,Name,Version,ReleaseDate,SMBIOSBIOSVersion\""

:: Baseboard info
call :add_entry "baseboard_info" "powershell -NoProfile -Command \"Get-CimInstance Win32_BaseBoard | Format-List Manufacturer,Product,Version,SerialNumber\""

:: GPU info via PowerShell
call :add_entry "gpu_info" "powershell -NoProfile -Command \"Get-CimInstance Win32_VideoController | Format-List Name,AdapterRAM,DriverVersion,VideoProcessor,CurrentHorizontalResolution,CurrentVerticalResolution\""

:: -------------------------------------------------------------------
:: Accelerator detection (CUDA only)
:: -------------------------------------------------------------------
if "%MLC_ACCELERATOR_BACKEND%"=="cuda" (
  where nvidia-smi >nul 2>&1
  if !errorlevel! equ 0 (
    call :add_entry "nvidia_smi_topo" "nvidia-smi topo -m"
    call :add_entry "nvidia_smi_full" "nvidia-smi -q"
  ) else (
    call :add_entry "accelerator_error" "echo nvidia-smi not found"
  )
)

echo Raw system information written to %OUTPUT_FILE%
exit /b 0

:add_entry
:: %~1 = key, %~2 = command
set "ENTRY_KEY=%~1"
set "ENTRY_CMD=%~2"

:: Create temp file for command output
set "TMPFILE=%TEMP%\mlc_platform_%RANDOM%.txt"
%ENTRY_CMD% > "%TMPFILE%" 2>&1

:: Use Python to safely add the entry to JSON (handles all escaping)
python -c "import json; f=open(r'%OUTPUT_FILE%'); data=json.load(f); f.close(); g=open(r'%TMPFILE%', encoding='utf-8', errors='replace'); out=g.read(); g.close(); data[r'%ENTRY_KEY%']={'command': r'%ENTRY_CMD%', 'output': out}; h=open(r'%OUTPUT_FILE%','w'); json.dump(data, h, indent=2); h.close()"

del /f /q "%TMPFILE%" >nul 2>&1
exit /b 0
