# README for get-ml-model-neuralmagic-zoo
This README is automatically generated. Create and add custom content in info.md. Please follow the [script execution document](https://docs.mlcommons.org/mlcflow/targets/script/execution-flow/) to understand more about the MLC script execution.

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
mlcr get,ml-model,model,zoo,deepsparse,model-zoo,sparse-zoo,neuralmagic,neural-magic
```

No script specific inputs
### Generic Script Inputs

| Name | Description | Choices | Default |
|------|-------------|---------|------|
| `--input` | Input to the script passed using the env key `MLC_INPUT` |  | `` |
| `--output` | Output from the script passed using the env key `MLC_OUTPUT` |  | `` |
| `--outdirname` | The directory to store the script output |  | `cache directory ($HOME/MLC/repos/local/cache/<>) if the script is cacheable or else the current directory` |
| `--outbasename` | The output file/folder name |  | `` |
| `--search_folder_path` | The folder path where executables of a given script need to be searched. Search is done recursively upto 4 levels. |  | `` |
| `--name` |  |  | `` |
| `--extra_cache_tags` | Extra cache tags to be added to the cached entry when the script results are saved |  | `` |
| `--skip_compile` | Skip compilation |  | `False` |
| `--skip_run` | Skip run |  | `False` |
| `--skip_sudo` | Skip SUDO detection |  | `False` |
| `--accept_license` | Accept the required license requirement to run the script |  | `False` |
| `--skip_system_deps` | Skip installing any system dependencies |  | `False` |
| `--git_ssh` | Use SSH for git repos |  | `False` |
| `--gh_token` | Github Token |  | `` |
| `--hf_token` | Huggingface Token |  | `` |
| `--verify_ssl` | Verify SSL |  | `False` |
## Variations

### Ungrouped

- `bert-base-pruned90-none` (alias: model-stub.zoo:nlp/question_answering/bert-base/pytorch/huggingface/squad/pruned90-none)
- `bert-base-pruned95_obs_quant-none` (alias: model-stub.zoo:nlp/question_answering/bert-base/pytorch/huggingface/squad/pruned95_obs_quant-none)
- `bert-base_cased-pruned90-none` (alias: model-stub.zoo:nlp/question_answering/bert-base_cased/pytorch/huggingface/squad/pruned90-none)
- `bert-large-base-none` (alias: model-stub.zoo:nlp/question_answering/bert-large/pytorch/huggingface/squad/base-none)
- `bert-large-pruned80_quant-none-vnni` (alias: model-stub.zoo:nlp/question_answering/bert-large/pytorch/huggingface/squad/pruned80_quant-none-vnni)
- `mobilebert-14layer_pruned50-none-vnni` (alias: model-stub.zoo:nlp/question_answering/mobilebert-none/pytorch/huggingface/squad/14layer_pruned50-none-vnni)
- `mobilebert-14layer_pruned50_quant-none-vnni` (alias: model-stub.zoo:nlp/question_answering/mobilebert-none/pytorch/huggingface/squad/14layer_pruned50_quant-none-vnni)
- `mobilebert-base_quant-none` (alias: model-stub.zoo:nlp/question_answering/mobilebert-none/pytorch/huggingface/squad/base_quant-none)
- `mobilebert-none-base-none` (alias: model-stub.zoo:nlp/question_answering/mobilebert-none/pytorch/huggingface/squad/base-none)
- `model-stub.#` _(# can be substituted dynamically)_
- `obert-base-pruned90-none` (alias: model-stub.zoo:nlp/question_answering/obert-base/pytorch/huggingface/squad/pruned90-none)
- `obert-large-base-none` (alias: model-stub.zoo:nlp/question_answering/obert-large/pytorch/huggingface/squad/base-none)
- `obert-large-pruned95-none-vnni` (alias: model-stub.zoo:nlp/question_answering/obert-large/pytorch/huggingface/squad/pruned95-none-vnni)
- `obert-large-pruned95_quant-none-vnni` (alias: model-stub.zoo:nlp/question_answering/obert-large/pytorch/huggingface/squad/pruned95_quant-none-vnni)
- `obert-large-pruned97-none` (alias: model-stub.zoo:nlp/question_answering/obert-large/pytorch/huggingface/squad/pruned97-none)
- `obert-large-pruned97-quant-none` (alias: model-stub.zoo:nlp/question_answering/obert-large/pytorch/huggingface/squad/pruned97_quant-none)
- `oberta-base-pruned90-quant-none` (alias: model-stub.zoo:nlp/question_answering/oberta-base/pytorch/huggingface/squad/pruned90_quant-none)
- `roberta-base-pruned85-quant-none` (alias: model-stub.zoo:nlp/question_answering/roberta-base/pytorch/huggingface/squad/pruned85_quant-none)
