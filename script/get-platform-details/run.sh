#!/bin/bash

OUTPUT_FILE="$MLC_PLATFORM_DETAILS_FILE_PATH"

# Start with empty JSON object. We are using jq to populate the JSON file with a structure like:
# {
#   "key1": {
#     "command": "the command we ran",
#     "output": "the output of the command"
#   },
#   "key2": {
#     "command": "another command",
#     "output": "its output"
#   }
# }
JSON_OBJ='{}'

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

    JSON_OBJ=$(echo "$JSON_OBJ" | jq --arg k "$key" \
                                  --arg c "$cmd" \
                                  --arg o "$output" \
      '. + {($k): {"command": $c, "output": $o}}')
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

    add_entry "accelerator_model_name" \
      "nvidia-smi --query-gpu=name --format=csv,noheader | head -n1" no

    add_entry "accelerators_per_node" \
      "nvidia-smi -L | wc -l" no

    add_entry "accelerator_memory_capacity" \
      "nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -n1 | awk '{print \$1*1024*1024}'" no

    add_entry "accelerator_memory_type" \
      "nvidia-smi --query-gpu=name --format=csv,noheader | head -n1 | grep -qi HBM && echo HBM || echo GDDR" no

    add_entry "accelerator_interconnect" \
      "nvidia-smi topo -m | grep -q NV && echo NVLink || echo PCIe" no

    add_entry "accelerator_host_interconnect" \
      "GEN=\$(nvidia-smi --query-gpu=pcie.link.gen.current --format=csv,noheader,nounits | head -n1); echo PCIe\ Gen\$GEN" no

  else
    add_entry "accelerator_error" \
      "echo nvidia-smi not found; cannot detect CUDA accelerator details" no
  fi
fi

echo
# echo "}" >> "$OUTPUT_FILE"

echo "$JSON_OBJ" | jq '.' > "$OUTPUT_FILE"

echo "System information written to $OUTPUT_FILE"