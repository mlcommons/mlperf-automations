$ErrorActionPreference = 'SilentlyContinue'

try {
    # Get system information
    $allCpus = Get-CimInstance Win32_Processor
    $cpu = $allCpus | Select-Object -First 1
    $cs = Get-CimInstance Win32_ComputerSystem
    $os = Get-CimInstance Win32_OperatingSystem
    $mem = Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property Capacity -Sum
    $disk = Get-PSDrive -PSProvider FileSystem | Where-Object {$_.Free -ne $null} | Measure-Object -Property Used,Free -Sum
    
    # Calculate CPU topology
    $socketCount = $allCpus.Count
    $coresPerSocket = $cpu.NumberOfCores
    $totalCores = ($allCpus | Measure-Object -Property NumberOfCores -Sum).Sum
    $logicalProcessors = $cs.NumberOfLogicalProcessors
    $threadsPerCore = if ($totalCores -gt 0) { [math]::Round($logicalProcessors / $totalCores, 0) } else { 1 }
    
    # Output lscpu-like information
    $output = @()
    $output += "Architecture: $($cpu.Architecture)"
    $output += "CPU op-mode(s): $(if($cpu.AddressWidth -eq 64){'32-bit, 64-bit'}else{'32-bit'})"
    $output += "Byte Order: Little Endian"
    $output += "CPU(s): $logicalProcessors"
    $output += "On-line CPU(s) list: 0-$(($logicalProcessors)-1)"
    $output += "Thread(s) per core: $threadsPerCore"
    $output += "Core(s) per socket: $coresPerSocket"
    $output += "Socket(s): $socketCount"
    $output += "Vendor ID: $($cpu.Manufacturer)"
    $output += "CPU family: $($cpu.Family)"
    $output += "Model: $($cpu.Model)"
    $output += "Model name: $($cpu.Name)"
    $output += "Stepping: $($cpu.Stepping)"
    $output += "CPU MHz: $($cpu.CurrentClockSpeed)"
    $output += "CPU max MHz: $($cpu.MaxClockSpeed)"
    $output += "Virtualization: $(if($cpu.VirtualizationFirmwareEnabled){'Enabled'}else{'Disabled'})"
    if ($cpu.L1CacheSize) { $output += "L1d cache: $($cpu.L1CacheSize) KB" }
    if ($cpu.L2CacheSize) { $output += "L2 cache: $($cpu.L2CacheSize) KB" }
    if ($cpu.L3CacheSize) { $output += "L3 cache: $($cpu.L3CacheSize) KB" }
    $output += "Flags: $($cpu.Description)"
    
    # Write to tmp-lscpu.out
    $output | Out-File -FilePath "tmp-lscpu.out" -Encoding ASCII
    
    # Export CPU details to CSV with UTF-8 encoding (with BOM for Python compatibility)
    $cpu | Export-Csv -Path "tmp-wmic-cpu.csv" -NoTypeInformation -Encoding UTF8
    
    # Generate systeminfo CSV for compatibility
    $systemInfo = [PSCustomObject]@{
        'Host Name' = $env:COMPUTERNAME
        'OS Name' = $os.Caption
        'OS Version' = $os.Version
        'OS Manufacturer' = $os.Manufacturer
        'OS Configuration' = $os.OSType
        'OS Build Type' = $os.BuildType
        'System Manufacturer' = $cs.Manufacturer
        'System Model' = $cs.Model
        'System Type' = $cs.SystemType
        'Processor(s)' = "$($allCpus.Count) Processor(s) Installed."
        'Total Physical Memory' = "$memGB GB"
        'Domain' = $cs.Domain
    }
    $systemInfo | Export-Csv -Path "tmp-systeminfo.csv" -NoTypeInformation -Encoding UTF8
    
    # Calculate memory and disk capacity
    $memGB = [math]::Round($mem.Sum / 1GB, 2)
    $diskUsedGB = [math]::Round(($disk | Where-Object {$_.Property -eq 'Used'}).Sum / 1GB, 2)
    $diskFreeGB = [math]::Round(($disk | Where-Object {$_.Property -eq 'Free'}).Sum / 1GB, 2)
    $diskTotalGB = $diskUsedGB + $diskFreeGB
    
    # Write environment variables
    $envOutput = @()
    $envOutput += "MLC_HOST_MEMORY_CAPACITY=${memGB}G"
    $envOutput += "MLC_HOST_DISK_CAPACITY=${diskTotalGB}G"
    $envOutput += "MLC_HOST_CPU_MICROCODE=$($cpu.Revision)"
    $envOutput += "MLC_HOST_CPU_WRITE_PROTECT_SUPPORT=Not Available on Windows"
    $envOutput += "MLC_HOST_CPU_FPU_SUPPORT=$(if($cpu.ProcessorType -ge 3){'yes'}else{'Not Found'})"
    $envOutput += "MLC_HOST_CPU_FPU_EXCEPTION_SUPPORT=Not Available on Windows"
    $envOutput += "MLC_HOST_CPU_BUGS=Not Available on Windows"
    $envOutput += "MLC_HOST_CPU_TLB_SIZE=Not Available on Windows"
    $envOutput += "MLC_HOST_CPU_CFLUSH_SIZE=Not Available on Windows"
    $envOutput += "MLC_HOST_CACHE_ALIGNMENT_SIZE=$($cpu.DataWidth) bits"
    $envOutput += "MLC_HOST_POWER_MANAGEMENT=$(if($cpu.PowerManagementSupported){'Supported'}else{'Not Supported'})"
    
    $envOutput | Out-File -FilePath "tmp-run-env.out" -Encoding ASCII
    
    exit 0
} catch {
    Write-Error $_.Exception.Message
    exit 1
}
