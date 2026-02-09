#!/bin/bash

OUTPUT_FILE="$MLC_PLATFORM_DETAILS_FILE_PATH"

echo "{" > "$OUTPUT_FILE"
FIRST=true

add_kv () {
  local key="$1"
  local cmd_json="$2"
  local output_json="$3"

  if [ "$FIRST" = true ]; then
    FIRST=false
  else
    echo "," >> "$OUTPUT_FILE"
  fi

  cat >> "$OUTPUT_FILE" <<EOF
    "$key": {
      "command": $cmd_json,
      "output": $output_json
    }
EOF
}

add_entry () {
    local key="$1"
    local cmd="$2"
    local needs_sudo="$3"

    local output

    if [[ "$needs_sudo" == "yes" ]]; then
      if [[ ${MLC_SUDO_USER} == "yes" ]]; then
        output="$(${MLC_SUDO} bash -c "$cmd" 2>&1 || echo "FAILED (sudo): $cmd")"
      else
        output="sudo not available"
      fi
    else
      output="$(bash -c "$cmd" 2>&1 || echo "FAILED: $cmd")"
    fi

    local cmd_json
    local output_json
    cmd_json=$(printf '%s' "$cmd" | jq -Rs .)
    output_json=$(printf '%s' "$output" | jq -Rs .)

    add_kv "$key" "$cmd_json" "$output_json"
}

# -------- Non-sudo commands --------
add_entry "kernel_and_arch" "uname -a" no
add_entry "logged_in_users" "w" no
add_entry "current_user" "whoami" no
add_entry "ulimit_settings" "ulimit -a" no
add_entry "process_tree" "pstree" no
add_entry "cpuinfo" "cat /proc/cpuinfo" no
add_entry "lscpu" "lscpu" no
add_entry "cpu_cache" "lscpu --cache" no
add_entry "memory_info" "cat /proc/meminfo" no
add_entry "runlevel" "who -r" no
add_entry "systemd_version" "systemctl --version | head -n 1" no
add_entry "systemd_units" "systemctl list-unit-files" no
add_entry "kernel_cmdline" "cat /proc/cmdline" no
add_entry "thp_enabled" "cat /sys/kernel/mm/transparent_hugepage/enabled" no
add_entry "thp_defrag" "cat /sys/kernel/mm/transparent_hugepage/khugepaged/defrag" no
add_entry "os_release" "cat /etc/os-release" no
add_entry "disk_layout" "lsblk" no
add_entry "lsb_release" "lsb_release -d" no
add_entry "etc_versions" "cat /etc/*version*" no
add_entry "etc_releases" "cat /etc/*release*" no
add_entry "cpu_vulnerabilities" "grep . /sys/devices/system/cpu/vulnerabilities/*" no
add_entry "numa_topology" "numactl --hardware" no
add_entry "cpu_frequency" "cpupower frequency-info" no
add_entry "memory_free_human" "free -h" no
add_entry "pci_devices" "lspci" no
add_entry "infiniband_status" "ibstat" no   # requires Infiniband drivers; will fail gracefully if not present

# -------- Sudo-required commands --------
add_entry "sysctl_all" "sysctl -a" yes
add_entry "dmi_entries" "ls /sys/devices/virtual/dmi/id" yes
add_entry "dmidecode_full" "dmidecode" yes
add_entry "bios_info" "dmidecode -t bios" yes

# -------------------------------------------------------------------
# Accelerator detection (CUDA only)
# -------------------------------------------------------------------
if [[ "$MLC_ACCELERATOR_BACKEND" == "cuda" ]]; then

  if command -v nvidia-smi >/dev/null 2>&1; then

    GPU_NAME="$(nvidia-smi --query-gpu=name --format=csv,noheader | head -n1)"
    GPU_COUNT="$(nvidia-smi -L | wc -l)"
    GPU_MEM_BYTES="$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -n1)"

    # Convert MiB → bytes
    GPU_MEM_BYTES=$((GPU_MEM_BYTES * 1024 * 1024))

    # Memory type (derived from model)
    if echo "$GPU_NAME" | grep -qi "HBM"; then
      MEM_TYPE="HBM"
    else
      MEM_TYPE="GDDR"
    fi

    # Host interconnect (PCIe vs SXM)
    if echo "$GPU_NAME" | grep -qi "SXM"; then
      HOST_INTERCONNECT="NVLink"
    else
      HOST_INTERCONNECT="PCIe"
    fi

    # GPU↔GPU interconnect
    if nvidia-smi topo -m | grep -q "NV"; then
      GPU_INTERCONNECT="NVLink"
    else
      GPU_INTERCONNECT="PCIe"
    fi

    add_kv "accelerator_model_name" "nvidia-smi --query-gpu=name --format=csv,noheader" "$GPU_NAME"
    add_kv "accelerators_per_node" "nvidia-smi -L | wc -l" "$GPU_COUNT"
    add_kv "accelerator_memory_capacity" "nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits" "$GPU_MEM_BYTES"
    add_kv "accelerator_memory_type" "nvidia-smi --query-gpu=name --format=csv,noheader" "$MEM_TYPE"
    add_kv "accelerator_host_interconnect" "nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits" "$HOST_INTERCONNECT"
    add_kv "accelerator_interconnect" "nvidia-smi topo -m" "$GPU_INTERCONNECT"

  else
    add_kv "accelerator_model_name" "nvidia-smi --query-gpu=name --format=csv,noheader" "nvidia-smi not found; cannot detect CUDA accelerator details"
    add_kv "accelerators_per_node" "nvidia-smi -L | wc -l" "nvidia-smi not found; cannot detect CUDA accelerator details"
    add_kv "accelerator_memory_capacity" "nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits" "nvidia-smi not found; cannot detect CUDA accelerator details"
    add_kv "accelerator_memory_type" "nvidia-smi --query-gpu=name --format=csv,noheader" "nvidia-smi not found; cannot detect CUDA accelerator details"
    add_kv "accelerator_host_interconnect" "nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits" "nvidia-smi not found; cannot detect CUDA accelerator details"
    add_kv "accelerator_interconnect" "nvidia-smi topo -m" "nvidia-smi not found; cannot detect CUDA accelerator details"
  fi
fi

# -------- Accelerator interconnect detection (CUDA only) --------

if [[ "$MLC_ACCELERATOR_BACKEND" == "cuda" ]]; then

  INTERCONNECT="unknown"
  INTERCONNECT_ERROR=""

  if command -v nvidia-smi >/dev/null 2>&1; then
    TOPO_OUT="$(nvidia-smi topo -m 2>&1)"

    if echo "$TOPO_OUT" | grep -q "NV"; then
      INTERCONNECT="NVLink"
    else
      INTERCONNECT="PCIe"
    fi
  else
    INTERCONNECT_ERROR="nvidia-smi not found; cannot detect accelerator_interconnect"
  fi

  # Append to JSON
  echo "," >> "$OUTPUT_FILE"
  cat >> "$OUTPUT_FILE" <<EOF
  "accelerator_interconnect": {
    "value": "$(printf '%s' "$INTERCONNECT")",
    "error": "$(printf '%s' "$INTERCONNECT_ERROR")"
  }
EOF

fi

echo
echo "}" >> "$OUTPUT_FILE"

echo "System information written to $OUTPUT_FILE"

