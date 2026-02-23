#ifndef WINDOWS
 #include <unistd.h>
#endif

#include <stdio.h>
#include <cuda.h>

const char* get_memory_type(const char* gpu_name) {
    // Use exact string matches matching the Python dictionary style
    // Keys are copied verbatim from your provided map

    // Datacenter / AI / HPC (Hopper, Blackwell, Ampere)
    // this list is to be improved further
    if (strcmp(gpu_name, "NVIDIA H100 80GB HBM3") == 0) return "HBM3";
    if (strcmp(gpu_name, "NVIDIA H100 PCIe") == 0) return "HBM3";
    if (strcmp(gpu_name, "NVIDIA H100 SXM") == 0) return "HBM3";
    if (strcmp(gpu_name, "NVIDIA H200") == 0) return "HBM3e";
    if (strcmp(gpu_name, "NVIDIA H200 SXM") == 0) return "HBM3e";
    if (strcmp(gpu_name, "NVIDIA B100") == 0) return "HBM3e";
    if (strcmp(gpu_name, "NVIDIA B200") == 0) return "HBM3e";
    if (strcmp(gpu_name, "NVIDIA GB200") == 0) return "HBM3e";       // Grace-Blackwell superchip variant
    if (strcmp(gpu_name, "NVIDIA A100") == 0) return "HBM2e";
    if (strcmp(gpu_name, "NVIDIA A100 PCIe") == 0) return "HBM2e";
    if (strcmp(gpu_name, "NVIDIA A100 SXM") == 0) return "HBM2e";
    if (strcmp(gpu_name, "NVIDIA A800") == 0) return "GDDR6X";       // China export variant
    if (strcmp(gpu_name, "NVIDIA L40S") == 0) return "GDDR6";
    if (strcmp(gpu_name, "NVIDIA L40") == 0) return "GDDR6";
    if (strcmp(gpu_name, "NVIDIA A40") == 0) return "GDDR6";
    if (strcmp(gpu_name, "NVIDIA A30") == 0) return "HBM2";
    if (strcmp(gpu_name, "NVIDIA A10") == 0) return "GDDR6";

    // Professional / Edge / Workstation (Ada Lovelace, Blackwell pro)
    if (strcmp(gpu_name, "NVIDIA RTX 6000 Ada") == 0) return "GDDR6";
    if (strcmp(gpu_name, "NVIDIA RTX 5000 Ada") == 0) return "GDDR6";
    if (strcmp(gpu_name, "NVIDIA RTX 4000 Ada") == 0) return "GDDR6";
    if (strcmp(gpu_name, "NVIDIA RTX Pro 6000D") == 0) return "GDDR7";

    // Consumer / Gaming (frequently used for edge ML too)
    if (strcmp(gpu_name, "NVIDIA GeForce RTX 5090") == 0) return "GDDR7";
    if (strcmp(gpu_name, "NVIDIA GeForce RTX 5080") == 0) return "GDDR7";
    if (strcmp(gpu_name, "NVIDIA GeForce RTX 5070 Ti") == 0) return "GDDR7";
    if (strcmp(gpu_name, "NVIDIA GeForce RTX 5070") == 0) return "GDDR7";
    if (strcmp(gpu_name, "NVIDIA GeForce RTX 5060 Ti") == 0) return "GDDR7";  // ← added as requested
    if (strcmp(gpu_name, "NVIDIA GeForce RTX 4090") == 0) return "GDDR6X";
    if (strcmp(gpu_name, "NVIDIA GeForce RTX 4080") == 0) return "GDDR6X";
    if (strcmp(gpu_name, "NVIDIA GeForce RTX 3090") == 0) return "GDDR6X";
    if (strcmp(gpu_name, "NVIDIA GeForce RTX 3080") == 0) return "GDDR6X";
    if (strcmp(gpu_name, "NVIDIA GeForce RTX 3070") == 0) return "GDDR6";
    if (strcmp(gpu_name, "NVIDIA GeForce RTX 3060") == 0) return "GDDR6";

    // Older but still seen in some edge/datacenter setups
    if (strcmp(gpu_name, "NVIDIA V100") == 0) return "HBM2";
    if (strcmp(gpu_name, "NVIDIA Tesla V100") == 0) return "HBM2";
    if (strcmp(gpu_name, "NVIDIA TITAN RTX") == 0) return "GDDR6";

    return "Unknown / Not in lookup table";
}

int main(int argc, char *argv[])
{
  int ndev=0;
  int id=0;
  cudaError_t error;
  cudaDeviceProp features;

  int rtver=0;
  int dver=0;

  /* Get number of devices */
  error = cudaGetDeviceCount(&ndev);
  if (error != cudaSuccess) {
    printf("Error: problem obtaining number of CUDA devices: %d\n", error);
    return 1;
  }

  /* Iterating over devices */
  for (id=0; id<ndev; id++)
  {
     cudaSetDevice(id);

     printf("GPU Device ID: %d\n", id);

     cudaGetDeviceProperties(&features, id);
     if (error != cudaSuccess) {
       printf("Error: problem obtaining features of CUDA devices: %d\n", error);
       return 1;
     }

     printf("GPU Name: %s\n", features.name);
     printf("GPU compute capability: %d.%d\n", features.major, features.minor);

     error=cudaDriverGetVersion(&dver);
     if (error != cudaSuccess) {
       printf("Error: problem obtaining CUDA driver version: %d\n", error);
       return 1;
     }

     error=cudaRuntimeGetVersion(&rtver);
     if (error != cudaSuccess) {
       printf("Error: problem obtaining CUDA run-time version: %d\n", error);
       return 1;
     }

     printf("CUDA driver version: %d.%d\n", dver/1000, (dver%100)/10);
     printf("CUDA runtime version: %d.%d\n", rtver/1000, (rtver%100)/10);

     const char* mem_type = get_memory_type(features.name);
     printf("Memory Type: %s\n", mem_type);
     
     printf("Global memory: %llu\n", (unsigned long long) features.totalGlobalMem);
     printf("Max clock rate: %f MHz\n", features.clockRate * 0.001);

     printf("Total amount of shared memory per block: %lu\n", features.sharedMemPerBlock);
     printf("Total number of registers available per block: %d\n", features.regsPerBlock);
     printf("Warp size: %d\n", features.warpSize);
     printf("Maximum number of threads per multiprocessor:  %d\n", features.maxThreadsPerMultiProcessor);
     printf("Maximum number of threads per block: %d\n", features.maxThreadsPerBlock);
     printf("Max dimension size of a thread block X: %d\n", features.maxThreadsDim[0]);
     printf("Max dimension size of a thread block Y: %d\n", features.maxThreadsDim[1]);
     printf("Max dimension size of a thread block Z: %d\n", features.maxThreadsDim[2]);
     printf("Max dimension size of a grid size X: %d\n", features.maxGridSize[0]);
     printf("Max dimension size of a grid size Y: %d\n", features.maxGridSize[1]);
     printf("Max dimension size of a grid size Z: %d\n", features.maxGridSize[2]);
     printf("\n");
  }

  return error;
}
