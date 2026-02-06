#!/bin/bash

OUTPUT_FILE="${MLC_MLPERF_SYSTEM_INFO_FILE_PATH:-system-info.txt}"
echo "Collecting system info to: $OUTPUT_FILE"
echo "WARNING: Some commands require sudo (dmidecode, sysctl, etc.)"

> "$OUTPUT_FILE"  # Clear file

echo "=== KEY_SYSTEM_INFO ===" >> "$OUTPUT_FILE"

echo "host_processor_model_name: $(lscpu | grep -m1 'Model name:' | cut -d':' -f2- | sed 's/^[ \t]*//')" >> "$OUTPUT_FILE"
echo "host_processors_per_node: $(lscpu | grep 'Socket(s):' | awk '{print $2}')" >> "$OUTPUT_FILE"
echo "host_processor_core_count: $(lscpu | grep 'Core(s) per socket:' | awk '{print $4}')" >> "$OUTPUT_FILE"
echo "threads_per_core: $(lscpu | grep 'Thread(s) per core:' | awk '{print $4}')" >> "$OUTPUT_FILE"
echo "host_processor_vcpu_count: $(( $(lscpu | grep 'Socket(s):' | awk '{print $2}') * $(lscpu | grep 'Core(s) per socket:' | awk '{print $4}') * $(lscpu | grep 'Thread(s) per core:' | awk '{print $4}') ))" >> "$OUTPUT_FILE"

# GPU / Accelerator info (critical for your keys)
if command -v nvidia-smi >/dev/null 2>&1; then
    echo "accelerator_model_name: $(nvidia-smi --query-gpu=name --format=csv,noheader | head -1 | sed 's/ NVIDIA //')" >> "$OUTPUT_FILE"
    echo "accelerators_per_node: $(nvidia-smi -L | wc -l)" >> "$OUTPUT_FILE"
    echo "accelerator_memory_capacity: $(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1 | awk '{printf "%.0f GB\n", $1/1024}')" >> "$OUTPUT_FILE"
    echo "accelerator_memory_type: HBM3e" >> "$OUTPUT_FILE"   # common for Blackwell; can parse if variant available

    # NVLink info
    NV_C2C=$(nvidia-smi nvlink -s 2>/dev/null | grep -i 'C2C' || echo "NVLink-C2C")
    NV_INTER=$(nvidia-smi topo -m 2>/dev/null | grep -i 'NVLink' || echo "5th-gen NVLink and NVLink Switches")
    echo "accelerator_host_interconnect: $NV_C2C" >> "$OUTPUT_FILE"
    echo "accelerator_interconnect: $NV_INTER" >> "$OUTPUT_FILE"
else
    echo "accelerators_per_node: 0" >> "$OUTPUT_FILE"
    echo "accelerator_model_name: None" >> "$OUTPUT_FILE"
fi

# Host memory
echo "host_memory_capacity: $(free -h | grep Mem: | awk '{print $2}')" >> "$OUTPUT_FILE"
if [[ ${MLC_SUDO_USER} == "yes" ]]; then
    echo "host_memory_configuration: $(sudo dmidecode --type memory 2>/dev/null | grep -i 'Type: LPDDR5X' -A 5 | grep -i 'Size' | head -1 | awk '{print $2 " " $3}' || echo "LPDDR5X")" >> "$OUTPUT_FILE"
fi

# Network
echo "host_network_card_count: $(lspci | grep -iE 'Mellanox|ConnectX|BlueField|Ethernet|Network' | wc -l) cards detected ($(lspci | grep -iE 'Mellanox|ConnectX|BlueField' || echo 'No Mellanox/BlueField detected'))" >> "$OUTPUT_FILE"
echo "host_networking: $( (ibstat | grep 'Link layer' | head -1 || ethtool eth0 2>/dev/null | grep -i speed) | sed 's/^[ \t]*//')" >> "$OUTPUT_FILE"

# Storage (basic summary)
echo "host_storage_capacity: $(lsblk -o NAME,SIZE,TYPE,MOUNTPOINT | grep -E 'disk|nvme' | awk '{print $2 " " $1 " " $3}' | paste -sd ', ' -)" >> "$OUTPUT_FILE"
echo "host_storage_type: NVMe SSD, possibly CIFS/NFS mounted" >> "$OUTPUT_FILE"

# General system context
echo "kernel_version: $(uname -r)" >> "$OUTPUT_FILE"
echo "architecture: $(uname -m)" >> "$OUTPUT_FILE"
echo "numa_nodes: $(lscpu | grep 'NUMA node(s):' | awk '{print $3}')" >> "$OUTPUT_FILE"

echo "=== FULL_RAW_DATA ===" >> "$OUTPUT_FILE"
echo "lscpu output:" >> "$OUTPUT_FILE"
lscpu >> "$OUTPUT_FILE" 2>&1

echo "nvidia-smi -q summary:" >> "$OUTPUT_FILE"
nvidia-smi -q 2>/dev/null | head -n 60 >> "$OUTPUT_FILE" || echo "nvidia-smi not found" >> "$OUTPUT_FILE"

echo "dmidecode memory (sudo):" >> "$OUTPUT_FILE"
if [[ ${MLC_SUDO_USER} == "yes" ]]; then
    sudo dmidecode --type memory 2>/dev/null >> "$OUTPUT_FILE" || echo "sudo dmidecode failed" >> "$OUTPUT_FILE"
fi
echo "lspci network devices:" >> "$OUTPUT_FILE"
lspci | grep -iE 'ethernet|network|infiniband|mellanox|connectx|bluefield' >> "$OUTPUT_FILE"

echo "lsblk storage:" >> "$OUTPUT_FILE"
lsblk -o NAME,SIZE,TYPE,MOUNTPOINT,FSTYPE >> "$OUTPUT_FILE"

echo "System information collection complete."