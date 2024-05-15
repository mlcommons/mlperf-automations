from cmind import utils
import os

def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    automation = i['automation']
    version = env.get('CM_VERSION')
    print(f"The got version is:{version}")
    print(f"CM Cuda version string {env['CM_CUDA_VERSION_STRING']}")
    if version not in env.get('CM_CUDA_LINUX_FILENAME', ''):
        return {'return': 1, 'error': "Only CUDA versions 11.7.0, 11.8.0, 12.0.0, 12.1.1, 12.2.0, 12.3.2 and 12.4.1 are supported now!"}

    recursion_spaces = i['recursion_spaces']
    nvcc_bin = "nvcc"

    env['WGET_URL']="https://developer.download.nvidia.com/compute/cuda/"+env['CM_VERSION']+"/local_installers/"+env['CM_CUDA_LINUX_FILENAME']

    extra_options = env.get('CUDA_ADDITIONAL_INSTALL_OPTIONS', '')
    if env.get('CM_CUDA_INSTALL_DRIVER','') == "yes":
        extra_options += " --driver"
    env['CUDA_ADDITIONAL_INSTALL_OPTIONS'] = extra_options

    env['CM_CUDA_INSTALLED_PATH'] = os.path.join(os.getcwd(), 'install')
    env['CM_NVCC_BIN_WITH_PATH'] = os.path.join(os.getcwd(), 'install', 'bin', nvcc_bin)
    env['CM_GET_DEPENDENT_CACHED_PATH'] =  env['CM_NVCC_BIN_WITH_PATH']

    # Set CUDA_RUN_FILE_LOCAL_PATH to empty if not set for backwards compatibility in download file
    env['CUDA_RUN_FILE_LOCAL_PATH'] = env.get('CUDA_RUN_FILE_LOCAL_PATH','')

    return {'return':0}
