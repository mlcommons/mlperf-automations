# MLCommons Automation Scripts

*Last updated: 2026-02-21 03:34:11*

This directory contains automation scripts for MLPerf benchmarks, AI/ML workflows, and development operations.

## Table of Contents

- [AI/ML datasets](#aiml-datasets)
- [AI/ML frameworks](#aiml-frameworks)
- [AI/ML models](#aiml-models)
- [AI/ML optimization](#aiml-optimization)
- [CUDA automation](#cuda-automation)
- [Cloud automation](#cloud-automation)
- [Compiler automation](#compiler-automation)
- [Dashboard automation](#dashboard-automation)
- [Detection or installation of tools and artifacts](#detection-or-installation-of-tools-and-artifacts)
- [DevOps automation](#devops-automation)
- [Docker automation](#docker-automation)
- [MLCommons automation](#mlcommons-automation)
- [MLCommons interface](#mlcommons-interface)
- [MLCommons script templates](#mlcommons-script-templates)
- [MLCommons system utilities](#mlcommons-system-utilities)
- [MLCommons utilities](#mlcommons-utilities)
- [MLPerf Automotive](#mlperf-automotive)
- [MLPerf Inference](#mlperf-inference)
- [MLPerf Training](#mlperf-training)
- [Modular AI/ML application pipeline](#modular-aiml-application-pipeline)
- [Platform information](#platform-information)
- [Python automation](#python-automation)
- [ROCm automation](#rocm-automation)
- [Remote automation](#remote-automation)
- [Reproducibility and artifact evaluation](#reproducibility-and-artifact-evaluation)
- [Tests](#tests)
- [TinyML automation](#tinyml-automation)
- [Uncategorized](#uncategorized)
- [Utilities](#utilities)

---

## AI/ML datasets

- **[get-croissant](get-croissant/)**
  - get-croissant
  - Tags: `get`, `mlcommons`, `croissant`
- **[get-dataset-cifar10](get-dataset-cifar10/)**
  - get-dataset-cifar10
  - Tags: `get`, `dataset`, `cifar10`, `image-classification`, `validation`, `training`
- **[get-dataset-cnndm](get-dataset-cnndm/)**
  - get-dataset-cnndm
  - Tags: `get`, `dataset`, `gpt-j`, `cnndm`, `cnn-dailymail`, `original`
- **[get-dataset-coco](get-dataset-coco/)**
  - get-dataset-coco
  - Tags: `get`, `dataset`, `object-detection`, `coco`
- **[get-dataset-coco2014](get-dataset-coco2014/)**
  - get-dataset-coco2014
  - Tags: `get`, `dataset`, `coco2014`, `object-detection`, `original`
- **[get-dataset-cognata-mlcommons](get-dataset-cognata-mlcommons/)**
  - get-dataset-cognata-mlcommons
  - Tags: `get`, `raw`, `dataset`, `cognata`, `mlcommons-cognata`, `ml-task--object-detection`, `ml-task--image-segmentation`
- **[get-dataset-criteo](get-dataset-criteo/)**
  - get-dataset-criteo
  - Tags: `get`, `dataset`, `criteo`, `original`
- **[get-dataset-imagenet-aux](get-dataset-imagenet-aux/)**
  - get-dataset-imagenet-aux
  - Tags: `get`, `aux`, `dataset-aux`, `image-classification`, `imagenet-aux`
- **[get-dataset-imagenet-calibration](get-dataset-imagenet-calibration/)**
  - get-dataset-imagenet-calibration
  - Tags: `get`, `dataset`, `imagenet`, `calibration`
- **[get-dataset-imagenet-helper](get-dataset-imagenet-helper/)**
  - get-dataset-imagenet-helper
  - Tags: `get`, `imagenet`, `helper`, `imagenet-helper`
- **[get-dataset-imagenet-train](get-dataset-imagenet-train/)**
  - get-dataset-imagenet-train
  - Tags: `get`, `imagenet`, `train`, `dataset`, `original`
- **[get-dataset-imagenet-val](get-dataset-imagenet-val/)**
  - get-dataset-imagenet-val
  - Tags: `get`, `val`, `validation`, `dataset`, `imagenet`, `ILSVRC`, `image-classification`, `original`
- **[get-dataset-kits19](get-dataset-kits19/)**
  - get-dataset-kits19
  - Tags: `get`, `dataset`, `medical-imaging`, `kits`, `original`, `kits19`
- **[get-dataset-librispeech](get-dataset-librispeech/)**
  - get-dataset-librispeech
  - Tags: `get`, `dataset`, `speech`, `speech-recognition`, `librispeech`, `validation`, `audio`, `training`, `original`
- **[get-dataset-mlperf-inference-mixtral](get-dataset-mlperf-inference-mixtral/)**
  - get-dataset-mlperf-inference-mixtral
  - Tags: `get`, `dataset-mixtral`, `openorca-mbxp-gsm8k-combined`
- **[get-dataset-openimages](get-dataset-openimages/)**
  - get-dataset-openimages
  - Tags: `get`, `dataset`, `openimages`, `open-images`, `object-detection`, `original`
- **[get-dataset-openimages-annotations](get-dataset-openimages-annotations/)**
  - get-dataset-openimages-annotations
  - Tags: `get`, `aux`, `dataset-aux`, `object-detection`, `openimages`, `annotations`
- **[get-dataset-openimages-calibration](get-dataset-openimages-calibration/)**
  - get-dataset-openimages-calibration
  - Tags: `get`, `dataset`, `openimages`, `calibration`
- **[get-dataset-openorca](get-dataset-openorca/)**
  - get-dataset-openorca
  - Tags: `get`, `dataset`, `openorca`, `language-processing`, `original`
- **[get-dataset-squad](get-dataset-squad/)**
  - get-dataset-squad
  - Tags: `get`, `dataset`, `squad`, `language-processing`, `validation`, `original`
- **[get-dataset-squad-vocab](get-dataset-squad-vocab/)**
  - get-dataset-squad-vocab
  - Tags: `get`, `aux`, `squad`, `dataset-aux`, `language-processing`, `squad-aux`, `vocab`, `squad-vocab`
- **[get-preprocessed-dataset-cognata](get-preprocessed-dataset-cognata/)**
  - get-preprocessed-dataset-cognata
  - Tags: `get`, `dataset`, `cognata`, `preprocessed`
- **[get-preprocessed-dataset-criteo](get-preprocessed-dataset-criteo/)**
  - get-preprocessed-dataset-criteo
  - Tags: `get`, `dataset`, `criteo`, `recommendation`, `dlrm`, `preprocessed`
- **[get-preprocessed-dataset-generic](get-preprocessed-dataset-generic/)** (alias: `get-preprocesser-script-generic`)
  - get-preprocessed-dataset-generic
  - Tags: `get`, `preprocessor`, `generic`, `image-preprocessor`, `script`
- **[get-preprocessed-dataset-imagenet](get-preprocessed-dataset-imagenet/)**
  - get-preprocessed-dataset-imagenet
  - Tags: `get`, `dataset`, `imagenet`, `ILSVRC`, `image-classification`, `preprocessed`
- **[get-preprocessed-dataset-kits19](get-preprocessed-dataset-kits19/)**
  - get-preprocessed-dataset-kits19
  - Tags: `get`, `dataset`, `medical-imaging`, `kits19`, `preprocessed`
- **[get-preprocessed-dataset-librispeech](get-preprocessed-dataset-librispeech/)**
  - get-preprocessed-dataset-librispeech
  - Tags: `get`, `dataset`, `speech-recognition`, `librispeech`, `preprocessed`
- **[get-preprocessed-dataset-nuscenes](get-preprocessed-dataset-nuscenes/)**
  - get-preprocessed-dataset-nuscenes
  - Tags: `get`, `dataset`, `nuscenes`, `preprocessed`
- **[get-preprocessed-dataset-openimages](get-preprocessed-dataset-openimages/)**
  - get-preprocessed-dataset-openimages
  - Tags: `get`, `dataset`, `openimages`, `open-images`, `object-detection`, `preprocessed`
- **[get-preprocessed-dataset-openorca](get-preprocessed-dataset-openorca/)**
  - get-preprocessed-dataset-openorca
  - Tags: `get`, `dataset`, `openorca`, `language-processing`, `preprocessed`
- **[get-preprocessed-dataset-squad](get-preprocessed-dataset-squad/)**
  - get-preprocessed-dataset-squad
  - Tags: `get`, `dataset`, `preprocessed`, `tokenized`, `squad`

## AI/ML frameworks

- **[get-google-saxml](get-google-saxml/)**
  - get-google-saxml
  - Tags: `get`, `google`, `saxml`
- **[get-onnxruntime-prebuilt](get-onnxruntime-prebuilt/)**
  - get-onnxruntime-prebuilt
  - Tags: `install`, `onnxruntime`, `get`, `prebuilt`, `lib`, `lang-c`, `lang-cpp`
- **[get-qaic-apps-sdk](get-qaic-apps-sdk/)**
  - get-qaic-apps-sdk
  - Tags: `get`, `detect`, `qaic`, `apps`, `sdk`, `apps-sdk`, `qaic-apps-sdk`
- **[get-qaic-platform-sdk](get-qaic-platform-sdk/)**
  - get-qaic-platform-sdk
  - Tags: `get`, `detect`, `qaic`, `platform`, `sdk`, `platform-sdk`, `qaic-platform-sdk`
- **[get-qaic-software-kit](get-qaic-software-kit/)**
  - get-qaic-software-kit
  - Tags: `get`, `qaic`, `software`, `kit`, `qaic-software-kit`
- **[get-rocm](get-rocm/)**
  - get-rocm
  - Tags: `get`, `rocm`, `get-rocm`
- **[get-tool-perf](get-tool-perf/)**
  - get-tool-perf
  - Tags: `tool`, `perf`, `get`, `perf-tool`
- **[get-tvm](get-tvm/)**
  - get-tvm
  - Tags: `get`, `tvm`, `get-tvm`
- **[install-qaic-compute-sdk-from-src](install-qaic-compute-sdk-from-src/)**
  - install-qaic-compute-sdk-from-src
  - Tags: `get`, `qaic`, `from.src`, `software`, `compute`, `compute-sdk`, `qaic-compute-sdk`, `sdk`
- **[install-rocm](install-rocm/)**
  - install-rocm
  - Tags: `install`, `rocm`, `install-rocm`
- **[install-tensorflow-for-c](install-tensorflow-for-c/)**
  - install-tensorflow-for-c
  - Tags: `install`, `tensorflow`, `lib`, `lang-c`
- **[install-tensorflow-from-src](install-tensorflow-from-src/)**
  - install-tensorflow-from-src
  - Tags: `get`, `install`, `tensorflow`, `lib`, `source`, `from-source`, `from-src`, `src`, `from.src`
- **[install-tflite-from-src](install-tflite-from-src/)**
  - install-tflite-from-src
  - Tags: `get`, `install`, `tflite-cmake`, `tensorflow-lite-cmake`, `from-src`

## AI/ML models

- **[convert-ml-model-huggingface-to-onnx](convert-ml-model-huggingface-to-onnx/)**
  - convert-ml-model-huggingface-to-onnx
  - Tags: `ml-model`, `model`, `huggingface-to-onnx`, `onnx`, `huggingface`, `convert`
- **[get-dlrm](get-dlrm/)**
  - get-dlrm
  - Tags: `get`, `src`, `dlrm`
- **[get-ml-model-3d-unet-kits19](get-ml-model-3d-unet-kits19/)**
  - get-ml-model-3d-unet-kits19
  - Tags: `get`, `ml-model`, `raw`, `3d-unet`, `kits19`, `medical-imaging`
- **[get-ml-model-abtf-ssd-pytorch](get-ml-model-abtf-ssd-pytorch/)**
  - get-ml-model-abtf-ssd-pytorch
  - Tags: `get`, `ml-model`, `abtf-ssd-pytorch`, `ssd`, `resnet50`, `cmc`
- **[get-ml-model-bert-base-squad](get-ml-model-bert-base-squad/)**
  - get-ml-model-bert-base-squad
  - Tags: `get`, `ml-model`, `raw`, `bert`, `bert-base`, `bert-squad`, `language`, `language-processing`
- **[get-ml-model-bert-large-squad](get-ml-model-bert-large-squad/)**
  - get-ml-model-bert-large-squad
  - Tags: `get`, `ml-model`, `raw`, `bert`, `bert-large`, `bert-squad`, `language`, `language-processing`
- **[get-ml-model-dlrm-terabyte](get-ml-model-dlrm-terabyte/)**
  - get-ml-model-dlrm-terabyte
  - Tags: `get`, `ml-model`, `dlrm`, `raw`, `terabyte`, `criteo-terabyte`, `criteo`, `recommendation`
- **[get-ml-model-efficientnet-lite](get-ml-model-efficientnet-lite/)**
  - get-ml-model-efficientnet-lite
  - Tags: `get`, `ml-model`, `efficientnet`, `raw`, `ml-model-efficientnet`, `ml-model-efficientnet-lite`, `lite`, `tflite`, `image-classification`
- **[get-ml-model-gptj](get-ml-model-gptj/)**
  - get-ml-model-gptj
  - Tags: `get`, `raw`, `ml-model`, `gptj`, `gpt-j`, `large-language-model`
- **[get-ml-model-huggingface-zoo](get-ml-model-huggingface-zoo/)**
  - get-ml-model-huggingface-zoo
  - Tags: `get`, `ml-model`, `model`, `zoo`, `raw`, `model-zoo`, `huggingface`
- **[get-ml-model-llama2](get-ml-model-llama2/)**
  - get-ml-model-llama2
  - Tags: `get`, `raw`, `ml-model`, `language-processing`, `llama2`, `llama2-70b`, `text-summarization`
- **[get-ml-model-llama3](get-ml-model-llama3/)**
  - get-ml-model-llama3
  - Tags: `get`, `raw`, `ml-model`, `language-processing`, `llama3`, `llama3-405b`
- **[get-ml-model-mixtral](get-ml-model-mixtral/)**
  - get-ml-model-mixtral
  - Tags: `get`, `raw`, `ml-model`, `language-processing`, `mixtral`, `mixtral-8x7b`
- **[get-ml-model-mobilenet](get-ml-model-mobilenet/)**
  - get-ml-model-mobilenet
  - Tags: `get`, `ml-model`, `mobilenet`, `raw`, `ml-model-mobilenet`, `image-classification`
- **[get-ml-model-neuralmagic-zoo](get-ml-model-neuralmagic-zoo/)**
  - get-ml-model-neuralmagic-zoo
  - Tags: `get`, `ml-model`, `model`, `zoo`, `deepsparse`, `model-zoo`, `sparse-zoo`, `neuralmagic`, `neural-magic`
- **[get-ml-model-resnet50](get-ml-model-resnet50/)**
  - get-ml-model-resnet50
  - Tags: `get`, `raw`, `ml-model`, `resnet50`, `ml-model-resnet50`, `image-classification`
- **[get-ml-model-retinanet](get-ml-model-retinanet/)**
  - get-ml-model-retinanet
  - Tags: `get`, `ml-model`, `raw`, `resnext50`, `retinanet`, `object-detection`
- **[get-ml-model-retinanet-nvidia](get-ml-model-retinanet-nvidia/)**
  - get-ml-model-retinanet-nvidia
  - Tags: `get`, `ml-model`, `nvidia-retinanet`, `nvidia`
- **[get-ml-model-rgat](get-ml-model-rgat/)**
  - get-ml-model-rgat
  - Tags: `get`, `raw`, `ml-model`, `rgat`
- **[get-ml-model-rnnt](get-ml-model-rnnt/)**
  - get-ml-model-rnnt
  - Tags: `get`, `ml-model`, `rnnt`, `raw`, `librispeech`, `speech-recognition`
- **[get-ml-model-stable-diffusion](get-ml-model-stable-diffusion/)**
  - get-ml-model-stable-diffusion
  - Tags: `get`, `raw`, `ml-model`, `stable-diffusion`, `sdxl`, `text-to-image`
- **[get-ml-model-tiny-resnet](get-ml-model-tiny-resnet/)**
  - get-ml-model-tiny-resnet
  - Tags: `get`, `raw`, `ml-model`, `resnet`, `pretrained`, `tiny`, `model`, `ic`, `ml-model-tiny-resnet`, `image-classification`
- **[get-ml-model-using-imagenet-from-model-zoo](get-ml-model-using-imagenet-from-model-zoo/)**
  - get-ml-model-using-imagenet-from-model-zoo
  - Tags: `get`, `ml-model`, `model-zoo`, `zoo`, `imagenet`, `image-classification`
- **[get-ml-model-whisper](get-ml-model-whisper/)**
  - get-ml-model-whisper
  - Tags: `get-ml-model-whisper`, `get`, `ml-model`, `whisper`, `speech-recognition`
- **[get-tvm-model](get-tvm-model/)**
  - get-tvm-model
  - Tags: `get`, `ml-model-tvm`, `tvm-model`

## AI/ML optimization

- **[calibrate-model-for.qaic](calibrate-model-for.qaic/)**
  - calibrate-model-for.qaic
  - Tags: `qaic`, `calibrate`, `profile`, `qaic-profile`, `qaic-calibrate`
- **[compile-model-for.qaic](compile-model-for.qaic/)**
  - compile-model-for.qaic
  - Tags: `qaic`, `compile`, `model`, `model-compile`, `qaic-compile`
- **[prune-bert-models](prune-bert-models/)**
  - prune-bert-models
  - Tags: `prune`, `bert-models`, `bert-prune`, `prune-bert-models`

## CUDA automation

- **[get-cuda](get-cuda/)**
  - get-cuda
  - Tags: `get`, `cuda`, `cuda-compiler`, `cuda-lib`, `toolkit`, `lib`, `nvcc`, `get-nvcc`, `get-cuda`, `46d133d9ef92422d`
- **[get-cuda-devices](get-cuda-devices/)**
  - get-cuda-devices
  - Tags: `get`, `cuda-devices`
- **[get-cudnn](get-cudnn/)**
  - get-cudnn
  - Tags: `get`, `cudnn`, `nvidia`
- **[get-tensorrt](get-tensorrt/)**
  - get-tensorrt
  - Tags: `get`, `tensorrt`, `nvidia`
- **[install-cuda-package-manager](install-cuda-package-manager/)**
  - install-cuda-package-manager
  - Tags: `install`, `package-manager`, `cuda`, `package-manager-cuda`, `install-pm-cuda`
- **[install-cuda-prebuilt](install-cuda-prebuilt/)**
  - install-cuda-prebuilt
  - Tags: `install`, `prebuilt`, `cuda`, `prebuilt-cuda`, `install-prebuilt-cuda`
- **[plug-prebuilt-cudnn-to-cuda](plug-prebuilt-cudnn-to-cuda/)**
  - plug-prebuilt-cudnn-to-cuda
  - Tags: `plug`, `prebuilt-cudnn`, `to-cuda`
- **[plug-prebuilt-cusparselt-to-cuda](plug-prebuilt-cusparselt-to-cuda/)**
  - plug-prebuilt-cusparselt-to-cuda
  - Tags: `plug`, `prebuilt-cusparselt`, `to-cuda`

## Cloud automation

- **[destroy-terraform](destroy-terraform/)**
  - destroy-terraform
  - Tags: `destroy`, `terraform`, `cmd`
- **[get-aws-cli](get-aws-cli/)**
  - get-aws-cli
  - Tags: `get`, `aws-cli`, `aws`, `cli`
- **[get-terraform](get-terraform/)**
  - get-terraform
  - Tags: `get`, `terraform`, `get-terraform`
- **[install-aws-cli](install-aws-cli/)**
  - install-aws-cli
  - Tags: `install`, `script`, `aws-cli`, `aws`, `cli`
- **[install-terraform-from-src](install-terraform-from-src/)**
  - install-terraform-from-src
  - Tags: `install`, `terraform`, `from-src`
- **[run-terraform](run-terraform/)**
  - run-terraform
  - Tags: `run`, `terraform`

## Compiler automation

- **[get-aocc](get-aocc/)**
  - Detect or install AOCC compiler
  - Tags: `compiler`, `get`, `aocc`
- **[get-aocl](get-aocl/)**
  - get-aocl
  - Tags: `get`, `lib`, `aocl`, `amd-optimized`, `amd`
- **[get-cl](get-cl/)**
  - Detect or install Microsoft C compiler
  - Tags: `get`, `cl`, `compiler`, `c-compiler`, `cpp-compiler`, `get-cl`
- **[get-compiler-flags](get-compiler-flags/)**
  - get-compiler-flags
  - Tags: `get`, `compiler-flags`
- **[get-compiler-rust](get-compiler-rust/)**
  - get-compiler-rust
  - Tags: `get`, `rust-compiler`
- **[get-gcc](get-gcc/)**
  - Detect or install GCC compiler
  - Tags: `get`, `gcc`, `compiler`, `c-compiler`, `cpp-compiler`, `get-gcc`
- **[get-go](get-go/)**
  - get-go
  - Tags: `get`, `tool`, `go`, `get-go`
- **[get-llvm](get-llvm/)**
  - Detect or install LLVM compiler
  - Tags: `get`, `llvm`, `compiler`, `c-compiler`, `cpp-compiler`, `get-llvm`
- **[get-oneapi](get-oneapi/)** (alias: `get-one-api`)
  - Detect or install OneAPI compiler
  - Tags: `get`, `oneapi`, `compiler`, `get-oneapi`
- **[get-profiler-uprof](get-profiler-uprof/)**
  - Detect or install AMD uprof
  - Tags: `get-uprof`, `get`, `uprof`, `uprof-profiler`
- **[install-diffusers-from-src](install-diffusers-from-src/)**
  - Build diffusers from sources
  - Tags: `install`, `get`, `src`, `from.src`, `diffusers`, `src-diffusers`
- **[install-gcc-src](install-gcc-src/)**
  - install-gcc-src
  - Tags: `install`, `src`, `gcc`, `src-gcc`
- **[install-gflags-from-src](install-gflags-from-src/)**
  - Build gflags from sources
  - Tags: `install`, `get`, `src`, `from.src`, `gflags`, `src-gflags`
- **[install-ipex-from-src](install-ipex-from-src/)**
  - Build IPEX from sources
  - Tags: `install`, `get`, `src`, `from.src`, `ipex`, `src-ipex`
- **[install-llvm-prebuilt](install-llvm-prebuilt/)**
  - Install prebuilt LLVM compiler
  - Tags: `install`, `prebuilt`, `llvm`, `prebuilt-llvm`, `install-prebuilt-llvm`
- **[install-llvm-src](install-llvm-src/)**
  - Build LLVM compiler from sources (can take >30 min)
  - Tags: `install`, `src`, `llvm`, `from.src`, `src-llvm`
- **[install-onednn-from-src](install-onednn-from-src/)**
  - Build oneDNN from sources
  - Tags: `install`, `get`, `src`, `from.src`, `onednn`, `src-onednn`
- **[install-onnxruntime-from-src](install-onnxruntime-from-src/)**
  - Build onnxruntime from sources
  - Tags: `install`, `get`, `src`, `from.src`, `onnxruntime`, `src-onnxruntime`
- **[install-opencv-from-src](install-opencv-from-src/)**
  - Build opencv from sources
  - Tags: `install`, `get`, `src`, `from.src`, `opencv`, `opencv`, `src-opencv`
- **[install-pytorch-from-src](install-pytorch-from-src/)**
  - Build pytorch from sources
  - Tags: `install`, `get`, `src`, `from-src`, `from.src`, `pytorch`, `src-pytorch`
- **[install-pytorch-kineto-from-src](install-pytorch-kineto-from-src/)**
  - Build pytorch kineto from sources
  - Tags: `install`, `get`, `src`, `from.src`, `pytorch-kineto`, `kineto`, `src-pytorch-kineto`
- **[install-rapidjson-from-src](install-rapidjson-from-src/)**
  - Build rapidjson from sources
  - Tags: `install`, `get`, `src`, `from.src`, `rapidjson`, `src-rapidjson`
- **[install-torchvision-from-src](install-torchvision-from-src/)**
  - Build pytorchvision from sources
  - Tags: `install`, `get`, `src`, `from.src`, `pytorchvision`, `torchvision`, `src-pytorchvision`
- **[install-tpp-pytorch-extension](install-tpp-pytorch-extension/)**
  - Build TPP-PEX from sources
  - Tags: `install`, `get`, `src`, `from.src`, `tpp-pex`, `src-tpp-pex`
- **[install-transformers-from-src](install-transformers-from-src/)**
  - Build transformers from sources
  - Tags: `install`, `src`, `from.src`, `transformers`, `src-transformers`
- **[install-vllm-from-src](install-vllm-from-src/)**
  - Build vllm from sources
  - Tags: `install-vllm-from-src`

## Dashboard automation

- **[publish-results-to-dashboard](publish-results-to-dashboard/)**
  - publish-results-to-dashboard
  - Tags: `publish-results`, `dashboard`

## Detection or installation of tools and artifacts

- **[get-android-sdk](get-android-sdk/)**
  - get-android-sdk
  - Tags: `get`, `android`, `sdk`, `android-sdk`
- **[get-apptainer](get-apptainer/)**
  - get-apptainer
  - Tags: `get-apptainer`
- **[get-aria2](get-aria2/)**
  - get-aria2
  - Tags: `get`, `aria2`, `get-aria2`
- **[get-bazel](get-bazel/)**
  - get-bazel
  - Tags: `get`, `bazel`, `get-bazel`
- **[get-blis](get-blis/)**
  - get-blis
  - Tags: `get`, `lib`, `blis`
- **[get-brew](get-brew/)**
  - get-brew
  - Tags: `get`, `brew`
- **[get-cmake](get-cmake/)**
  - get-cmake
  - Tags: `get`, `cmake`, `get-cmake`
- **[get-cmsis_5](get-cmsis_5/)**
  - get-cmsis_5
  - Tags: `get`, `cmsis`, `cmsis_5`, `arm-software`
- **[get-docker](get-docker/)**
  - get-docker
  - Tags: `get`, `install`, `docker`, `engine`
- **[get-generic-sys-util](get-generic-sys-util/)**
  - get-generic-sys-util
  - Tags: `get`, `sys-util`, `generic`, `generic-sys-util`
- **[get-google-test](get-google-test/)**
  - get-google-test
  - Tags: `get`, `google-test`, `googletest`, `gtest`, `test`, `google`
- **[get-java](get-java/)**
  - get-java
  - Tags: `get`, `java`
- **[get-javac](get-javac/)**
  - get-javac
  - Tags: `get`, `javac`
- **[get-lib-armnn](get-lib-armnn/)**
  - get-lib-armnn
  - Tags: `get`, `lib-armnn`, `lib`, `armnn`
- **[get-lib-armpl](get-lib-armpl/)**
  - get-lib-armpl
  - Tags: `armpl`, `lib`, `get`, `arm`
- **[get-lib-dnnl](get-lib-dnnl/)**
  - get-lib-dnnl
  - Tags: `get`, `lib-dnnl`, `lib`, `dnnl`
- **[get-lib-jemalloc](get-lib-jemalloc/)**
  - get-lib-jemalloc
  - Tags: `get`, `lib`, `lib-jemalloc`, `jemalloc`
- **[get-lib-mimalloc](get-lib-mimalloc/)**
  - get-lib-mimalloc
  - Tags: `get-lib-mimalloc`, `get`, `lib`, `mimalloc`
- **[get-lib-protobuf](get-lib-protobuf/)**
  - get-lib-protobuf
  - Tags: `get`, `google-protobuf`, `protobuf`, `lib`, `lib-protobuf`, `google`
- **[get-lib-qaic-api](get-lib-qaic-api/)**
  - get-lib-qaic-api
  - Tags: `get`, `api`, `lib-qaic-api`, `lib`, `qaic`
- **[get-lib-tcmalloc](get-lib-tcmalloc/)**
  - get-lib-tcmalloc
  - Tags: `tcmalloc`, `get`, `lib`
- **[get-nvidia-docker](get-nvidia-docker/)**
  - get-nvidia-docker
  - Tags: `get`, `install`, `nvidia`, `nvidia-container-toolkit`, `nvidia-docker`, `engine`
- **[get-openssl](get-openssl/)**
  - get-openssl
  - Tags: `get`, `openssl`, `lib`, `lib-openssl`
- **[get-rclone](get-rclone/)**
  - get-rclone
  - Tags: `get`, `rclone`
- **[get-sys-utils-min](get-sys-utils-min/)**
  - get-sys-utils-min
  - Tags: `get`, `sys-utils-min`
- **[get-sys-utils-mlc](get-sys-utils-mlc/)**
  - get-sys-utils-mlc
  - Tags: `get`, `sys-utils-cm`, `sys-utils-mlc`
- **[get-xilinx-sdk](get-xilinx-sdk/)**
  - get-xilinx-sdk
  - Tags: `get`, `xilinx`, `sdk`
- **[get-zendnn](get-zendnn/)**
  - get-zendnn
  - Tags: `get`, `zendnn`, `amd`, `from.src`
- **[install-apt-package](install-apt-package/)**
  - install-apt-package
  - Tags: `get`, `install`, `apt-package`, `package`
- **[install-bazel](install-bazel/)**
  - install-bazel
  - Tags: `install`, `script`, `bazel`
- **[install-cmake-prebuilt](install-cmake-prebuilt/)**
  - install-cmake-prebuilt
  - Tags: `install`, `prebuilt`, `cmake`, `prebuilt-cmake`, `install-prebuilt-cmake`
- **[install-gflags](install-gflags/)**
  - install-gflags
  - Tags: `install`, `src`, `get`, `gflags`
- **[install-github-cli](install-github-cli/)**
  - install-github-cli
  - Tags: `install`, `gh`, `github`, `cli`, `github-cli`
- **[install-intel-neural-speed-from-src](install-intel-neural-speed-from-src/)**
  - Build Intel Neural Speed from sources
  - Tags: `install`, `src`, `from.src`, `neural-speed`, `intel-neural-speed`
- **[install-numactl-from-src](install-numactl-from-src/)**
  - Build numactl from sources
  - Tags: `install`, `src`, `from.src`, `numactl`, `src-numactl`
- **[install-openssl](install-openssl/)**
  - install-openssl
  - Tags: `install`, `src`, `openssl`, `openssl-lib`

## DevOps automation

- **[benchmark-program](benchmark-program/)**
  - benchmark-program
  - Tags: `program`, `benchmark`, `benchmark-program`
- **[compile-program](compile-program/)**
  - compile-program
  - Tags: `compile`, `program`, `c-program`, `cpp-program`, `compile-program`, `compile-c-program`, `compile-cpp-program`
- **[convert-csv-to-md](convert-csv-to-md/)**
  - convert-csv-to-md
  - Tags: `csv-to-md`, `convert`, `to-md`, `from-csv`
- **[copy-to-clipboard](copy-to-clipboard/)**
  - copy-to-clipboard
  - Tags: `copy`, `to`, `clipboard`, `copy-to-clipboard`
- **[create-conda-env](create-conda-env/)**
  - create-conda-env
  - Tags: `create`, `get`, `env`, `conda-env`, `conda-environment`, `create-conda-environment`
- **[create-patch](create-patch/)**
  - create-patch
  - Tags: `create`, `patch`
- **[detect-sudo](detect-sudo/)**
  - detect-sudo
  - Tags: `detect`, `sudo`, `access`
- **[download-and-extract](download-and-extract/)**
  - download-and-extract
  - Tags: `dae`, `file`, `download-and-extract`
- **[download-file](download-file/)**
  - download-file
  - Tags: `download`, `file`, `download-file`
- **[download-torrent](download-torrent/)**
  - download-torrent
  - Tags: `download`, `torrent`, `download-torrent`
- **[extract-file](extract-file/)**
  - extract-file
  - Tags: `extract`, `file`, `extract-file`
- **[fail](fail/)**
  - fail
  - Tags: `fail`, `filter`
- **[get-conda](get-conda/)**
  - get-conda
  - Tags: `get`, `conda`, `get-conda`
- **[get-git-repo](get-git-repo/)**
  - get-git-repo
  - Tags: `get`, `git`, `repo`, `repository`, `clone`
- **[get-github-cli](get-github-cli/)**
  - get-github-cli
  - Tags: `get`, `gh`, `gh-cli`, `github`, `cli`, `github-cli`
- **[get-huggingface-cli](get-huggingface-cli/)**
  - get-huggingface-cli
  - Tags: `get`, `huggingface`, `hf-cli`, `huggingface-cli`, `cli`
- **[pull-git-repo](pull-git-repo/)**
  - pull-git-repo
  - Tags: `pull`, `git`, `repo`, `repository`
- **[push-csv-to-spreadsheet](push-csv-to-spreadsheet/)**
  - push-csv-to-spreadsheet
  - Tags: `push`, `google-spreadsheet`, `spreadsheet`, `push-to-google-spreadsheet`
- **[run-vllm-server](run-vllm-server/)**
  - run-vllm-server
  - Tags: `run`, `server`, `vllm`, `vllm-server`
- **[set-device-settings-qaic](set-device-settings-qaic/)**
  - set-device-settings-qaic
  - Tags: `set`, `device`, `qaic`, `ai100`, `cloud`, `performance`, `power`, `setting`, `mode`, `vc`, `ecc`
- **[set-echo-off-win](set-echo-off-win/)**
  - set-echo-off-win
  - Tags: `set`, `echo`, `off`, `win`, `echo-off-win`, `echo-off`
- **[set-performance-mode](set-performance-mode/)**
  - set-performance-mode
  - Tags: `set`, `system`, `performance`, `power`, `mode`
- **[set-sqlite-dir](set-sqlite-dir/)**
  - set-sqlite-dir
  - Tags: `set`, `sqlite`, `dir`, `sqlite-dir`
- **[tar-my-folder](tar-my-folder/)**
  - tar-my-folder
  - Tags: `run`, `tar`

## Docker automation

- **[build-docker-image](build-docker-image/)**
  - build-docker-image
  - Tags: `build`, `docker`, `image`, `docker-image`, `dockerimage`
- **[build-dockerfile](build-dockerfile/)**
  - build-dockerfile
  - Tags: `build`, `dockerfile`
- **[prune-docker](prune-docker/)**
  - prune-docker
  - Tags: `prune`, `docker`
- **[run-docker-container](run-docker-container/)**
  - run-docker-container
  - Tags: `run`, `docker`, `container`

## MLCommons automation

- **[create-custom-cache-entry](create-custom-cache-entry/)**
  - create-custom-cache-entry
  - Tags: `create`, `custom`, `cache`, `entry`

## MLCommons interface

- **[get-cache-dir](get-cache-dir/)**
  - get-cache-dir
  - Tags: `get`, `cache`, `dir`, `directory`

## MLCommons script templates

- **[gemini_call](gemini_call/)**
  - gemini_call
  - Tags: `gemini-call`, `query`
- **[get-multilib](get-multilib/)**
  - get-multilib
  - Tags: `get-multilib`, `multilib`, `get`
- **[kill-process](kill-process/)**
  - kill-process
  - Tags: `kill`, `process`
- **[openai-call](openai-call/)**
  - openai-call
  - Tags: `query`, `openai`, `openai-call`, `call`
- **[template-script](template-script/)**
  - template-script
  - Tags: `generic`, `template`

## MLCommons system utilities

- **[set-cpu-frequency](set-cpu-frequency/)**
  - set-cpu-frequency
  - Tags: `set`, `cpu`, `target`, `freq`, `frequency`

## MLCommons utilities

- **[get-tool-intel-pin](get-tool-intel-pin/)**
  - get-tool-intel-pin
  - Tags: `get-intel-pin-tool`, `get`, `intel`, `pin-tool`, `pin`
- **[get-tool-intel-sde](get-tool-intel-sde/)**
  - get-tool-intel-sde
  - Tags: `get-intel-sde-tool`, `get`, `intel`, `sde`, `tool`, `sde-tool`
- **[parse-dmidecode-memory-info](parse-dmidecode-memory-info/)**
  - parse-dmidecode-memory-info
  - Tags: `dmidecode`, `parse`, `memory`, `info`

## MLPerf Automotive

- **[app-mlperf-automotive](app-mlperf-automotive/)**
  - app-mlperf-automotive
  - Tags: `app`, `app-mlperf-inference`, `app-mlperf-inference-automotive`, `mlperf-inference`, `mlperf-inference-automotive`, `abtf-inference`
- **[app-mlperf-automotive-mlcommons-python](app-mlperf-automotive-mlcommons-python/)**
  - app-mlperf-automotive-mlcommons-python
  - Tags: `automotive`, `mlcommons`, `reference`, `run-mlperf-inference`, `object-detection`, `abtf-model`, `demo`
- **[get-mlperf-automotive-scratch-space](get-mlperf-automotive-scratch-space/)**
  - get-mlperf-automotive-scratch-space
  - Tags: `get`, `abtf`, `inference`, `scratch`, `space`
- **[get-mlperf-automotive-src](get-mlperf-automotive-src/)**
  - get-mlperf-automotive-src
  - Tags: `get`, `src`, `source`, `automotive`, `automotive-src`, `automotive-source`, `mlperf`, `mlcommons`
- **[run-mlperf-automotive-app](run-mlperf-automotive-app/)**
  - run-mlperf-automotive-app
  - Tags: `run`, `run-abtf`, `run-abtf-inference`, `mlcommons`, `inference`, `reference`

## MLPerf Inference

- **[add-custom-nvidia-system](add-custom-nvidia-system/)**
  - add-custom-nvidia-system
  - Tags: `add`, `custom`, `system`, `nvidia`
- **[app-loadgen-generic-python](app-loadgen-generic-python/)**
  - app-loadgen-generic-python
  - Tags: `app`, `loadgen`, `generic`, `loadgen-generic`, `python`
- **[app-mlperf-inference](app-mlperf-inference/)**
  - app-mlperf-inference
  - Tags: `app`, `vision`, `language`, `mlcommons`, `mlperf`, `inference`, `generic`
- **[app-mlperf-inference-amd](app-mlperf-inference-amd/)**
  - app-mlperf-inference-amd
  - Tags: `reproduce`, `mlcommons`, `mlperf`, `inference`, `harness`, `amd-harness`, `amd`
- **[app-mlperf-inference-ctuning-cpp-tflite](app-mlperf-inference-ctuning-cpp-tflite/)**
  - app-mlperf-inference-ctuning-cpp-tflite
  - Tags: `app`, `mlcommons`, `mlperf`, `inference`, `tflite-cpp`
- **[app-mlperf-inference-dummy](app-mlperf-inference-dummy/)**
  - app-mlperf-inference-dummy
  - Tags: `reproduce`, `mlcommons`, `mlperf`, `inference`, `harness`, `dummy-harness`, `dummy`
- **[app-mlperf-inference-intel](app-mlperf-inference-intel/)**
  - app-mlperf-inference-intel
  - Tags: `reproduce`, `mlcommons`, `mlperf`, `inference`, `harness`, `intel-harness`, `intel`, `intel-harness`, `intel`
- **[app-mlperf-inference-mlcommons-cpp](app-mlperf-inference-mlcommons-cpp/)**
  - app-mlperf-inference-mlcommons-cpp
  - Tags: `app`, `mlcommons`, `mlperf`, `inference`, `cpp`
- **[app-mlperf-inference-mlcommons-python](app-mlperf-inference-mlcommons-python/)**
  - app-mlperf-inference-mlcommons-python
  - Tags: `app`, `vision`, `language`, `mlcommons`, `mlperf`, `inference`, `reference`, `ref`
- **[app-mlperf-inference-nvidia](app-mlperf-inference-nvidia/)**
  - app-mlperf-inference-nvidia
  - Tags: `reproduce`, `mlcommons`, `mlperf`, `inference`, `harness`, `nvidia-harness`, `nvidia`
- **[app-mlperf-inference-qualcomm](app-mlperf-inference-qualcomm/)**
  - app-mlperf-inference-qualcomm
  - Tags: `reproduce`, `mlcommons`, `mlperf`, `inference`, `harness`, `qualcomm-harness`, `qualcomm`, `kilt-harness`, `kilt`
- **[app-mlperf-inference-redhat](app-mlperf-inference-redhat/)**
  - app-mlperf-inference-redhat
  - Tags: `reproduce`, `mlcommons`, `mlperf`, `inference`, `harness`, `redhat-harness`, `redhat`
- **[benchmark-any-mlperf-inference-implementation](benchmark-any-mlperf-inference-implementation/)**
  - benchmark-any-mlperf-inference-implementation
  - Tags: `benchmark`, `run`, `natively`, `all`, `inference`, `any`, `mlperf`, `mlperf-implementation`, `implementation`, `mlperf-models`
- **[benchmark-program-mlperf](benchmark-program-mlperf/)**
  - benchmark-program-mlperf
  - Tags: `mlperf`, `benchmark-mlperf`
- **[build-mlperf-inference-server-nvidia](build-mlperf-inference-server-nvidia/)**
  - build-mlperf-inference-server-nvidia
  - Tags: `build`, `mlcommons`, `mlperf`, `inference`, `inference-server`, `server`, `nvidia-harness`, `nvidia`
- **[generate-mlperf-inference-submission](generate-mlperf-inference-submission/)**
  - generate-mlperf-inference-submission
  - Tags: `generate`, `submission`, `mlperf`, `mlperf-inference`, `inference`, `mlcommons`, `inference-submission`, `mlperf-inference-submission`, `mlcommons-inference-submission`
- **[generate-mlperf-inference-user-conf](generate-mlperf-inference-user-conf/)**
  - generate-mlperf-inference-user-conf
  - Tags: `generate`, `mlperf`, `inference`, `user-conf`, `inference-user-conf`
- **[get-mlperf-endpoints-src](get-mlperf-endpoints-src/)**
  - get-mlperf-endpoints-src
  - Tags: `get-mlperf-endpoints-src`
- **[get-mlperf-inference-intel-scratch-space](get-mlperf-inference-intel-scratch-space/)**
  - get-mlperf-inference-intel-scratch-space
  - Tags: `get`, `mlperf`, `inference`, `intel`, `scratch`, `space`
- **[get-mlperf-inference-loadgen](get-mlperf-inference-loadgen/)**
  - get-mlperf-inference-loadgen
  - Tags: `get`, `loadgen`, `inference`, `inference-loadgen`, `mlperf`, `mlcommons`
- **[get-mlperf-inference-nvidia-common-code](get-mlperf-inference-nvidia-common-code/)**
  - get-mlperf-inference-nvidia-common-code
  - Tags: `get`, `nvidia`, `mlperf`, `inference`, `common-code`
- **[get-mlperf-inference-nvidia-scratch-space](get-mlperf-inference-nvidia-scratch-space/)**
  - get-mlperf-inference-nvidia-scratch-space
  - Tags: `get`, `mlperf`, `inference`, `nvidia`, `scratch`, `space`
- **[get-mlperf-inference-results](get-mlperf-inference-results/)**
  - get-mlperf-inference-results
  - Tags: `get`, `results`, `inference`, `official`, `inference-results`, `mlcommons`, `mlperf`
- **[get-mlperf-inference-results-dir](get-mlperf-inference-results-dir/)**
  - get-mlperf-inference-results-dir
  - Tags: `get`, `mlperf`, `inference`, `local`, `results`, `dir`, `directory`
- **[get-mlperf-inference-src](get-mlperf-inference-src/)**
  - get-mlperf-inference-src
  - Tags: `get`, `src`, `source`, `inference`, `inference-src`, `inference-source`, `mlperf`, `mlcommons`
- **[get-mlperf-inference-submission-dir](get-mlperf-inference-submission-dir/)**
  - get-mlperf-inference-submission-dir
  - Tags: `get`, `mlperf`, `inference`, `submission`, `local`, `dir`, `directory`
- **[get-mlperf-inference-sut-configs](get-mlperf-inference-sut-configs/)**
  - get-mlperf-inference-sut-configs
  - Tags: `get`, `mlperf`, `inference`, `sut`, `configs`, `sut-configs`
- **[get-mlperf-inference-sut-description](get-mlperf-inference-sut-description/)**
  - get-mlperf-inference-sut-description
  - Tags: `get`, `mlperf`, `sut`, `description`, `system-under-test`, `system-description`
- **[get-mlperf-logging](get-mlperf-logging/)**
  - get-mlperf-logging
  - Tags: `get`, `mlperf`, `logging`, `mlperf-logging`
- **[get-mlperf-power-dev](get-mlperf-power-dev/)**
  - get-mlperf-power-dev
  - Tags: `get`, `src`, `source`, `power`, `power-dev`, `mlperf`, `mlcommons`
- **[get-nvidia-mitten](get-nvidia-mitten/)**
  - get-nvidia-mitten
  - Tags: `get`, `nvidia`, `mitten`, `nvidia-mitten`
- **[get-spec-ptd](get-spec-ptd/)**
  - get-spec-ptd
  - Tags: `get`, `spec`, `ptd`, `ptdaemon`, `power`, `daemon`, `power-daemon`, `mlperf`, `mlcommons`
- **[install-mlperf-logging-from-src](install-mlperf-logging-from-src/)**
  - install-mlperf-logging-from-src
  - Tags: `install`, `mlperf`, `logging`, `from.src`
- **[preprocess-mlperf-inference-submission](preprocess-mlperf-inference-submission/)**
  - preprocess-mlperf-inference-submission
  - Tags: `run`, `mlc`, `mlcommons`, `mlperf`, `inference`, `submission`, `mlperf-inference`, `processor`, `preprocessor`, `preprocess`
- **[process-mlperf-accuracy](process-mlperf-accuracy/)**
  - process-mlperf-accuracy
  - Tags: `run`, `mlperf`, `mlcommons`, `accuracy`, `mlc`, `process`, `process-accuracy`
- **[push-mlperf-inference-results-to-github](push-mlperf-inference-results-to-github/)**
  - push-mlperf-inference-results-to-github
  - Tags: `push`, `mlperf`, `mlperf-inference-results`, `publish-results`, `inference`, `submission`, `github`
- **[run-all-mlperf-models](run-all-mlperf-models/)**
  - run-all-mlperf-models
  - Tags: `run`, `natively`, `all`, `mlperf-models`
- **[run-mlperf-inference-app](run-mlperf-inference-app/)**
  - run-mlperf-inference-app
  - Tags: `run`, `common`, `generate-run-cmds`, `run-mlperf`, `run-mlperf-inference`, `vision`, `mlcommons`, `mlperf`, `inference`, `reference`
- **[run-mlperf-inference-mobilenet-models](run-mlperf-inference-mobilenet-models/)**
  - run-mlperf-inference-mobilenet-models
  - Tags: `run`, `mobilenet`, `models`, `image-classification`, `mobilenet-models`, `mlperf`, `inference`
- **[run-mlperf-inference-submission-checker](run-mlperf-inference-submission-checker/)**
  - run-mlperf-inference-submission-checker
  - Tags: `run`, `mlc`, `mlcommons`, `mlperf`, `inference`, `mlperf-inference`, `submission`, `checker`, `submission-checker`, `mlc-submission-checker`
- **[run-mlperf-power-client](run-mlperf-power-client/)**
  - run-mlperf-power-client
  - Tags: `run`, `mlc`, `mlcommons`, `mlperf`, `power`, `client`, `power-client`
- **[run-mlperf-power-server](run-mlperf-power-server/)**
  - run-mlperf-power-server
  - Tags: `run`, `mlc`, `mlcommons`, `mlperf`, `power`, `server`, `power-server`
- **[runtime-system-infos](runtime-system-infos/)**
  - runtime-system-infos
  - Tags: `runtime`, `system`, `utilisation`, `infos`
- **[submit-mlperf-results](submit-mlperf-results/)**
  - submit-mlperf-results
  - Tags: `submit`, `mlperf`, `results`, `mlperf-results`, `publish-results`, `submission`
- **[truncate-mlperf-inference-accuracy-log](truncate-mlperf-inference-accuracy-log/)**
  - truncate-mlperf-inference-accuracy-log
  - Tags: `run`, `mlc`, `mlcommons`, `mlperf`, `inference`, `mlperf-inference`, `truncation`, `truncator`, `truncate`, `accuracy`, `accuracy-log`, `accuracy-log-trancation`, `accuracy-log-truncator`, `mlc-accuracy-log-trancation`, `mlc-accuracy-log-truncator`

## MLPerf Training

- **[app-mlperf-training-nvidia](app-mlperf-training-nvidia/)**
  - app-mlperf-training-nvidia
  - Tags: `app`, `vision`, `language`, `mlcommons`, `mlperf`, `training`, `nvidia`
- **[app-mlperf-training-reference](app-mlperf-training-reference/)**
  - app-mlperf-training-reference
  - Tags: `app`, `vision`, `language`, `mlcommons`, `mlperf`, `training`, `reference`, `ref`
- **[get-mlperf-training-nvidia-code](get-mlperf-training-nvidia-code/)**
  - get-mlperf-training-nvidia-code
  - Tags: `get`, `nvidia`, `mlperf`, `training`, `code`, `training-code`
- **[get-mlperf-training-src](get-mlperf-training-src/)**
  - get-mlperf-training-src
  - Tags: `get`, `src`, `source`, `training`, `training-src`, `training-source`, `mlperf`, `mlcommons`
- **[prepare-training-data-bert](prepare-training-data-bert/)**
  - prepare-training-data-bert
  - Tags: `prepare`, `mlperf`, `training`, `data`, `input`, `bert`
- **[prepare-training-data-resnet](prepare-training-data-resnet/)**
  - prepare-training-data-resnet
  - Tags: `prepare`, `mlperf`, `training`, `data`, `input`, `resnet`
- **[reproduce-mlperf-training-nvidia](reproduce-mlperf-training-nvidia/)**
  - reproduce-mlperf-training-nvidia
  - Tags: `reproduce`, `mlcommons`, `mlperf`, `train`, `training`, `nvidia-training`, `nvidia`
- **[run-mlperf-training-submission-checker](run-mlperf-training-submission-checker/)**
  - run-mlperf-training-submission-checker
  - Tags: `run`, `mlc`, `mlcommons`, `mlperf`, `training`, `train`, `mlperf-training`, `submission`, `checker`, `submission-checker`, `mlc-submission-checker`

## Modular AI/ML application pipeline

- **[app-image-classification-onnx-py](app-image-classification-onnx-py/)**
  - app-image-classification-onnx-py
  - Tags: `app`, `modular`, `image-classification`, `onnx`, `python`
- **[app-image-classification-tf-onnx-cpp](app-image-classification-tf-onnx-cpp/)**
  - app-image-classification-tf-onnx-cpp
  - Tags: `app`, `image-classification`, `tf`, `tensorflow`, `tf-onnx`, `tensorflow-onnx`, `onnx`, `cpp`
- **[app-image-classification-torch-py](app-image-classification-torch-py/)**
  - app-image-classification-torch-py
  - Tags: `app`, `image-classification`, `torch`, `python`
- **[app-image-classification-tvm-onnx-py](app-image-classification-tvm-onnx-py/)**
  - app-image-classification-tvm-onnx-py
  - Tags: `app`, `image-classification`, `tvm-onnx`, `python`
- **[app-image-corner-detection](app-image-corner-detection/)**
  - app-image-corner-detection
  - Tags: `app`, `image`, `corner-detection`
- **[app-stable-diffusion-onnx-py](app-stable-diffusion-onnx-py/)**
  - app-stable-diffusion-onnx-py
  - Tags: `app`, `modular`, `stable`, `diffusion`, `stable-diffusion`, `onnx`, `python`

## Platform information

- **[detect-cpu](detect-cpu/)**
  - detect-cpu
  - Tags: `detect`, `cpu`, `detect-cpu`, `info`
- **[detect-os](detect-os/)**
  - detect-os
  - Tags: `detect-os`, `detect`, `os`, `info`
- **[get-platform-details](get-platform-details/)**
  - get-platform-details
  - Tags: `get`, `platform`, `details`, `platform-details`
- **[save-machine-state](save-machine-state/)**
  - save-machine-state
  - Tags: `machine-state`, `save`, `machine`, `system`, `system-state`, `state`

## Python automation

- **[activate-python-venv](activate-python-venv/)**
  - Activate virtual Python environment
  - Tags: `activate`, `python`, `activate-python-venv`, `python-venv`
- **[get-generic-python-lib](get-generic-python-lib/)**
  - get-generic-python-lib
  - Tags: `get`, `install`, `generic`, `pip-package`, `generic-python-lib`
- **[get-python3](get-python3/)**
  - get-python3
  - Tags: `get`, `python`, `python3`, `get-python`, `get-python3`
- **[install-generic-conda-package](install-generic-conda-package/)**
  - install-generic-conda-package
  - Tags: `get`, `install`, `generic`, `generic-conda-lib`, `conda-lib`, `conda-package`, `generic-conda-package`
- **[install-python-src](install-python-src/)**
  - install-python-src
  - Tags: `install`, `src`, `python`, `python3`, `src-python3`, `src-python`
- **[install-python-venv](install-python-venv/)**
  - install-python-venv
  - Tags: `install`, `python`, `get-python-venv`, `python-venv`

## ROCm automation

- **[get-rocm-devices](get-rocm-devices/)**
  - get-rocm-devices
  - Tags: `get`, `rocm-devices`

## Remote automation

- **[remote-run-commands](remote-run-commands/)**
  - remote-run-commands
  - Tags: `remote`, `run`, `cmds`, `remote-run`, `remote-run-cmds`, `ssh-run`, `ssh`

## Reproducibility and artifact evaluation

- **[get-ipol-src](get-ipol-src/)**
  - get-ipol-src
  - Tags: `get`, `ipol`, `journal`, `src`, `ipol-src`

## Tests

- **[run-python](run-python/)**
  - run-python
  - Tags: `run`, `python`
- **[upgrade-python-pip](upgrade-python-pip/)**
  - upgrade-python-pip
  - Tags: `upgrade`, `python`, `pip`, `python-pip`

## TinyML automation

- **[create-fpgaconvnet-app-tinyml](create-fpgaconvnet-app-tinyml/)**
  - create-fpgaconvnet-app-tinyml
  - Tags: `create`, `app`, `fpgaconvnet`
- **[create-fpgaconvnet-config-tinyml](create-fpgaconvnet-config-tinyml/)**
  - create-fpgaconvnet-config-tinyml
  - Tags: `create`, `config`, `fpgaconvnet`
- **[flash-tinyml-binary](flash-tinyml-binary/)**
  - flash-tinyml-binary
  - Tags: `flash`, `tiny`, `mlperf`, `mlcommons`
- **[generate-mlperf-tiny-report](generate-mlperf-tiny-report/)**
  - generate-mlperf-tiny-report
  - Tags: `generate`, `mlperf`, `tiny`, `mlperf-tiny`, `report`
- **[generate-mlperf-tiny-submission](generate-mlperf-tiny-submission/)**
  - generate-mlperf-tiny-submission
  - Tags: `generate`, `submission`, `mlperf`, `mlperf-tiny`, `tiny`, `mlcommons`, `tiny-submission`, `mlperf-tiny-submission`, `mlcommons-tiny-submission`
- **[get-microtvm](get-microtvm/)**
  - get-microtvm
  - Tags: `get`, `src`, `source`, `microtvm`, `tiny`
- **[get-mlperf-tiny-eembc-energy-runner-src](get-mlperf-tiny-eembc-energy-runner-src/)**
  - get-mlperf-tiny-eembc-energy-runner-src
  - Tags: `get`, `src`, `source`, `eembc`, `energyrunner`, `energy-runner`, `eembc-energy-runner`, `tinymlperf-energy-runner`
- **[get-mlperf-tiny-src](get-mlperf-tiny-src/)**
  - get-mlperf-tiny-src
  - Tags: `get`, `src`, `source`, `tiny`, `tiny-src`, `tiny-source`, `tinymlperf`, `tinymlperf-src`, `mlperf`, `mlcommons`
- **[get-zephyr](get-zephyr/)**
  - get-zephyr
  - Tags: `get`, `zephyr`
- **[get-zephyr-sdk](get-zephyr-sdk/)**
  - get-zephyr-sdk
  - Tags: `get`, `zephyr-sdk`
- **[reproduce-mlperf-octoml-tinyml-results](reproduce-mlperf-octoml-tinyml-results/)**
  - reproduce-mlperf-octoml-tinyml-results
  - Tags: `reproduce`, `tiny`, `results`, `mlperf`, `octoml`, `mlcommons`
- **[wrapper-reproduce-octoml-tinyml-submission](wrapper-reproduce-octoml-tinyml-submission/)**
  - wrapper-reproduce-octoml-tinyml-submission
  - Tags: `run`, `generate-tiny`, `generate`, `submission`, `tiny`, `generate-tiny-submission`, `results`, `mlcommons`, `mlperf`, `octoml`

## Uncategorized

- **[authenticate-github-cli](authenticate-github-cli/)**
  - authenticate-github-cli
  - Tags: `auth`, `authenticate`, `github`, `gh`, `cli`
- **[clean-nvidia-mlperf-inference-scratch-space](clean-nvidia-mlperf-inference-scratch-space/)**
  - clean-nvidia-mlperf-inference-scratch-space
  - Tags: `clean`, `nvidia`, `scratch`, `space`, `mlperf`, `inference`
- **[draw-graph-from-json-data](draw-graph-from-json-data/)**
  - draw-graph-from-json-data
  - Tags: `draw`, `graph`, `from-json`, `from-json-data`
- **[dump-pip-freeze](dump-pip-freeze/)**
  - dump-pip-freeze
  - Tags: `dump`, `pip`, `freeze`
- **[get-dataset-igbh](get-dataset-igbh/)**
  - get-dataset-igbh
  - Tags: `get`, `dataset`, `mlperf`, `rgat`, `igbh`, `inference`
- **[get-dataset-mlperf-inference-dlrmv3-synthetic-streaming](get-dataset-mlperf-inference-dlrmv3-synthetic-streaming/)**
  - get-dataset-mlperf-inference-dlrmv3-synthetic-streaming
  - Tags: `get`, `dataset`, `mlperf`, `inference`, `dlrmv3`, `synthetic-streaming`, `get-dataset-mlperf-inference-dlrmv3-synthetic-streaming`
- **[get-dataset-mlperf-inference-gpt-oss](get-dataset-mlperf-inference-gpt-oss/)**
  - get-dataset-mlperf-inference-gpt-oss
  - Tags: `get-dataset-mlperf-inference-gpt-oss`
- **[get-dataset-mlperf-inference-llama3](get-dataset-mlperf-inference-llama3/)**
  - get-dataset-mlperf-inference-llama3
  - Tags: `get`, `dataset`, `mlperf`, `llama3`, `inference`
- **[get-dataset-mlperf-inference-shopify-catalogue](get-dataset-mlperf-inference-shopify-catalogue/)**
  - get-dataset-mlperf-inference-shopify-catalogue
  - Tags: `get-dataset-mlperf-inference-shopify-catalogue`
- **[get-dataset-mlperf-inference-text-to-video](get-dataset-mlperf-inference-text-to-video/)**
  - get-dataset-mlperf-inference-text-to-video
  - Tags: `get-dataset-mlperf-inference-text-to-video`
- **[get-dataset-mlperf-inference-yolo-coco2017-filtered-dataset](get-dataset-mlperf-inference-yolo-coco2017-filtered-dataset/)**
  - get-dataset-mlperf-inference-yolo-coco2017-filtered-dataset
  - Tags: `get`, `dataset`, `mlperf-inference`, `yolo-coco2017-filtered`, `get-dataset-mlperf-inference-yolo-coco2017-filtered-dataset`
- **[get-dataset-nuscenes](get-dataset-nuscenes/)**
  - get-dataset-nuscenes
  - Tags: `get`, `dataset`, `nuscenes`
- **[get-dataset-waymo](get-dataset-waymo/)**
  - get-dataset-waymo
  - Tags: `get`, `dataset`, `waymo`
- **[get-dataset-waymo-calibration](get-dataset-waymo-calibration/)**
  - get-dataset-waymo-calibration
  - Tags: `get`, `waymo`, `dataset`, `calibration`
- **[get-dataset-whisper](get-dataset-whisper/)**
  - get-dataset-whisper
  - Tags: `get-dataset-whisper`, `get`, `dataset`, `whisper`
- **[get-dlrm-data-mlperf-inference](get-dlrm-data-mlperf-inference/)**
  - get-dlrm-data-mlperf-inference
  - Tags: `get`, `dlrm`, `data`, `mlperf`, `inference`
- **[get-gh-actions-runner](get-gh-actions-runner/)**
  - get-gh-actions-runner
  - Tags: `get`, `gh`, `github`, `actions-runner`, `runner-code`, `runner`, `code`, `gh-actions-runner`
- **[get-ml-model-bevformer](get-ml-model-bevformer/)**
  - get-ml-model-bevformer
  - Tags: `get`, `ml-model`, `bevformer`, `get-ml-model-bevformer`
- **[get-ml-model-deeplabv3_plus](get-ml-model-deeplabv3_plus/)** (alias: `get-ml-model-deeplabv3-plus`)
  - get-ml-model-deeplabv3_plus
  - Tags: `get`, `ml-model`, `deeplab`, `v3-plus`, `deeplabv3-plus`
- **[get-ml-model-deepseek-r1](get-ml-model-deepseek-r1/)**
  - get-ml-model-deepseek-r1
  - Tags: `get`, `ml-model`, `deepseek-r1`, `get-ml-model-deepseek-r1`
- **[get-ml-model-dlrm-v3](get-ml-model-dlrm-v3/)**
  - get-ml-model-dlrm-v3
  - Tags: `get`, `ml-model`, `dlrm-v3`, `get-ml-model-dlrm-v3`
- **[get-ml-model-gpt-oss](get-ml-model-gpt-oss/)**
  - get-ml-model-gpt-oss
  - Tags: `get-ml-model-gpt-oss`
- **[get-ml-model-pointpainting](get-ml-model-pointpainting/)** (alias: `get-ml-model-pointpillars`)
  - get-ml-model-pointpainting
  - Tags: `get`, `ml-model`, `ml`, `model`, `pointpainting`
- **[get-ml-model-qwen3-vlm](get-ml-model-qwen3-vlm/)**
  - get-ml-model-qwen3-vlm
  - Tags: `get-ml-model-qwen3-vl`
- **[get-ml-model-wan2](get-ml-model-wan2/)**
  - get-ml-model-wan2
  - Tags: `get-ml-model-wan2`
- **[get-ml-model-yolov11](get-ml-model-yolov11/)**
  - get-ml-model-yolov11
  - Tags: `get-ml-model-yolov11`
- **[get-mlperf-automotive-utils](get-mlperf-automotive-utils/)**
  - get-mlperf-automotive-utils
  - Tags: `get`, `mlperf`, `automotive`, `util`, `utils`, `functions`
- **[get-mlperf-inference-utils](get-mlperf-inference-utils/)**
  - get-mlperf-inference-utils
  - Tags: `get`, `mlperf`, `inference`, `util`, `utils`, `functions`
- **[get-preprocessed-dataset-mlperf-deepseek-r1](get-preprocessed-dataset-mlperf-deepseek-r1/)**
  - get-preprocessed-dataset-mlperf-deepseek-r1
  - Tags: `get`, `preprocessed`, `dataset`, `mlperf`, `deepseek-r1`, `mlperf-deepseek-r1`
- **[get-rclone-config](get-rclone-config/)**
  - get-rclone-config
  - Tags: `get`, `rclone-config`
- **[get-wkhtmltopdf](get-wkhtmltopdf/)**
  - get-wkhtmltopdf
  - Tags: `get`, `wkhtmltopdf`
- **[install-nccl-libs](install-nccl-libs/)**
  - install-nccl-libs
  - Tags: `install`, `nccl`, `libs`
- **[install-pip-package-for-mlc-python](install-pip-package-for-mlc-python/)**
  - install-pip-package-for-mlc-python
  - Tags: `install`, `pip`, `package`, `pip-package`, `for-mlc-python`, `for.mlc-python`
- **[save-mlperf-inference-implementation-state](save-mlperf-inference-implementation-state/)**
  - save-mlperf-inference-implementation-state
  - Tags: `save`, `mlperf`, `inference`, `implementation`, `state`
- **[set-user-limits](set-user-limits/)**
  - set-user-limits
  - Tags: `set`, `user`, `limits`, `limit`
- **[set-venv](set-venv/)**
  - set-venv
  - Tags: `set`, `venv`

## Utilities

- **[send-mail](send-mail/)**
  - send-mail
  - Tags: `send`, `mail`, `email`

---

## Statistics

- **Total Scripts**: 316
- **Categories**: 29

## Usage

These scripts are part of the MLCommons automation framework. To use them:

```bash
# Run a script using its alias
mlc run script <alias> [options]

# Or directly
cd <script-directory>
./run.sh [options]
```

For more information about each script, see the `meta.yaml` file in the script directory.
