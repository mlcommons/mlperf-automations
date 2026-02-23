import pycuda.driver as cuda
import pycuda.autoinit


def get_gpu_info():
    num_gpus = cuda.Device.count()
    all_gpu_info = []

    for i in range(num_gpus):
        device = cuda.Device(i)
        cuda_runtime_version = cuda.get_version()
        cuda_runtime_version_str = f"{cuda_runtime_version[0]}.{cuda_runtime_version[1]}"

        memory_type_map = {
            # Datacenter / AI / HPC (Hopper, Blackwell, Ampere)
            # this list is to be improved further
            "NVIDIA H100 80GB HBM3": "HBM3",
            "NVIDIA H100 PCIe": "HBM3",
            "NVIDIA H100 SXM": "HBM3",
            "NVIDIA H200": "HBM3e",
            "NVIDIA H200 SXM": "HBM3e",
            "NVIDIA B100": "HBM3e",
            "NVIDIA B200": "HBM3e",
            "NVIDIA GB200": "HBM3e",       # Grace-Blackwell superchip variant
            "NVIDIA A100": "HBM2e",
            "NVIDIA A100 PCIe": "HBM2e",
            "NVIDIA A100 SXM": "HBM2e",
            "NVIDIA A800": "GDDR6X",       # China export variant
            "NVIDIA L40S": "GDDR6",
            "NVIDIA L40": "GDDR6",
            "NVIDIA A40": "GDDR6",
            "NVIDIA A30": "HBM2",
            "NVIDIA A10": "GDDR6",

            # Professional / Edge / Workstation (Ada Lovelace, Blackwell pro)
            "NVIDIA RTX 6000 Ada": "GDDR6",
            "NVIDIA RTX 5000 Ada": "GDDR6",
            "NVIDIA RTX 4000 Ada": "GDDR6",
            "NVIDIA RTX Pro 6000D": "GDDR7",

            # Consumer / Gaming (frequently used for edge ML too)
            "NVIDIA GeForce RTX 5090": "GDDR7",
            "NVIDIA GeForce RTX 5080": "GDDR7",
            "NVIDIA GeForce RTX 5070 Ti": "GDDR7",
            "NVIDIA GeForce RTX 5070": "GDDR7",
            "NVIDIA GeForce RTX 5060 Ti": "GDDR7",
            "NVIDIA GeForce RTX 4090": "GDDR6X",
            "NVIDIA GeForce RTX 4080": "GDDR6X",
            "NVIDIA GeForce RTX 3090": "GDDR6X",
            "NVIDIA GeForce RTX 3080": "GDDR6X",
            "NVIDIA GeForce RTX 3070": "GDDR6",
            "NVIDIA GeForce RTX 3060": "GDDR6",

            # Older but still seen in some edge/datacenter setups
            "NVIDIA V100": "HBM2",
            "NVIDIA Tesla V100": "HBM2",
            "NVIDIA TITAN RTX": "GDDR6",
        }
        

        memory_type = memory_type_map.get(device.name(), "Unknown / Not in lookup table")

        gpu_info = {
            "GPU Device ID": device.pci_bus_id(),
            "GPU Name": device.name(),
            "GPU compute capability": f"{device.compute_capability()[0]}.{device.compute_capability()[1]}",
            "CUDA driver version": f"{cuda.get_driver_version() // 1000}.{(cuda.get_driver_version() % 1000) // 10}",
            "CUDA runtime version": cuda_runtime_version_str,
            "Memory Type": memory_type,
            "Global memory": device.total_memory(),
            "Max clock rate": f"{device.get_attribute(cuda.device_attribute.CLOCK_RATE)} MHz",
            "Total amount of shared memory per block": device.get_attribute(cuda.device_attribute.MAX_SHARED_MEMORY_PER_BLOCK),
            "Total number of registers available per block": device.get_attribute(cuda.device_attribute.MAX_REGISTERS_PER_BLOCK),
            "Warp size": device.get_attribute(cuda.device_attribute.WARP_SIZE),
            "Maximum number of threads per multiprocessor": device.get_attribute(cuda.device_attribute.MAX_THREADS_PER_MULTIPROCESSOR),
            "Maximum number of threads per block": device.get_attribute(cuda.device_attribute.MAX_THREADS_PER_BLOCK),
            "Max dimension size of a thread block X": device.get_attribute(cuda.device_attribute.MAX_BLOCK_DIM_X),
            "Max dimension size of a thread block Y": device.get_attribute(cuda.device_attribute.MAX_BLOCK_DIM_Y),
            "Max dimension size of a thread block Z": device.get_attribute(cuda.device_attribute.MAX_BLOCK_DIM_Z),
            "Max dimension size of a grid size X": device.get_attribute(cuda.device_attribute.MAX_GRID_DIM_X),
            "Max dimension size of a grid size Y": device.get_attribute(cuda.device_attribute.MAX_GRID_DIM_Y),
            "Max dimension size of a grid size Z": device.get_attribute(cuda.device_attribute.MAX_GRID_DIM_Z),
        }

        all_gpu_info.append(gpu_info)

    return all_gpu_info


# Print the GPU information for all available GPUs
if __name__ == "__main__":
    gpu_info_list = get_gpu_info()
    with open("tmp-run.out", "w") as f:
        for idx, gpu_info in enumerate(gpu_info_list):
            print(f"GPU {idx}:")
            for key, value in gpu_info.items():
                f.write(f"{key}: {value}\n")
