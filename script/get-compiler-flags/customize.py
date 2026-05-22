from mlc import utils
import os
import subprocess


def preprocess(i):
    os_info = i['os_info']

    env = i['env']
    logger = i['automation'].logger
    env['+ CFLAGS'] = []
    env['+ CXXFLAGS'] = []
    env['+ FFLAGS'] = []
    env['+ LDFLAGS'] = []

    # TBD: add unified flags for Windows
    if os_info['platform'] == 'windows':
        return {'return': 0}

    if env.get("MLC_FAST_COMPILATION") in ["yes", "on", "1"]:
        DEFAULT_COMPILER_FLAGS = env.get("MLC_COMPILER_FLAGS_FAST", "-O3")
        # -flto") - this flag is not always available
        DEFAULT_LINKER_FLAGS = env.get("MLC_LINKER_FLAGS_FAST", "-O3")
    elif env.get("MLC_DEBUG_COMPILATION") in ["yes", "on", "1"]:
        DEFAULT_COMPILER_FLAGS = env.get("MLC_COMPILER_FLAGS_DEBUG", "-O0")
        DEFAULT_LINKER_FLAGS = env.get("MLC_LINKER_FLAGS_DEBUG", "-O0")
    else:
        DEFAULT_COMPILER_FLAGS = env.get("MLC_COMPILER_FLAGS_DEFAULT", "-O2")
        DEFAULT_LINKER_FLAGS = env.get("MLC_LINKER_FLAGS_DEFAULT", "-O2")

    env['+ CFLAGS'] += DEFAULT_COMPILER_FLAGS.split(" ")
    env['+ CXXFLAGS'] += DEFAULT_COMPILER_FLAGS.split(" ")
    env['+ FFLAGS'] += DEFAULT_COMPILER_FLAGS.split(" ")
    env['+ LDFLAGS'] += DEFAULT_LINKER_FLAGS.split(" ")

    env['+ CFLAGS'] = list(set(env['+ CFLAGS']))
    env['+ CXXFLAGS'] = list(set(env['+ CXXFLAGS']))
    env['+ FFLAGS'] = list(set(env['+ FFLAGS']))
    env['+ LDFLAGS'] = list(set(env['+ LDFLAGS']))

    if os_info['platform'] == 'darwin' and env.get(
            'MLC_COMPILER_FAMILY', '') == 'LLVM':
        try:
            sdkroot = subprocess.check_output(
                ["xcrun", "--show-sdk-path"], text=True).strip()
            if sdkroot:
                env['SDKROOT'] = sdkroot
                env['+ CFLAGS'] += ['-isysroot', sdkroot]
                env['+ CXXFLAGS'] += ['-isysroot', sdkroot]
                env['+ LDFLAGS'] += ['-isysroot', sdkroot]
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning(
                'Unable to detect macOS SDK path via xcrun; proceeding without explicit SDKROOT')

    sys_cmd = "cpp -v /dev/null -o /dev/null 2>&1"
    result = subprocess.check_output(sys_cmd, shell=True).decode("utf-8")
    start = False
    inc_dir = []
    for out in result.split("\n"):
        if "> search starts here" not in out and not start:
            continue
        if not start:
            start = True
            continue
        if "End of search list" in out:
            break
        if 'gcc' not in out:
            inc_dir.append(out.strip())
    env['+MLC_HOST_OS_DEFAULT_INCLUDE_PATH'] = inc_dir

#    if env['MLC_C_COMPILER_BIN'] == 'icc':
#        if env['MLC_CPUINFO_Vendor_ID'] == 'GenuineIntel':
#            if int(env['MLC_CPUINFO_CPU_family']) >= 0:
#                env['+ CFLAGS'] += ["-ipo"]
#    if env['MLC_C_COMPILER_BIN'] == 'gcc':
#        if env['MLC_HOST_CPU_VENDOR_ID'] == 'AMD':
#            if int(env['MLC_HOST_CPU_FAMILY']) >= 0:
#                env['+ CFLAGS'] += ["-march=znver2", "-flto"]

    return {'return': 0}
