from mlc import utils
from utils import is_true
import glob
import os
import subprocess


def _find_lib(root, names):
    # AOCL binary packages ship LP64/ILP64 subdirs; apps here use 32-bit ints.
    if not root or not os.path.isdir(root):
        return ''
    for name in names:
        hits = sorted(glob.glob(os.path.join(root, '**', name), recursive=True))
        hits = [h for h in hits if os.sep + 'ILP64' + os.sep not in h]
        if hits:
            return hits[0]
    return ''


def _link_name(path):
    base = os.path.basename(path)
    return base[3:].split('.so')[0].split('.a')[0]


def _openmp_runtime(lib, search_roots):
    """Directory of the OpenMP runtime a shared BLIS needs (libomp for AOCC builds)."""
    if not lib.endswith('.so') and '.so.' not in lib:
        return '', ''
    try:
        out = subprocess.run(['readelf', '-d', lib], capture_output=True,
                             text=True).stdout
    except OSError:
        return '', ''
    for rt, link in (('libomp.so', 'omp'), ('libgomp.so', 'gomp')):
        if rt in out:
            for root in search_roots:
                hit = _find_lib(root, [rt, rt + '.*'])
                if hit:
                    return os.path.dirname(hit), link
            return '', link
    return '', ''


def postprocess(i):
    env = i['env']

    use_aocl = env.get('MLC_HOST_PLATFORM_FLAVOR', '') == 'x86_64' and \
        not is_true(env.get('MLC_BLAS_LAPACK_FORCE_OPENBLAS', ''))

    if not use_aocl:
        env['MLC_BLAS_LAPACK_VENDOR'] = 'openblas'
        env['BLA_VENDOR'] = 'OpenBLAS'
        env['MLC_BLAS_LIBS'] = '-lopenblas'
        env['MLC_LAPACK_LIBS'] = '-lopenblas'
        env['MLC_BLAS_LIBRARIES'] = 'openblas'
        env['MLC_LAPACK_LIBRARIES'] = 'openblas'
    else:
        blis = _find_lib(env.get('MLC_AOCL_BLIS_LIB_PATH', ''),
                         ['libblis-mt.so', 'libblis-mt.a', 'libblis.so', 'libblis.a'])
        flame = _find_lib(env.get('MLC_AOCL_LIBFLAME_LIB_PATH', ''),
                          ['libflame.so', 'libflame.a'])
        aoclutils = _find_lib(env.get('MLC_AOCL_UTILS_LIB_PATH', ''),
                              ['libaoclutils.so', 'libaoclutils.a'])
        if not blis or not flame:
            return {'return': 1, 'error': 'AOCL BLIS/libflame libraries not found '
                    f'(blis={blis!r}, flame={flame!r})'}

        lib_dirs = []
        for lib in (blis, flame, aoclutils):
            if lib and os.path.dirname(lib) not in lib_dirs:
                lib_dirs.append(os.path.dirname(lib))

        omp_dir, omp_link = _openmp_runtime(
            blis, [env.get('MLC_AOCL_BLIS_LIB_PATH', ''), '/usr/lib', '/usr/lib64'])
        if omp_dir and omp_dir not in lib_dirs:
            lib_dirs.append(omp_dir)

        blis_flags = f"-L{os.path.dirname(blis)} -l{_link_name(blis)}"
        omp_flags = (f"-L{omp_dir} " if omp_dir else '') + \
            (f"-l{omp_link}" if omp_link else '')
        blas_libs = f"{blis_flags} {omp_flags} -lm -lpthread".replace('  ', ' ')
        lapack_libs = f"-L{os.path.dirname(flame)} -lflame"
        if aoclutils:
            lapack_libs += f" -L{os.path.dirname(aoclutils)} -laoclutils"

        env['MLC_BLAS_LAPACK_VENDOR'] = 'aocl'
        env['BLA_VENDOR'] = 'AOCL_mt' if '-mt' in _link_name(blis) else 'AOCL'
        env['MLC_BLAS_LIBS'] = blas_libs
        env['MLC_LAPACK_LIBS'] = f"{lapack_libs} {blas_libs}"
        env['MLC_BLAS_LIBRARIES'] = blis
        env['MLC_LAPACK_LIBRARIES'] = ';'.join(
            [flame] + ([aoclutils] if aoclutils else []) + [blis])
        env['MLC_BLAS_LAPACK_LIB_DIRS'] = ':'.join(lib_dirs)
        env['+LD_LIBRARY_PATH'] = lib_dirs
        env['+LIBRARY_PATH'] = lib_dirs

    # autoconf AX_BLAS/AX_LAPACK conventions.
    env['BLAS_LIBS'] = env['MLC_BLAS_LIBS']
    env['LAPACK_LIBS'] = env['MLC_LAPACK_LIBS']

    return {'return': 0}
