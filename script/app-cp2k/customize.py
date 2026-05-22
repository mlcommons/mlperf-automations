from mlc import utils
import os


def preprocess(i):

    env = i['env']
    state = i['state']
    os_info = i['os_info']

    for key in ["+LD_LIBRARY_PATH", "+LIBRARY_PATH", "+PATH"]:
        if key not in env:
            env[key] = []

    compiler = env.get('MLC_CP2K_COMPILER', 'gcc')

    # Set compiler paths based on the selected compiler family
    if compiler == 'aocc':
        cc = env.get('MLC_C_COMPILER_WITH_PATH', 'clang')
        cxx = env.get('MLC_CXX_COMPILER_WITH_PATH', 'clang++')
        fc = env.get('MLC_FORTRAN_COMPILER_WITH_PATH', 'flang')
        aocc_lib_path = env.get('MLC_AOCC_LIB_PATH', '')
        if aocc_lib_path:
            env['+LD_LIBRARY_PATH'].append(os.path.abspath(aocc_lib_path))
            env['+LIBRARY_PATH'].append(os.path.abspath(aocc_lib_path))

    elif compiler == 'gcc':
        cc = env.get('MLC_C_COMPILER_WITH_PATH', 'gcc')
        cxx = env.get('MLC_CXX_COMPILER_WITH_PATH', 'g++')
        fc = env.get('MLC_FORTRAN_COMPILER_WITH_PATH', 'gfortran')

    elif compiler == 'llvm':
        cc = env.get('MLC_C_COMPILER_WITH_PATH', 'clang')
        cxx = env.get('MLC_CXX_COMPILER_WITH_PATH', 'clang++')
        fc = env.get('MLC_FORTRAN_COMPILER_WITH_PATH', 'flang')
        llvm_lib_path = os.path.join(
            env.get('MLC_LLVM_INSTALLED_PATH', ''), 'lib')
        if os.path.isdir(llvm_lib_path):
            env['+LD_LIBRARY_PATH'].append(os.path.abspath(llvm_lib_path))
            env['+LIBRARY_PATH'].append(os.path.abspath(llvm_lib_path))

    elif compiler == 'oneapi':
        cc = env.get('MLC_ONEAPI_COMPILER_WITH_PATH', 'icx')
        cxx = cc.replace('icx', 'icpx') if 'icx' in cc else 'icpx'
        fc = cc.replace('icx', 'ifx') if 'icx' in cc else 'ifx'
        oneapi_lib_path = os.path.join(
            env.get('MLC_ONEAPI_INSTALLED_PATH', ''), 'lib')
        if os.path.isdir(oneapi_lib_path):
            env['+LD_LIBRARY_PATH'].append(os.path.abspath(oneapi_lib_path))
            env['+LIBRARY_PATH'].append(os.path.abspath(oneapi_lib_path))

    else:
        return {'return': 1, 'error': f'Unsupported compiler: {compiler}'}

    env['MLC_CP2K_CC'] = cc
    env['MLC_CP2K_CXX'] = cxx
    env['MLC_CP2K_FC'] = fc

    # Add BLAS paths
    blas_install = env.get('MLC_BLAS_INSTALL_PATH', '')
    if blas_install:
        blas_lib_path = os.path.join(blas_install, 'lib')
        blas_bin_path = os.path.join(blas_install, 'bin')
        if os.path.isdir(blas_lib_path):
            env['+LD_LIBRARY_PATH'].append(os.path.abspath(blas_lib_path))
            env['+LIBRARY_PATH'].append(os.path.abspath(blas_lib_path))
        if os.path.isdir(blas_bin_path):
            env['+PATH'].append(os.path.abspath(blas_bin_path))

    return {'return': 0}


def postprocess(i):

    env = i['env']

    install_dir = os.path.join(os.getcwd(), 'install')
    bin_dir = os.path.join(install_dir, 'bin')
    lib_dir = os.path.join(install_dir, 'lib')

    env['MLC_CP2K_INSTALL_PATH'] = install_dir

    for key in ['+LD_LIBRARY_PATH', '+PATH']:
        if key not in env:
            env[key] = []

    if os.path.isdir(bin_dir):
        env['+PATH'].append(bin_dir)
    if os.path.isdir(lib_dir):
        env['+LD_LIBRARY_PATH'].append(lib_dir)

    return {'return': 0}
