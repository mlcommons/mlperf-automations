from mlc import utils
from utils import is_true
import os
import subprocess


def preprocess(i):
    os_info = i['os_info']
    env = i['env']
    meta = i['meta']
    automation = i['automation']

    # Required parameter check
    model_name = env.get("MLC_VLLM_SERVER_MODEL_NAME")
    if not model_name:
        return {'return': 1, 'error': 'Model name not specified'}

    # Base command with required model argument
    cmd_args = f" --model {env['MLC_ML_MODEL_PATH']} --served-model-name {model_name}"

    # Dictionary mapping environment variables to their corresponding command line arguments
    param_mapping = {
        "MLC_VLLM_SERVER_TP_SIZE": "--tensor-parallel-size",
        "MLC_VLLM_SERVER_PP_SIZE": "--pipeline-parallel-size",
        "MLC_VLLM_SERVER_API_KEY": "--api-key",
        "MLC_VLLM_SERVER_DIST_EXEC_BACKEND": "--distributed-executor-backend",
        "MLC_VLLM_SERVER_HOST": "--host",
        "MLC_VLLM_SERVER_PORT": "--port",
        "MLC_VLLM_SERVER_UVICORN_LOG_LEVEL": "--uvicorn-log-level",
        "MLC_VLLM_SERVER_ALLOWED_ORIGINS": "--allowed-origins",
        "MLC_VLLM_SERVER_ALLOWED_METHODS": "--allowed-methods",
        "MLC_VLLM_SERVER_ALLOWED_HEADERS": "--allowed-headers",
        "MLC_VLLM_SERVER_LORA_MODULES": "--lora-modules",
        "MLC_VLLM_SERVER_PROMPT_ADAPTERS": "--prompt-adapters",
        "MLC_VLLM_SERVER_CHAT_TEMPLATE": "--chat-template",
        "MLC_VLLM_SERVER_RESPONSE_ROLE": "--response-role",
        "MLC_VLLM_SERVER_SSL_KEYFILE": "--ssl-keyfile",
        "MLC_VLLM_SERVER_SSL_CERTFILE": "--ssl-certfile",
        "MLC_VLLM_SERVER_SSL_CA_CERTS": "--ssl-ca-certs",
        "MLC_VLLM_SERVER_SSL_CERT_REQS": "--ssl-cert-reqs",
        "MLC_VLLM_SERVER_ROOT_PATH": "--root-path",
        "MLC_VLLM_SERVER_MIDDLEWARE": "--middleware",
        "MLC_VLLM_SERVER_TOKENIZER": "--tokenizer",
        "MLC_VLLM_SERVER_REVISION": "--revision",
        "MLC_VLLM_SERVER_CODE_REVISION": "--code-revision",
        "MLC_VLLM_SERVER_TOKENIZER_REVISION": "--tokenizer-revision",
        "MLC_VLLM_SERVER_TOKENIZER_MODE": "--tokenizer-mode",
        "MLC_VLLM_SERVER_DOWNLOAD_DIR": "--download-dir",
        "MLC_VLLM_SERVER_LOAD_FORMAT": "--load-format",
        "MLC_VLLM_SERVER_DTYPE": "--dtype",
        "MLC_VLLM_SERVER_KV_CACHE_DTYPE": "--kv-cache-dtype",
        "MLC_VLLM_SERVER_QUANTIZATION_PARAM_PATH": "--quantization-param-path",
        "MLC_VLLM_SERVER_MAX_MODEL_LEN": "--max-model-len",
        "MLC_VLLM_SERVER_GUIDED_DECODING_BACKEND": "--guided-decoding-backend",
        "MLC_VLLM_SERVER_MAX_PARALLEL_LOADING_WORKERS": "--max-parallel-loading-workers",
        "MLC_VLLM_SERVER_BLOCK_SIZE": "--block-size",
        "MLC_VLLM_SERVER_NUM_LOOKAHEAD_SLOTS": "--num-lookahead-slots",
        "MLC_VLLM_SERVER_SEED": "--seed",
        "MLC_VLLM_SERVER_SWAP_SPACE": "--swap-space",
        "MLC_VLLM_SERVER_GPU_MEMORY_UTILIZATION": "--gpu-memory-utilization",
        "MLC_VLLM_SERVER_NUM_GPU_BLOCKS_OVERRIDE": "--num-gpu-blocks-override",
        "MLC_VLLM_SERVER_MAX_NUM_BATCHED_TOKENS": "--max-num-batched-tokens",
        "MLC_VLLM_SERVER_MAX_NUM_SEQS": "--max-num-seqs",
        "MLC_VLLM_SERVER_MAX_LOGPROBS": "--max-logprobs",
        "MLC_VLLM_SERVER_QUANTIZATION": "--quantization",
        "MLC_VLLM_SERVER_ROPE_SCALING": "--rope-scaling",
        "MLC_VLLM_SERVER_ROPE_THETA": "--rope-theta"
    }

    # Boolean flags that don't need values
    bool_flags = {
        "MLC_VLLM_SERVER_ALLOW_CREDENTIALS": "--allow-credentials",
        "MLC_VLLM_SERVER_SKIP_TOKENIZER_INIT": "--skip-tokenizer-init",
        "MLC_VLLM_SERVER_TRUST_REMOTE_CODE": "--trust-remote-code",
        "MLC_VLLM_SERVER_WORKER_USE_RAY": "--worker-use-ray",
        "MLC_VLLM_SERVER_RAY_WORKERS_USE_NSIGHT": "--ray-workers-use-nsight",
        "MLC_VLLM_SERVER_ENABLE_PREFIX_CACHING": "--enable-prefix-caching",
        "MLC_VLLM_SERVER_DISABLE_SLIDING_WINDOW": "--disable-sliding-window",
        "MLC_VLLM_SERVER_USE_V2_BLOCK_MANAGER": "--use-v2-block-manager",
        "MLC_VLLM_SERVER_DISABLE_LOG_STATS": "--disable-log-stats"
    }

    # Add parameters with values
    for env_var, arg_name in param_mapping.items():
        value = env.get(env_var)
        if value:
            cmd_args += f" {arg_name} {value}"

    # Add boolean flags
    for env_var, arg_name in bool_flags.items():
        if is_true(env.get(env_var)):
            cmd_args += f" {arg_name}"

    cmd = f"{env['MLC_PYTHON_BIN_WITH_PATH']} -m vllm.entrypoints.openai.api_server {cmd_args}"
    print(cmd)

    env['MLC_VLLM_RUN_CMD'] = cmd

    return {'return': 0}


def postprocess(i):

    env = i['env']

    return {'return': 0}
