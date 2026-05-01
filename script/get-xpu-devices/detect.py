import json
import subprocess

def get_xpu_info():
    xpus = subprocess.run(["sudo", "xpu-smi", "discovery", "-j"], capture_output=True, text=True)
    xpu_devices = json.loads(xpus.stdout)["device_list"]
    num_xpus = len(xpu_devices)
    all_xpu_info = []

    for i in range(num_xpus):
        
        device_id = i
        device_info = subprocess.run(["sudo", "xpu-smi", "discovery", "-d", str(device_id), "-j"], capture_output=True, text=True)
        device_info_json = json.loads(device_info.stdout)
        device_name = device_info_json["device_name"]

        memory_type_map = {
            # Arc Pro Series
            "Intel(R) Arc(TM) Pro B50 Graphics": "GDDR6",
            "Intel(R) Arc(TM) Pro B60 Graphics": "GDDR6",
            "Intel(R) Arc(TM) Pro B70 Graphics": "GDDR6",
        }

        memory_type = memory_type_map.get(
            device_name, "Unknown / Not in lookup table")

        xpu_info = {
            "GPU Device ID": device_info_json["pci_device_id"],
            "GPU Name": device_name,
            "XPU driver version": f"{device_info_json['driver_version']}",
            "Memory Type": memory_type,
            "Global memory": f"{round(int(device_info_json['memory_physical_size_byte']) / 1_073_741_824)} GiB",  # Convert bytes to GiB; key maps to MLC_XPU_DEVICE_PROP_GLOBAL_MEMORY
            "Max clock rate": f"{device_info_json['core_clock_rate_mhz']} MHz",
            "Number of EUs": device_info_json["number_of_eus"],
            "EU Threads per EU": device_info_json["number_of_threads_per_eu"],
            "Host Interconnect Type": f"{float(device_info_json['pcie_generation']):.1f} x{device_info_json['pcie_max_link_width']}",
            "Host Interconnect Bandwidth": f"{device_info_json['pcie_max_bandwidth']}",
        }

        all_xpu_info.append(xpu_info)

    return all_xpu_info


# Print the XPU information for all available XPUs
if __name__ == "__main__":
    xpu_info_list = get_xpu_info()
    with open("tmp-run.out", "w") as f:
        for idx, xpu_info in enumerate(xpu_info_list):
            print(f"XPU {idx}:")
            for key, value in xpu_info.items():
                f.write(f"{key}: {value}\n")
