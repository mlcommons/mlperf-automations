# README for get-generic-python-lib
This README is automatically generated. Add custom content in [info.md](info.md). Please follow the [script execution document](https://docs.mlcommons.org/mlcflow/targets/script/execution-flow/) to understand more about the MLC script execution.

`mlcflow` stores all local data under `$HOME/MLC` by default. So, if there is space constraint on the home directory and you have more space on say `/mnt/$USER`, you can do
```
mkdir /mnt/$USER/MLC
ln -s /mnt/$USER/MLC $HOME/MLC
```
You can also use the `ENV` variable `MLC_REPOS` to control this location but this will need a set after every system reboot.

## Setup

If you are not on a Python development environment please refer to the [official docs](https://docs.mlcommons.org/mlcflow/install/) for the installation.

```bash
python3 -m venv mlcflow
. mlcflow/bin/activate
pip install mlcflow
```

- Using a virtual environment is recommended (per `pip` best practices), but you may skip it or use `--break-system-packages` if needed.

### Pull mlperf-automations

Once `mlcflow` is installed:

```bash
mlc pull repo mlcommons@mlperf-automations --pat=<Your Private Access Token>
```
- `--pat` or `--ssh` is only needed if the repo is PRIVATE
- If `--pat` is avoided, you'll be asked to enter the password where you can enter your Private Access Token
- `--ssh` option can be used instead of `--pat=<>` option if you prefer to use SSH for accessing the github repository.
## Run Commands

```bash
mlcr get generic-python-lib
```

### Script Inputs

| Name | Description | Choices | Default |
|------|-------------|---------|------|
| `--extra_index_url` |  |  | `` |
| `--force_install` |  |  | `` |
| `--index_url` |  |  | `` |
### Generic Script Inputs

| Name | Description | Choices | Default |
|------|-------------|---------|------|
| `--input` | Input to the script passed using the env key `MLC_INPUT` |  | `` |
| `--output` | Output from the script passed using the env key `MLC_OUTPUT` |  | `` |
| `--outdirname` | The directory to store the script output |  | `cache directory ($HOME/MLC/repos/local/cache/<>) if the script is cacheable or else the current directory` |
| `--outbasename` | The output file/folder name |  | `` |
| `--name` |  |  | `` |
| `--extra_cache_tags` | Extra cache tags to be added to the cached entry when the script results are saved |  | `` |
| `--skip_compile` | Skip compilation |  | `False` |
| `--skip_run` | Skip run |  | `False` |
| `--accept_license` | Accept the required license requirement to run the script |  | `False` |
| `--skip_system_deps` | Skip installing any system dependencies |  | `False` |
| `--git_ssh` | Use SSH for git repos |  | `False` |
| `--gh_token` | Github Token |  | `` |
| `--hf_token` | Huggingface Token |  | `` |
| `--verify_ssl` | Verify SSL |  | `False` |
## Variations

### Ungrouped

- `Pillow`
- `anthropic`
- `apache-tvm`
- `apex`
- `async_timeout`
- `attr`
- `attrs`
- `boto3`
- `cloudpickle`
- `cmind`
- `colored`
- `conda.#` _(# can be substituted dynamically)_
- `cupy`
- `custom-python`
- `cxx11-abi`
- `datasets`
- `decorator`
- `deepsparse`
- `dllogger`
- `extra-index-url.#` _(# can be substituted dynamically)_
- `fiftyone`
- `find_links_url.#` _(# can be substituted dynamically)_
- `google-api-python-client`
- `google-auth-oauthlib`
- `google-generativeai`
- `groq`
- `huggingface_hub`
- `index-url.#` _(# can be substituted dynamically)_
- `inflect`
- `jax`
- `jax_cuda`
- `librosa`
- `matplotlib`
- `mlperf_loadgen`
- `mlperf_logging`
- `mpld3`
- `mxeval`
- `nibabel`
- `no-deps`
- `numpy`
- `nvidia-apex`
- `nvidia-apex-from-src`
- `nvidia-dali`
- `nvidia-pycocotools` (base: pycocotools)
- `nvidia-pyindex`
- `nvidia-tensorrt`
- `onnx`
- `onnx-graphsurgeon`
- `onnxruntime`
- `onnxruntime_gpu`
- `openai`
- `opencv-python`
- `package.#` _(# can be substituted dynamically)_
- `pandas`
- `path.#` _(# can be substituted dynamically)_
- `pdfplumber`
- `pillow`
- `pip`
- `polygraphy`
- `pre`
- `protobuf`
- `psutil`
- `pycocotools`
- `pycuda`
- `python-dotenv`
- `quark-amd`
- `ray`
- `requests`
- `rocm`
- `safetensors`
- `scikit-learn`
- `scipy`
- `scons`
- `setfit`
- `setuptools`
- `six`
- `sklearn`
- `sox`
- `sparsezoo`
- `streamlit`
- `streamlit_option_menu`
- `tensorboard`
- `tensorflow`
- `tensorrt`
- `tflite`
- `tflite-runtime`
- `tokenization`
- `toml`
- `torch`
- `torch_cuda`
- `torch_tensorrt`
- `torchaudio`
- `torchaudio_cuda`
- `torchvision`
- `torchvision_cuda`
- `tornado`
- `tqdm`
- `transformers`
- `typing_extensions`
- `ujson`
- `unidecode`
- `url.#` _(# can be substituted dynamically)_
- `wandb`
- `west`
- `whl-url.#` _(# can be substituted dynamically)_
- `xgboost`
- `xlsxwriter`
