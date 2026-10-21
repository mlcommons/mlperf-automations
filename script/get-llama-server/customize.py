from mlc import utils
import os
import hashlib
import subprocess


def is_true(v):
    return str(v).strip().lower() in ('yes', 'true', '1', 'on')


_COMPILER_BINS = {
    'gcc':      ('MLC_GCC_DIR_PATH',      'MLC_GCC_BIN_WITH_PATH',        'gcc',   'g++'),
    'aocc':     ('MLC_AOCC_DIR_PATH',     'MLC_AOCC_BIN_WITH_PATH',       'clang', 'clang++'),
    'llvm':     ('MLC_LLVM_DIR_PATH',     'MLC_LLVM_CLANG_BIN_WITH_PATH', 'clang', 'clang++'),
    'amdclang': ('MLC_AMDCLANG_DIR_PATH', 'MLC_AMDCLANG_BIN_WITH_PATH',   'clang', 'clang++'),
    'oneapi':   ('MLC_ONEAPI_DIR_PATH',   'MLC_ICX_BIN_WITH_PATH',        'icx',   'icpx'),
}

_VERSION_KEYS = {
    'aocc': 'MLC_AOCC_VERSION', 'gcc': 'MLC_GCC_VERSION',
    'llvm': 'MLC_LLVM_CLANG_VERSION', 'amdclang': 'MLC_AMDCLANG_VERSION',
    'oneapi': 'MLC_ONEAPI_VERSION',
}


def _resolve_compiler(env):
    """Return (family, cc, cxx) for the selected compiler."""
    fam = (env.get('MLC_AGENT_COMPILER') or 'aocc').lower()
    if fam not in _COMPILER_BINS:
        return fam, '', ''
    dir_key, bin_key, cc_name, cxx_name = _COMPILER_BINS[fam]
    cc = env.get(bin_key, '')
    cdir = env.get(dir_key, '')
    if not cc and cdir:
        cc = os.path.join(cdir, 'bin', cc_name)
    if not cc:
        return fam, '', ''
    cc_dir = os.path.dirname(cc)
    cxx = os.path.join(cc_dir, cxx_name)
    if not os.path.isfile(cxx):
        cxx = cc + '++' if not cc.endswith(cxx_name) else cxx
    return fam, cc, cxx


