from mlc import utils
import os
import json


def preprocess(i):

    env = i['env']
    state = i['state']

    app = env.get('MLC_HPC_BENCH_APP', 'cp2k')

    # Determine OMP_NUM_THREADS
    num_ranks = int(env.get('MLC_HPC_BENCH_NUM_MPI_RANKS', '1'))
    omp_threads = env.get('MLC_HPC_BENCH_OMP_THREADS', '')
    if not omp_threads:
        total_cores = int(env.get('MLC_HOST_CPU_TOTAL_PHYSICAL_CORES', '0'))
        if total_cores > 0:
            omp_threads = str(total_cores // num_ranks)
        else:
            omp_threads = '1'
    env['MLC_HPC_BENCH_OMP_THREADS'] = omp_threads

    if app == 'cp2k':
        return preprocess_cp2k(env, state)

    return {'return': 1, 'error': f'Unsupported HPC application: {app}'}


def preprocess_cp2k(env, state):

    install_path = env.get('MLC_CP2K_INSTALL_PATH', '')
    if not install_path:
        return {'return': 1, 'error': 'MLC_CP2K_INSTALL_PATH not set. Build CP2K first.'}

    # Ensure library paths are set for runtime
    for key in ['+LD_LIBRARY_PATH', '+PATH']:
        if key not in env:
            env[key] = []

    # Add CP2K lib dir
    cp2k_lib_dir = os.path.join(install_path, 'lib')
    if os.path.isdir(cp2k_lib_dir):
        env['+LD_LIBRARY_PATH'].append(cp2k_lib_dir)

    # Add BLAS lib dir
    blas_install = env.get('MLC_BLAS_INSTALL_PATH', '')
    if blas_install:
        blas_lib_dir = os.path.join(blas_install, 'lib')
        if os.path.isdir(blas_lib_dir):
            env['+LD_LIBRARY_PATH'].append(blas_lib_dir)

    # Find the CP2K binary (prefer psmp > popt > ssmp > sopt)
    bin_dir = os.path.join(install_path, 'bin')
    cp2k_bin = ''
    for suffix in ['psmp', 'popt', 'ssmp', 'sopt']:
        candidate = os.path.join(bin_dir, f'cp2k.{suffix}')
        if os.path.isfile(candidate):
            cp2k_bin = candidate
            break

    if not cp2k_bin:
        return {'return': 1, 'error': f'No CP2K binary found in {bin_dir}'}

    env['MLC_HPC_BENCH_BIN'] = cp2k_bin

    # Find benchmark input file
    src_path = env.get('MLC_CP2K_SRC_PATH', '')
    bench_input = env.get('MLC_HPC_BENCH_INPUT', 'H2O-64')
    input_file = os.path.join(src_path, 'benchmarks', 'QS', f'{bench_input}.inp')

    if not os.path.isfile(input_file):
        return {'return': 1, 'error': f'Benchmark input not found: {input_file}'}

    env['MLC_HPC_BENCH_INPUT_FILE'] = input_file

    return {'return': 0}


def postprocess(i):

    env = i['env']
    state = i['state']

    app = env.get('MLC_HPC_BENCH_APP', 'cp2k')

    if app == 'cp2k':
        return postprocess_cp2k(env, state)

    return {'return': 0}


def postprocess_cp2k(env, state):

    # Parse CP2K timing output
    output_file = os.path.join(os.getcwd(), 'bench_output.log')
    if not os.path.isfile(output_file):
        return {'return': 0}

    timing = {}
    in_timing = False

    with open(output_file, 'r') as f:
        for line in f:
            if 'T I M I N G' in line:
                in_timing = True
                continue
            if in_timing and line.strip().startswith('CP2K'):
                parts = line.split()
                if len(parts) >= 7:
                    timing['cp2k_total_time'] = float(parts[6])
                break

    if timing:
        env['MLC_HPC_BENCH_CP2K_TOTAL_TIME'] = str(timing.get('cp2k_total_time', ''))

    # Save results as JSON
    results = {
        'app': 'cp2k',
        'compiler': env.get('MLC_HPC_BENCH_COMPILER', 'unknown'),
        'benchmark': env.get('MLC_HPC_BENCH_INPUT', ''),
        'num_mpi_ranks': env.get('MLC_HPC_BENCH_NUM_MPI_RANKS', '1'),
        'omp_threads': env.get('MLC_HPC_BENCH_OMP_THREADS', ''),
        'timing': timing,
    }

    results_dir = env.get('MLC_HPC_BENCH_RESULTS_DIR', os.getcwd())
    os.makedirs(results_dir, exist_ok=True)
    results_file = os.path.join(results_dir, 'benchmark_results.json')
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    env['MLC_HPC_BENCH_RESULTS_FILE'] = results_file

    return {'return': 0}
