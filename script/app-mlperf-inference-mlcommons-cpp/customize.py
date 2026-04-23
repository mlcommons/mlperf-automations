from mlc import utils
import os
import shutil


def preprocess(i):

    os_info = i['os_info']

    automation = i['automation']

    meta = i['meta']

    logger = i['automation'].logger

    if os_info['platform'] == 'windows':
        logger.info(
            '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
        logger.warning(
            'This script was not thoroughly tested on Windows and compilation may fail - please help us test and improve it!')
        logger.info(
            '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
#        # Currently support only LLVM on Windows
#        print ('# Forcing LLVM on Windows')
#        r = automation.update_deps({'deps':meta['post_deps'], 'update_deps':{'compile-program': {'adr':{'compiler':{'tags':'llvm'}}}}})
#        if r['return']>0: return r

    env = i['env']

    if env.get('MLC_MLPERF_SKIP_RUN', '') == "yes":
        return {'return': 0}

    if 'MLC_MODEL' not in env:
        return {
            'return': 1, 'error': 'Please select a variation specifying the model to run'}
    if 'MLC_MLPERF_BACKEND' not in env:
        return {'return': 1,
                'error': 'Please select a variation specifying the backend'}
    if 'MLC_MLPERF_DEVICE' not in env:
        return {
            'return': 1, 'error': 'Please select a variation specifying the device to run on'}

    source_files = []
    script_path = i['run_script_input']['path']
    if env['MLC_MODEL'] == "retinanet":
        env['MLC_DATASET_LIST'] = env['MLC_DATASET_ANNOTATIONS_FILE_PATH']
    elif 'bert' in env['MLC_MODEL']:
        env['MLC_DATASET_SQUAD_TOKENIZED_ROOT'] = env.get(
            'MLC_DATASET_SQUAD_TOKENIZED_ROOT', '')
        env['MLC_DATASET_MAX_SEQ_LENGTH'] = env.get(
            'MLC_DATASET_SQUAD_TOKENIZED_MAX_SEQ_LENGTH', '384')
    env['MLC_SOURCE_FOLDER_PATH'] = os.path.join(script_path, "src")

    for file in os.listdir(env['MLC_SOURCE_FOLDER_PATH']):
        if file.endswith(".c") or file.endswith(".cpp"):
            source_files.append(file)

    env['MLC_CXX_SOURCE_FILES'] = ";".join(source_files)

    if '+CPLUS_INCLUDE_PATH' not in env:
        env['+CPLUS_INCLUDE_PATH'] = []

    env['+CPLUS_INCLUDE_PATH'].append(os.path.join(script_path, "inc"))
    env['+C_INCLUDE_PATH'].append(os.path.join(script_path, "inc"))

    if env['MLC_MLPERF_DEVICE'] == 'gpu':
        env['+C_INCLUDE_PATH'].append(env['MLC_CUDA_PATH_INCLUDE'])
        env['+CPLUS_INCLUDE_PATH'].append(env['MLC_CUDA_PATH_INCLUDE'])
        env['+LD_LIBRARY_PATH'].append(env['MLC_CUDA_PATH_LIB'])
        env['+DYLD_FALLBACK_LIBRARY_PATH'].append(env['MLC_CUDA_PATH_INCLUDE'])

    if '+ CXXFLAGS' not in env:
        env['+ CXXFLAGS'] = []
    if env.get('MLC_MLPERF_BACKEND', '') == 'pytorch':
        env['+ CXXFLAGS'].append("-std=c++17")
    else:
        env['+ CXXFLAGS'].append("-std=c++14")

    # add preprocessor flag like "#define MLC_MODEL_RESNET50"
    env['+ CXXFLAGS'].append('-DMLC_MODEL_' +
                             env['MLC_MODEL'].upper().replace('-', '_').replace('.', '_'))
    # add preprocessor flag like "#define MLC_MLPERF_BACKEND_ONNXRUNTIME"
    env['+ CXXFLAGS'].append('-DMLC_MLPERF_BACKEND_' +
                             env['MLC_MLPERF_BACKEND'].upper())
    # add preprocessor flag like "#define MLC_MLPERF_DEVICE_CPU"
    env['+ CXXFLAGS'].append('-DMLC_MLPERF_DEVICE_' +
                             env['MLC_MLPERF_DEVICE'].upper())

    # For PyTorch backend, detect LibTorch include/lib paths from pip torch
    if env.get('MLC_MLPERF_BACKEND', '') == 'pytorch':
        import torch as _torch
        torch_path = os.path.dirname(_torch.__file__)
        torch_inc = os.path.join(torch_path, 'include')
        torch_inc_csrc = os.path.join(
            torch_path,
            'include',
            'torch',
            'csrc',
            'api',
            'include')
        torch_lib = os.path.join(torch_path, 'lib')
        env['+CPLUS_INCLUDE_PATH'].append(torch_inc)
        env['+CPLUS_INCLUDE_PATH'].append(torch_inc_csrc)
        env['+C_INCLUDE_PATH'].append(torch_inc)
        env['+C_INCLUDE_PATH'].append(torch_inc_csrc)
        env['+LD_LIBRARY_PATH'].append(torch_lib)
        env['+DYLD_FALLBACK_LIBRARY_PATH'].append(torch_lib)
        if not _torch.compiled_with_cxx11_abi():
            env['+ CXXFLAGS'].append('-D_GLIBCXX_USE_CXX11_ABI=0')

    if '+ LDCXXFLAGS' not in env:
        env['+ LDCXXFLAGS'] = []

    env['+ LDCXXFLAGS'].append("-lmlperf_loadgen")
    if os_info['platform'] != 'darwin':
        env['+ LDCXXFLAGS'].append("-lpthread")

    # For PyTorch, link against torch, torch_cpu, and c10
    if env.get('MLC_MLPERF_BACKEND', '') == 'pytorch':
        env['+ LDCXXFLAGS'] += ['-ltorch', '-ltorch_cpu', '-lc10']
        if env.get('MLC_MLPERF_DEVICE', '') == 'gpu':
            env['+ LDCXXFLAGS'] += ['-ltorch_cuda', '-lc10_cuda']
    # e.g. -lonnxruntime
    elif 'MLC_MLPERF_BACKEND_LIB_NAMESPEC' in env:
        env['+ LDCXXFLAGS'].append('-l' +
                                   env['MLC_MLPERF_BACKEND_LIB_NAMESPEC'])
    # e.g. -lcudart
    if 'MLC_MLPERF_DEVICE_LIB_NAMESPEC' in env:
        env['+ LDCXXFLAGS'].append('-l' +
                                   env['MLC_MLPERF_DEVICE_LIB_NAMESPEC'])

    env['MLC_LINKER_LANG'] = 'CXX'
    env['MLC_RUN_DIR'] = os.getcwd()

    # For PyTorch backend, convert .pth weights to TorchScript .pt if needed
    if env.get('MLC_MLPERF_BACKEND', '') == 'pytorch':
        model_path = env.get('MLC_ML_MODEL_FILE_WITH_PATH', '')
        if model_path.endswith('.pth'):
            torchscript_path = model_path.replace('.pth', '_torchscript.pt')
            if not os.path.exists(torchscript_path):
                import torch
                import torchvision.models as models
                logger.info(
                    f"Converting {model_path} to TorchScript at {torchscript_path}")
                model = models.resnet50()
                model.load_state_dict(
                    torch.load(
                        model_path,
                        map_location='cpu',
                        weights_only=False))
                model.eval()
                traced = torch.jit.trace(model, torch.randn(1, 3, 224, 224))
                traced.save(torchscript_path)
                logger.info("TorchScript conversion done")
            env['MLC_ML_MODEL_FILE_WITH_PATH'] = torchscript_path

    if 'MLC_MLPERF_USER_CONF' not in env:
        if 'bert' in env['MLC_MODEL']:
            env['MLC_MLPERF_USER_CONF'] = os.path.join(
                env.get('MLC_MLPERF_INFERENCE_BERT_PATH', ''), "user.conf")
        else:
            env['MLC_MLPERF_USER_CONF'] = os.path.join(
                env['MLC_MLPERF_INFERENCE_CLASSIFICATION_AND_DETECTION_PATH'], "user.conf")

    return {'return': 0}


def postprocess(i):

    env = i['env']
    state = i['state']

    return {'return': 0}