def preprocess(i):
    env = i['env']

    # The image/dry-run pass must not build (benchmark-hpc pattern).
    if i.get('fake_run') or is_true(env.get('MLC_TMP_FAKE_RUN')):
        return {'return': 0}

    src = env.get('MLC_LLAMA_CPP_SRC_PATH', '')
    if not src or not os.path.isdir(src):
        return {'return': 1, 'error': "llama.cpp source not found "
                "(set --llama_cpp_path=<dir> or let the get,git,repo dep clone it)"}

    fam, cc, cxx = _resolve_compiler(env)
    if not cc:
        return {'return': 1, 'error': f"could not resolve a '{fam}' compiler "
                f"(pass --{fam}_dir=<install> or the get,{fam} dep found nothing)"}

    version = env.get(_VERSION_KEYS.get(fam, ''), '') if fam in _VERSION_KEYS else ''

    # Per-compiler build tree: a different toolchain (family, version or install
    # path) gets its own build dir, so switching compilers forces a fresh build
    # and never reuses another compiler's llama-server. The install-path hash
    # disambiguates two toolchains that report the same version string.
    cc_real = os.path.realpath(cc)
    pathhash = hashlib.md5(cc_real.encode()).hexdigest()[:8]
    verslug = ''.join(ch if (ch.isalnum() or ch in '.-') else '_' for ch in version)[:24]
    _profile = (env.get('MLC_AGENT_AGGRESSIVE_PROFILE', '') or '').lower()
    _suffix = ('-' + (_profile or 'aggr')) if is_true(env.get('MLC_AGENT_AGGRESSIVE')) else ''
    slug = fam + _suffix + (('-' + verslug) if verslug else '') + '-' + pathhash
    build_dir = env.get('MLC_LLAMA_BUILD_DIR', '') or os.path.join(src, 'build-' + slug)
    server_bin = os.path.join(build_dir, 'bin', 'llama-server')

    # Compiler runtime lib dirs (libomp/libgomp): linked at build (CMake FindOpenMP)
    # and exported at runtime so llama-server can load the compiler's own OpenMP.
    inst = os.path.dirname(os.path.dirname(cxx))
    libdirs = [d for d in (os.path.join(inst, 'lib'), os.path.join(inst, 'lib64'))
               if os.path.isdir(d)]

    custom = env.get('MLC_AGENT_ENGINE_CMAKE_FLAGS', '').strip()
    if custom:
        cmake_args = custom.split()
    elif _profile == 'clang_vfe':
        cmake_args = [
            '-DGGML_LTO=ON', '-DGGML_NATIVE=ON',
            '-DCMAKE_C_FLAGS=-flto -mllvm -inline-threshold=2000 -fvisibility=hidden',
            '-DCMAKE_CXX_FLAGS=-flto -mllvm -inline-threshold=2000 -fvirtual-function-elimination -fvisibility=hidden',
            '-DCMAKE_EXE_LINKER_FLAGS=-flto -Wl,-mllvm -Wl,-inline-threshold=2000',
            '-DCMAKE_SHARED_LINKER_FLAGS=-flto -Wl,-mllvm -Wl,-inline-threshold=2000',
        ]
    elif is_true(env.get('MLC_AGENT_AGGRESSIVE')):
        cmake_args = ['-DGGML_LTO=ON', '-DGGML_NATIVE=ON',
                      '-DCMAKE_C_FLAGS=-funroll-loops', '-DCMAKE_CXX_FLAGS=-funroll-loops']
    else:
        cmake_args = []
    if libdirs:
        cmake_args.append('-DCMAKE_LIBRARY_PATH=' + ';'.join(libdirs))

    script = os.path.join(env['MLC_TMP_CURRENT_SCRIPT_PATH'], 'build-llama-cpp.sh')
    run_env = dict(os.environ)
    run_env.update({
        'LLAMA_CPP_SRC_PATH': src,
        'LLAMA_BUILD_DIR': build_dir,
        'CC': cc,
        'CXX': cxx,
        'LLAMA_CMAKE_FLAGS_ARR': '\n'.join(cmake_args),
        'LLAMA_FORCE_BUILD': 'true' if is_true(env.get('MLC_AGENT_FORCE_BUILD')) else 'false',
        'BUILD_JOBS': str(env.get('MLC_AGENT_BUILD_NCPUS')
                          or env.get('MLC_HOST_CPU_TOTAL_LOGICAL_CORES') or ''),
    })
    if libdirs:
        _ld = ':'.join(libdirs)
        run_env['LIBRARY_PATH'] = _ld + (':' + run_env['LIBRARY_PATH'] if run_env.get('LIBRARY_PATH') else '')
        run_env['LD_LIBRARY_PATH'] = _ld + (':' + run_env['LD_LIBRARY_PATH'] if run_env.get('LD_LIBRARY_PATH') else '')

    print(f"Building llama.cpp ({fam}): CC={cc} CXX={cxx}")
    print(f"Build dir       : {build_dir}")
    if subprocess.run(['bash', script], env=run_env).returncode != 0:
        return {'return': 1, 'error': 'llama.cpp build failed'}
    if not os.path.isfile(server_bin):
        return {'return': 1, 'error': f'expected llama-server not found at {server_bin}'}

    env['MLC_LLAMA_BUILD_DIR'] = build_dir
    env['MLC_LLAMA_SERVER_BIN'] = server_bin
    env['MLC_LLAMA_BENCH_BIN'] = os.path.join(build_dir, 'bin', 'llama-bench')
    env['MLC_AGENT_ENGINE_COMPILED_WITH'] = f"{fam}: {cc}"
    if not env.get('MLC_AGENT_COMPILER_VERSION'):
        env['MLC_AGENT_COMPILER_VERSION'] = version

    if libdirs:
        env['MLC_AGENT_ENGINE_LIB_DIRS'] = ':'.join(libdirs)
        # LD_LIBRARY_PATH is a PATH-style list in MLC: use the '+' list form so
        # mlcflow exports it to the consumer shell (a plain string is not
        # propagated, so llama-server would fail to find the compiler's libomp).
        plus = env.setdefault('+LD_LIBRARY_PATH', [])
        if not isinstance(plus, list):
            plus = [plus] if plus else []
            env['+LD_LIBRARY_PATH'] = plus
        for d in libdirs:
            if d and d not in plus:
                plus.append(d)
    return {'return': 0}


def postprocess(i):
    return {'return': 0}
