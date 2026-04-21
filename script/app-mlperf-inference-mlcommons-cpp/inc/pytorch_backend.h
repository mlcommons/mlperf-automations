#ifndef PYTORCH_BACKEND_H_
#define PYTORCH_BACKEND_H_

#include <cstring>
#include <memory>
#include <vector>

#include <torch/script.h>
#include <torch/torch.h>

#include "loadgen.h"

#include "backend.h"

class PyTorchBackend : public MlcBackend {
public:
  PyTorchBackend(std::shared_ptr<Model> &model,
                 std::shared_ptr<MlcDevice> &device,
                 size_t performance_sample_count, size_t batch_size,
                 bool use_cuda)
      : MlcBackend(model, device, performance_sample_count, batch_size),
        use_cuda(use_cuda) {
    // Load TorchScript model for each concurrency
    for (size_t i = 0; i < device->NumConcurrency(); i++) {
      torch::jit::script::Module m = torch::jit::load(model->model_path);
      m.eval();
      if (use_cuda) {
        m.to(torch::Device(torch::kCUDA, i));
      }
      modules.push_back(std::move(m));
    }
  }

  void RunInference(size_t concurrency_index,
                    const std::vector<mlperf::QuerySample> &batch,
                    std::vector<void *> &batch_data) override {
    torch::NoGradGuard no_grad;

    torch::Device torch_device =
        use_cuda ? torch::Device(torch::kCUDA, concurrency_index)
                 : torch::Device(torch::kCPU);

    // Build input tensors
    std::vector<torch::jit::IValue> inputs;
    for (size_t i = 0; i < model->num_inputs; i++) {
      size_t sample_size = GetSampleSize(batch.front().index, i);
      size_t total_size = batch.size() * sample_size;
      const std::vector<size_t> &shape = GetSampleShape(batch.front().index, i);

      // Determine element type from input size and shape
      size_t num_elements = 1;
      for (size_t dim : shape)
        num_elements *= dim;
      size_t element_size = sample_size / num_elements;

      torch::ScalarType dtype;
      if (element_size == sizeof(float)) {
        dtype = torch::kFloat32;
      } else if (element_size == sizeof(int64_t)) {
        dtype = torch::kInt64;
      } else if (element_size == sizeof(int32_t)) {
        dtype = torch::kInt32;
      } else {
        dtype = torch::kFloat32;
      }

      // Build shape with batch dimension
      std::vector<int64_t> tensor_shape;
      tensor_shape.push_back(static_cast<int64_t>(batch.size()));
      for (size_t dim : shape)
        tensor_shape.push_back(static_cast<int64_t>(dim));

      // Create tensor from raw memory (on CPU first)
      torch::Tensor tensor =
          torch::from_blob(batch_data[i], tensor_shape, dtype).clone();

      if (use_cuda) {
        tensor = tensor.to(torch_device);
      }

      inputs.push_back(tensor);
    }

    // Run inference
    auto output = modules[concurrency_index].forward(inputs);

    // Process outputs
    std::vector<torch::Tensor> output_tensors;
    if (output.isTensor()) {
      output_tensors.push_back(output.toTensor().cpu().contiguous());
    } else if (output.isTuple()) {
      auto tuple = output.toTuple();
      for (const auto &elem : tuple->elements()) {
        output_tensors.push_back(elem.toTensor().cpu().contiguous());
      }
    } else if (output.isList()) {
      auto list = output.toTensorVector();
      for (auto &t : list) {
        output_tensors.push_back(t.cpu().contiguous());
      }
    }

    std::vector<mlperf::QuerySampleResponse> responses(batch.size());
    std::vector<std::vector<uint8_t>> response_buffers(batch.size());
    for (size_t i = 0; i < batch.size(); i++) {
      std::vector<void *> output_buffers(output_tensors.size());
      std::vector<std::vector<size_t>> output_shapes(output_tensors.size());

      for (size_t j = 0; j < output_tensors.size(); j++) {
        size_t elem_bytes = output_tensors[j].element_size();
        // Per-sample offset
        size_t per_sample_elements = 1;
        auto sizes = output_tensors[j].sizes();
        for (size_t k = 1; k < sizes.size(); k++)
          per_sample_elements *= sizes[k];
        output_buffers[j] =
            static_cast<uint8_t *>(output_tensors[j].data_ptr()) +
            i * per_sample_elements * elem_bytes;

        output_shapes[j].resize(sizes.size());
        for (size_t k = 0; k < sizes.size(); k++)
          output_shapes[j][k] = sizes[k];
      }

      model->PostProcess(batch[i].index, output_buffers, output_shapes,
                         response_buffers[i]);

      responses[i].id = batch[i].id;
      responses[i].data =
          reinterpret_cast<uintptr_t>(response_buffers[i].data());
      responses[i].size = response_buffers[i].size();
    }

    mlperf::QuerySamplesComplete(responses.data(), responses.size());
  }

private:
  std::vector<torch::jit::script::Module> modules;
  bool use_cuda;
};

#endif // PYTORCH_BACKEND_H_
