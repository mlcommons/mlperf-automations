#!/bin/bash

OUTPUT_FILE="$MLC_PLATFORM_DETAILS_RAW_FILE_PATH"

# Start with empty JSON object
echo '{}' > "$OUTPUT_FILE"

add_entry () {
    local key="$1"
    local cmd="$2"
    local needs_sudo="$3"

    local tmpfile
    tmpfile=$(mktemp)

    if [[ "$needs_sudo" == "yes" ]]; then
      if [[ ${MLC_SUDO_USER} == "yes" ]]; then
        ${MLC_SUDO} bash -c "$cmd" > "$tmpfile" 2>&1 || echo "FAILED (sudo): $cmd" > "$tmpfile"
      else
        echo "sudo not available" > "$tmpfile"
      fi
    else
      bash -c "$cmd" > "$tmpfile" 2>&1 || echo "FAILED: $cmd" > "$tmpfile"
    fi

    # macOS ships with an older jq or none; use python as fallback
    if command -v jq >/dev/null 2>&1; then
      jq --arg k "$key" \
         --arg c "$cmd" \
         --rawfile o "$tmpfile" \
         '. + {($k): {"command": $c, "output": $o}}' \
         "$OUTPUT_FILE" > "$OUTPUT_FILE.tmp" && mv "$OUTPUT_FILE.tmp" "$OUTPUT_FILE"
    else
      python3 -c "
import json, sys
with open('$OUTPUT_FILE') as f:
    data = json.load(f)
with open('$tmpfile') as f:
    output = f.read()
data['$key'] = {'command': '''$cmd''', 'output': output}
with open('$OUTPUT_FILE', 'w') as f:
    json.dump(data, f, indent=2)
"
    fi

    rm -f "$tmpfile"
}

# -------- Kernel / OS --------
add_entry "kernel_and_arch" "uname -a" no
add_entry "sw_vers" "sw_vers" no
add_entry "current_user" "whoami" no
add_entry "logged_in_users" "w" no
add_entry "operating_system" "echo $MLC_HOST_OS_TYPE-$MLC_HOST_OS_FLAVOR_LIKE-$MLC_HOST_OS_FLAVOR-$MLC_HOST_OS_VERSION" no

# -------- CPU / Hardware --------
add_entry "sysctl_hw" "sysctl hw machdep.cpu" no
add_entry "system_profiler" "system_profiler SPHardwareDataType" no

# -------- Memory --------
add_entry "vm_stat" "vm_stat" no

# -------- Disk --------
add_entry "diskutil" "diskutil list" no
add_entry "df_h" "df -h" no

# -------- Network --------
add_entry "ifconfig" "ifconfig -a" no

# -------- Limits --------
add_entry "ulimit_settings" "ulimit -a" no
add_entry "launchctl_limit" "launchctl limit" no

# -------- Sysctl (full) --------
add_entry "sysctl_all" "sysctl -a" no

# -------- Power --------
add_entry "power_settings" "pmset -g" no

# -------- GPU --------
add_entry "gpu_info" "system_profiler SPDisplaysDataType" no

# -------------------------------------------------------------------
# Accelerator detection (CUDA only)
# -------------------------------------------------------------------
if [[ "$MLC_ACCELERATOR_BACKEND" == "cuda" ]]; then
  if command -v nvidia-smi >/dev/null 2>&1; then
    add_entry "nvidia_smi_topo" "nvidia-smi topo -m" no
    add_entry "nvidia_smi_full" "nvidia-smi -q" no
  else
    add_entry "accelerator_error" \
      "echo nvidia-smi not found; cannot detect CUDA accelerator details" no
  fi
fi

echo "Raw system information written to $OUTPUT_FILE"
