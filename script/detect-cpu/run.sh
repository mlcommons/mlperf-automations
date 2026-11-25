#!/bin/bash

# Function to extract a field from /proc/cpuinfo
extract_field() {
  local key="$1"
  local default="$2"
  # Use awk to find the first occurrence and extract the value
  local value=$(awk -F: -v key="$key" '$1 ~ key {print $2; exit}' /proc/cpuinfo | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

  # Check if value is empty and assign default if needed
  echo "${value:-$default}"
}

_run_powermetrics_sample() {
  if [[ ${MLC_SUDO_USER} != "yes" ]]; then
    echo "sudo not available for powermetrics" > "$MLC_CPU_FREQ_CAPTURE_OUTPUT_FILE"
    return 1
  fi
  ${MLC_SUDO} powermetrics -s cpu_power -n 1 2>/dev/null | grep 'HW active frequency' > "$MLC_CPU_FREQ_CAPTURE_OUTPUT_FILE" || true
}

_run_cpu_freq_capture() {
  local mode="${MLC_CPU_FREQ_CAPTURE_MODE:-}"
  local output="${MLC_CPU_FREQ_CAPTURE_OUTPUT_FILE:-}"
  local pid_file="${MLC_CPU_FREQ_CAPTURE_PID_FILE:-}"
  local interval="${MLC_CPU_FREQ_CAPTURE_INTERVAL_MS:-500}"

  if [[ -z "$mode" ]]; then
    return 0
  fi
  if [[ -z "$output" ]]; then
    echo "MLC_CPU_FREQ_CAPTURE_OUTPUT_FILE is not set"
    exit 1
  fi

  case "$mode" in
    start)
      if [[ -z "$pid_file" ]]; then
        echo "MLC_CPU_FREQ_CAPTURE_PID_FILE is not set"
        exit 1
      fi
      if [[ -f "$pid_file" ]]; then
        old_pid=$(cat "$pid_file" 2>/dev/null || true)
        if [[ -n "$old_pid" ]]; then
          kill "$old_pid" 2>/dev/null || true
          wait "$old_pid" 2>/dev/null || true
        fi
        rm -f "$pid_file"
      fi
      : > "$output"
      if [[ ${MLC_SUDO_USER} != "yes" ]]; then
        echo "sudo not available for powermetrics" > "$output"
        exit 1
      fi
      ${MLC_SUDO} powermetrics -s cpu_power -i "$interval" -n 0 >> "$output" 2>&1 &
      echo $! > "$pid_file"
      echo "Started powermetrics CPU frequency capture (PID $(cat "$pid_file"))"
      ;;
    stop)
      if [[ -n "$pid_file" ]] && [[ -f "$pid_file" ]]; then
        pid=$(cat "$pid_file" 2>/dev/null || true)
        if [[ -n "$pid" ]]; then
          kill "$pid" 2>/dev/null || true
          wait "$pid" 2>/dev/null || true
        fi
        rm -f "$pid_file"
        echo "Stopped powermetrics CPU frequency capture"
      fi
      ;;
    sample)
      _run_powermetrics_sample
      ;;
    *)
      echo "Unknown MLC_CPU_FREQ_CAPTURE_MODE: $mode"
      exit 1
      ;;
  esac
}

if [[ ${MLC_HOST_OS_FLAVOR} == "macos" ]]; then
    sysctl -a | grep hw > tmp-lscpu.out
    cpu_model_name=$(sysctl -n machdep.cpu.brand_string)
    echo "MLC_HOST_CPU_MODEL_NAME=$cpu_model_name">>tmp-run-env.out
    if [[ -n "${MLC_CPU_FREQ_CAPTURE_MODE:-}" ]]; then
      _run_cpu_freq_capture
    fi
else
    lscpu > tmp-lscpu.out
    memory_capacity=`free -h --si | grep Mem: | tr -s ' ' | cut -d' ' -f2`
    echo "MLC_HOST_MEMORY_CAPACITY=$memory_capacity">>tmp-run-env.out
    disk_capacity=`df -h --total -l |grep total |tr -s ' '|cut -d' ' -f2`
    echo "MLC_HOST_DISK_CAPACITY=$disk_capacity">>tmp-run-env.out

    # extract cpu information which are not there in lscpu
    MLC_HOST_CPU_WRITE_PROTECT_SUPPORT=$(extract_field "wp" "Not Found")
    MLC_HOST_CPU_MICROCODE=$(extract_field "microcode" "Not Found")
    MLC_HOST_CPU_FPU_SUPPORT=$(extract_field "fpu" "Not Found")
    MLC_HOST_CPU_FPU_EXCEPTION_SUPPORT=$(extract_field "fpu_exception" "Not Found")
    MLC_HOST_CPU_BUGS=$(extract_field "bugs" "Not Found")
    MLC_HOST_CPU_TLB_SIZE=$(extract_field "TLB size" "Not Found")
    MLC_HOST_CPU_CFLUSH_SIZE=$(extract_field "clflush size" "Not Found")
    MLC_HOST_CACHE_ALIGNMENT_SIZE=$(extract_field "cache_alignment" "Not Found")
    MLC_HOST_POWER_MANAGEMENT=$(extract_field "power management" "Not Found")

    # Write results to a file
    {
      echo "MLC_HOST_CPU_WRITE_PROTECT_SUPPORT=$MLC_HOST_CPU_WRITE_PROTECT_SUPPORT"
      echo "MLC_HOST_CPU_MICROCODE=$MLC_HOST_CPU_MICROCODE"
      echo "MLC_HOST_CPU_FPU_SUPPORT=$MLC_HOST_CPU_FPU_SUPPORT"
      echo "MLC_HOST_CPU_FPU_EXCEPTION_SUPPORT=$MLC_HOST_CPU_FPU_EXCEPTION_SUPPORT"
      echo "MLC_HOST_CPU_BUGS=$MLC_HOST_CPU_BUGS"
      echo "MLC_HOST_CPU_TLB_SIZE=$MLC_HOST_CPU_TLB_SIZE"
      echo "MLC_HOST_CPU_CFLUSH_SIZE=$MLC_HOST_CPU_CFLUSH_SIZE"
      echo "MLC_HOST_CACHE_ALIGNMENT_SIZE=$MLC_HOST_CACHE_ALIGNMENT_SIZE"
      echo "MLC_HOST_POWER_MANAGEMENT=$MLC_HOST_POWER_MANAGEMENT"
    } >> tmp-run-env.out
fi


