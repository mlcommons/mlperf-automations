from mlc import utils
import os
import json
import shutil
from utils import *


def preprocess(i):
    env = i['env']
    state = i['state']
    os_info = i['os_info']

    logger = i['automation'].logger

    submitter = env.get('MLC_MLPERF_SUBMITTER', 'MLCommons')

    auto_detected_hw_name = False
    if env.get('MLC_HW_NAME', '') == '':
        host_name = env.get(
            'MLC_HOST_SYSTEM_NAME',
            'default').replace(
            "-",
            "_").replace(" ", "_")
        env['MLC_HW_NAME'] = host_name
        auto_detected_hw_name = True

    hw_name = env['MLC_HW_NAME']

    backend = env.get('MLC_MLPERF_BACKEND', '')
    backend_version = env.get('MLC_MLPERF_BACKEND_VERSION', '')
    sut_suffix = ''
    backend_name = ''
    backend_desc = ''
    if backend:
        backend_name = env.get('MLC_MLPERF_BACKEND_NAME', backend)
        sut_suffix = "-" + backend
        backend_desc = backend_name
        if backend_version:
            sut_suffix += "-" + backend_version
            backend_desc += ' v' + backend_version

    sut = hw_name + sut_suffix
    script_path = i['run_script_input']['path']
    sut_desc_path = env['MLC_MLPERF_INFERENCE_SUT_DESC_PATH']

    sut_path = os.path.join(sut_desc_path, "suts", sut + ".json")
    env['MLC_SUT_PATH'] = sut_path

    if os.path.exists(sut_path) and is_true(env.get('MLC_SUT_DESC_CACHE', '')):
        logger.info(f"Reusing SUT description file {sut}")
        state['MLC_SUT_META'] = json.load(open(sut_path))
    else:
        if not os.path.exists(os.path.dirname(sut_path)):
            os.makedirs(os.path.dirname(sut_path))

        logger.info("Generating SUT description file for " + sut)
        hw_path = os.path.join(os.getcwd(), "hardware", hw_name + ".json")
        if not os.path.exists(os.path.dirname(hw_path)):
            os.makedirs(os.path.dirname(hw_path))
        if not os.path.exists(hw_path):
            default_hw_path = os.path.join(
                script_path, "hardware", "default.json")
            print("HW description file for " + hw_name +
                  " not found. Copying from default!!!")
            shutil.copy(default_hw_path, hw_path)

        state['MLC_HW_META'] = json.load(open(hw_path))
        state['MLC_SUT_META'] = state['MLC_HW_META']
        state['MLC_SUT_META']['framework'] = backend_desc
        os_name = env.get('MLC_HOST_OS_FLAVOR', '').capitalize()
        os_version = env.get('MLC_HOST_OS_VERSION', '')
        if os_name and os_version:
            os_name_string = os_name + " " + os_version
        else:
            os_name_string = ''
        os_type = env.get('MLC_HOST_OS_TYPE', '')
        kernel = env.get('MLC_HOST_OS_KERNEL_VERSION', '')
        if os_type and kernel:
            os_name_string += " (" + os_type + "-" + kernel
            glibc_version = env.get('MLC_HOST_OS_GLIBC_VERSION', '')
            if glibc_version:
                os_name_string += '-glibc' + glibc_version
            os_name_string += ')'
        python_version = env.get('MLC_PYTHON_VERSION', '')
        compiler = env.get('MLC_COMPILER_FAMILY', '')
        compiler_version = env.get('MLC_COMPILER_VERSION', '')
        state['MLC_SUT_META']['submitter'] = submitter

        # If Windows and os_name_string is empty, rebuild it:

        if os_name_string == '' and os_info['platform'] == 'windows':
            import platform
            os_name_string = str(platform.platform())

        state['MLC_SUT_META']['operating_system'] = os_name_string

        state['MLC_SUT_META']['other_software_stack'] = "Python: " + \
            python_version + ", " + compiler + "-" + compiler_version

        if env.get('MLC_DOCKER_VERSION', '') != '':
            state['MLC_SUT_META']['other_software_stack'] += " Docker version:" + \
                env['MLC_DOCKER_VERSION']
        else:
            if os.path.exists('/.dockerenv'):
                state['MLC_SUT_META']['other_software_stack'] += ", Using Docker "

        if state['MLC_SUT_META'].get('system_name', '') == '':
            system_name = env.get('MLC_MLPERF_SYSTEM_NAME')
            if not system_name:
                system_name = env.get('MLC_HW_NAME')
                if system_name:
                    if auto_detected_hw_name:
                        system_name += " (auto detected)"
                else:
                    system_name = " (generic)"
            state['MLC_SUT_META']['system_name'] = system_name

        # Add GPU info

        if env.get('MLC_MLPERF_DEVICE', '') == "gpu" or env.get(
                'MLC_MLPERF_DEVICE', '') == "cuda":
            if env.get('MLC_CUDA_VERSION', '') != '':
                cuda_version = " , CUDA " + env['MLC_CUDA_VERSION']
                state['MLC_SUT_META']['other_software_stack'] += cuda_version

        if 'mlc_cuda_device_prop' in state:
            state['MLC_SUT_META']['accelerator_frequency'] = state['mlc_cuda_device_prop']['Max clock rate']
            state['MLC_SUT_META']['accelerator_memory_capacity'] = str(int(
                state['mlc_cuda_device_prop']['Global memory']) / (1024 * 1024.0 * 1024)) + " GB"
            state['MLC_SUT_META']['accelerator_model_name'] = state['mlc_cuda_device_prop']['GPU Name']
            num_accelerators = env.get('MLC_CUDA_NUM_DEVICES', "1")
            state['MLC_SUT_META']['accelerators_per_node'] = num_accelerators

        if state['MLC_SUT_META'].get('host_processor_core_count', '') == '':
            physical_cores_per_node = env.get(
                'MLC_HOST_CPU_PHYSICAL_CORES_PER_SOCKET')

            if physical_cores_per_node is None or physical_cores_per_node == '':
                if os_info['platform'] == 'windows':
                    physical_cores_per_node = '1'

            state['MLC_SUT_META']['host_processor_core_count'] = physical_cores_per_node

        if state['MLC_SUT_META'].get('host_processor_model_name', '') == '':
            state['MLC_SUT_META']['host_processor_model_name'] = env.get(
                'MLC_HOST_CPU_MODEL_NAME', 'undefined')
        if state['MLC_SUT_META'].get('host_processors_per_node', '') == '':
            x = env.get('MLC_HOST_CPU_SOCKETS', '')
            if x == '' and os_info['platform'] == 'windows':
                x = '1'
            state['MLC_SUT_META']['host_processors_per_node'] = x

        if state['MLC_SUT_META'].get('host_processor_caches', '') == '':
            state['MLC_SUT_META']['host_processor_caches'] = "L1d cache: " + env.get('MLC_HOST_CPU_L1D_CACHE_SIZE', ' ') + \
                ", L1i cache: " + env.get('MLC_HOST_CPU_L1I_CACHE_SIZE', ' ') + ", L2 cache: " + \
                env.get('MLC_HOST_CPU_L2_CACHE_SIZE', ' ') + \
                ", L3 cache: " + env.get('MLC_HOST_CPU_L3_CACHE_SIZE', ' ')

        if state['MLC_SUT_META'].get('host_processor_frequency', '') == '':
            state['MLC_SUT_META']['host_processor_frequency'] = env.get(
                'MLC_HOST_CPU_MAX_MHZ') if env.get('MLC_HOST_CPU_MAX_MHZ', '') != '' else 'undefined'
        if state['MLC_SUT_META'].get('host_memory_capacity', '') == '':
            state['MLC_SUT_META']['host_memory_capacity'] = env.get(
                'MLC_HOST_MEMORY_CAPACITY') if env.get('MLC_HOST_MEMORY_CAPACITY', '') != '' else 'undefined'
        if state['MLC_SUT_META'].get('host_storage_capacity', '') == '':
            state['MLC_SUT_META']['host_storage_capacity'] = env.get(
                'MLC_HOST_DISK_CAPACITY') if env.get('MLC_HOST_DISK_CAPACITY', '') != '' else 'undefined'
        if 'MLC_SUT_SW_NOTES' in env:
            sw_notes = env['MLC_SUT_SW_NOTES']
        else:
            sw_notes = ''
        state['MLC_SUT_META']['sw_notes'] = sw_notes

        if env.get('MLC_SUDO_USER', '') == "yes" and env.get(
                'MLC_HOST_OS_TYPE', 'linux'):
            env['MLC_MEMINFO_FILE'] = os.path.join(os.getcwd(), 'meminfo.dump')
            r = i['automation'].run_native_script(
                {'run_script_input': i['run_script_input'], 'env': env, 'script_name': 'detect_memory'})
            if r['return'] > 0:
                return r

    return {'return': 0}


def postprocess(i):

    env = i['env']
    state = i['state']

    if env.get('MLC_MEMINFO_OUTFILE', '') != '' and os.path.exists(
            env['MLC_MEMINFO_OUTFILE']):
        with open(env['MLC_MEMINFO_OUTFILE'], "r") as f:
            data = f.read()
        state['MLC_SUT_META']['host_memory_configuration'] = data

    state['MLC_SUT_META'] = dict(sorted(state['MLC_SUT_META'].items()))

    sut_path = env['MLC_SUT_PATH']

    sut_file = open(sut_path, "w")
    json.dump(state['MLC_SUT_META'], sut_file, indent=4)
    sut_file.close()

    return {'return': 0}
