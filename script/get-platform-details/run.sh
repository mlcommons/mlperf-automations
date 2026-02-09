#!/bin/bash

OUTPUT_FILE="$MLC_PLATFORM_DETAILS_FILE_PATH"

echo "{" > "$OUTPUT_FILE"
FIRST=true

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

echo
echo "}" >> "$OUTPUT_FILE"

echo "System information written to $OUTPUT_FILE"
