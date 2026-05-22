from mlc import utils
import os
import shutil
from utils import *


def preprocess(i):

    os_info = i['os_info']

    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported in this script yet'}
    env = i['env']
    state = i['state']

    # Patch nvmitten tree.py to tolerate duplicate keys (e.g. duplicate "model name"
    # entries from lscpu -J on hybrid-core or multi-socket systems).
    try:
        import nvmitten.tree as _nvmitten_tree_mod
        _tree_py_path = _nvmitten_tree_mod.__file__
        with open(_tree_py_path, 'r') as _f:
            _tree_src = _f.read()
        if 'raise ValueError(f"Cannot insert node with duplicate name {child_node.name}")' in _tree_src and '_MLC_PATCHED_' not in _tree_src:
            _tree_src = _tree_src.replace(
                '        if child_node.name in self.children:\n'
                '            raise ValueError(f"Cannot insert node with duplicate name {child_node.name}")\n'
                '        self.children[child_node.name] = child_node',
                '        # _MLC_PATCHED_ tolerate duplicate keys from lscpu\n'
                '        if child_node.name in self.children:\n'
                '            self.children[child_node.name].value = child_node.value\n'
                '            return\n'
                '        self.children[child_node.name] = child_node')
            with open(_tree_py_path, 'w') as _f:
                _f.write(_tree_src)
    except (ImportError, OSError):
        pass

    # Patch submission_checker/__init__.py if empty to expose ACC_PATTERN / MODEL_CONFIG
    # The NVIDIA harness does `import submission_checker; submission_checker.ACC_PATTERN`
    # but upstream __init__.py is empty; constants live in
    # submission_checker/constants.py
    nvidia_code_path = env.get('MLC_MLPERF_INFERENCE_NVIDIA_CODE_PATH', '')
    if nvidia_code_path:
        submission_checker_init = os.path.join(
            nvidia_code_path, 'build', 'inference', 'tools', 'submission',
            'submission_checker', '__init__.py')
        if os.path.isfile(submission_checker_init):
            with open(submission_checker_init, 'r') as _f:
                _content = _f.read().strip()
            if not _content:
                with open(submission_checker_init, 'w') as _f:
                    _f.write('from submission_checker.constants import *\n')

    if env.get('MLC_MODEL', '') == '':
        return {
            'return': 1, 'error': 'Please select a variation specifying the model to run'}

    make_command = env['MLPERF_NVIDIA_RUN_COMMAND']

    if env.get('MLC_MLPERF_DEVICE', '') == '':
        return {
            'return': 1, 'error': 'Please select a variation specifying the device to run on'}

    if is_true(env.get('MLC_MLPERF_SKIP_RUN', '')
               ) and make_command == "run_harness":
        return {'return': 0}

    env['MLPERF_SCRATCH_PATH'] = env['MLC_NVIDIA_MLPERF_SCRATCH_PATH']

    cmds = []
    scenario = env['MLC_MLPERF_LOADGEN_SCENARIO']
    mode = env['MLC_MLPERF_LOADGEN_MODE']

    make_command = env['MLPERF_NVIDIA_RUN_COMMAND']

    # For BERT on v6.0+ NVIDIA harness: inject minimal config and bert fields module so that
    # custom (non-NVIDIA-official) systems fall back to configs/minimal/ and find a bert config.
    # Applied idempotently so the container always has the correct files.
    _inference_version = env.get('MLC_MLPERF_INFERENCE_CODE_VERSION', '')
    if _inference_version >= 'v6.0' and nvidia_code_path:
        # Create 3rdparty/mlc-inference symlink to mlcommons/inference source and 3rdparty/trtllm
        # as an empty directory. This must happen BEFORE paths.py is first imported by the harness,
        # so that _verify_path() sees the symlink/dir and doesn't try to create
        # empty directories.
        _3rdparty_dir = os.path.join(nvidia_code_path, '3rdparty')
        os.makedirs(_3rdparty_dir, exist_ok=True)
        _mlc_inf_link = os.path.join(_3rdparty_dir, 'mlc-inference')
        _mlcommons_inf_src = env.get('MLC_MLPERF_INFERENCE_SOURCE', '')
        if os.path.islink(_mlc_inf_link) and not os.path.exists(_mlc_inf_link):
            os.unlink(_mlc_inf_link)  # Remove broken symlink
        if not os.path.exists(_mlc_inf_link) and _mlcommons_inf_src:
            os.symlink(_mlcommons_inf_src, _mlc_inf_link)
        os.makedirs(os.path.join(_3rdparty_dir, 'trtllm'), exist_ok=True)

        # Install nvmitten.configurator stub if the full module is absent (outside official Docker).
        # nvmitten v0.2.0 on PyPI only has a stub __init__.py without the configurator module.
        # The full nvmitten is shipped inside the official NVIDIA Docker image.
        import site as _site
        for _sp in (_site.getsitepackages() + [_site.getusersitepackages()]):
            _nvm_init = os.path.join(_sp, 'nvmitten', '__init__.py')
            if os.path.isfile(_nvm_init):
                _nvm_cfg_dir = os.path.join(_sp, 'nvmitten', 'configurator')
                _nvm_cfg_file = os.path.join(
                    _sp, 'nvmitten', 'configurator.py')
                # Check if proper configurator package is missing or is the old
                # no-op version
                _nvm_core = os.path.join(_nvm_cfg_dir, '_core.py')
                _needs_install = (
                    not os.path.isdir(_nvm_cfg_dir) and not os.path.isfile(_nvm_cfg_file))
                _needs_update = (os.path.isfile(_nvm_core) and (
                    '_parse_argv' not in open(_nvm_core).read() or
                    'load_module' not in open(_nvm_core).read() or
                    'def __setitem__' not in open(_nvm_core).read()))
                if _needs_install or _needs_update:
                    os.makedirs(_nvm_cfg_dir, exist_ok=True)
                    _nvm_cfg_init = os.path.join(_nvm_cfg_dir, '__init__.py')
                    with open(_nvm_cfg_init, 'w') as _f:
                        _f.write('from .fields import Field, AutoConfStrategy\n'
                                 'from ._core import Configuration, ConfigurationIndex, HelpInfo, bind, autoconfigure\n'
                                 '__all__ = ["Field", "AutoConfStrategy", "Configuration", '
                                 '"ConfigurationIndex", "HelpInfo", "bind", "autoconfigure"]\n')
                    _nvm_cfg_core = os.path.join(_nvm_cfg_dir, '_core.py')
                    with open(_nvm_cfg_core, 'w') as _f:
                        _f.write(
                            'import sys\n'
                            'import inspect\n'
                            '\n'
                            '_class_bindings = {}\n'
                            '_parsed_values = {}\n'
                            '_current_config = None  # Set to the Configuration instance during config.autoapply()\n'
                            '\n'
                            '\n'
                            'def _parse_argv():\n'
                            '    result = {}\n'
                            '    args = sys.argv[1:]\n'
                            '    i = 0\n'
                            '    while i < len(args):\n'
                            '        arg = args[i]\n'
                            '        if arg.startswith(\'--\'):\n'
                            '            arg = arg[2:]\n'
                            '            if \'=\' in arg:\n'
                            '                key, val = arg.split(\'=\', 1)\n'
                            '                result[key] = val\n'
                            '            elif i + 1 < len(args) and not args[i + 1].startswith(\'-\'):\n'
                            '                result[arg] = args[i + 1]\n'
                            '                i += 1\n'
                            '            else:\n'
                            '                result[arg] = \'true\'\n'
                            '        i += 1\n'
                            '    return result\n'
                            '\n'
                            '\n'
                            'class _AutoApplyCtx:\n'
                            '    def __init__(self, config=None):\n'
                            '        self.config = config\n'
                            '    def __enter__(self):\n'
                            '        global _parsed_values, _current_config\n'
                            '        _parsed_values = _parse_argv()\n'
                            '        _current_config = self.config\n'
                            '        return self\n'
                            '    def __exit__(self, *a):\n'
                            '        global _parsed_values, _current_config\n'
                            '        _parsed_values = {}\n'
                            '        _current_config = None\n'
                            '        return False\n'
                            '\n'
                            '\n'
                            'class Configuration:\n'
                            '    def __init__(self, data=None):\n'
                            '        self._data = dict(data) if data else {}\n'
                            '\n'
                            '    def autoapply(self): return _AutoApplyCtx(self)\n'
                            '    def __enter__(self): return self\n'
                            '    def __exit__(self, *a): return False\n'
                            '    def __setitem__(self, key, value): self._data[key] = value\n'
                            '    def __getitem__(self, key): return self._data[key]\n'
                            '    def __contains__(self, key): return key in self._data\n'
                            '    def __iter__(self): return iter(self._data)\n'
                            '    def items(self): return self._data.items()\n'
                            '    def get(self, key, default=None): return self._data.get(key, default)\n'
                            '    def update(self, other): self._data.update(other)\n'
                            '    def __repr__(self): return f\'Configuration({self._data!r})\'\n'
                            '\n'
                            '\n'
                            'class ConfigurationIndex:\n'
                            '    def __init__(self, *a, **kw):\n'
                            '        self._store = {}\n'
                            '\n'
                            '    def load_module(self, imp_path, prefix=None):\n'
                            '        import importlib\n'
                            '        prefix = list(prefix) if prefix else []\n'
                            '        try:\n'
                            '            if imp_path in sys.modules:\n'
                            '                del sys.modules[imp_path]\n'
                            '            parent = imp_path.split(\'.\')[0]\n'
                            '            if parent in sys.modules:\n'
                            '                del sys.modules[parent]\n'
                            '            mod = importlib.import_module(imp_path)\n'
                            '        except Exception:\n'
                            '            return\n'
                            '        exports = getattr(mod, \'EXPORTS\', {})\n'
                            '        for workload_setting, cfg in exports.items():\n'
                            '            key = tuple(prefix) + (workload_setting,)\n'
                            '            self._store[key] = cfg\n'
                            '\n'
                            '    def get(self, keyspace):\n'
                            '        raw = self._store.get(tuple(keyspace), None)\n'
                            '        if raw is None:\n'
                            '            return None\n'
                            '        return Configuration(raw)\n'
                            '\n'
                            '\n'
                            'class HelpInfo:\n'
                            '    @staticmethod\n'
                            '    def add_configurator_dependency(*a, **kw): pass\n'
                            '\n'
                            '\n'
                            'def bind(field, *aliases):\n'
                            '    def decorator(cls):\n'
                            '        if cls not in _class_bindings:\n'
                            '            _class_bindings[cls] = []\n'
                            '        _class_bindings[cls].append(field)\n'
                            '        return cls\n'
                            '    if hasattr(field, \'name\') and hasattr(field, \'from_string\'):\n'
                            '        return decorator\n'
                            '    return field\n'
                            '\n'
                            '\n'
                            'def autoconfigure(cls):\n'
                            '    original_init = cls.__init__\n'
                            '    try:\n'
                            '        sig = inspect.signature(original_init)\n'
                            '        explicit_params = frozenset(\n'
                            '            name for name, p in sig.parameters.items()\n'
                            '            if p.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD,\n'
                            '                          inspect.Parameter.KEYWORD_ONLY)\n'
                            '        )\n'
                            '    except Exception:\n'
                            '        explicit_params = None\n'
                            '    def new_init(self, *args, **kwargs):\n'
                            '        for f in _class_bindings.get(cls, []):\n'
                            '            if f.name not in kwargs:\n'
                            '                if explicit_params is not None and f.name not in explicit_params:\n'
                            '                    continue\n'
                            '                if _current_config is not None:\n'
                            '                    val = _current_config.get(f)\n'
                            '                    if val is not None:\n'
                            '                        if isinstance(val, str) and f.from_string is not None:\n'
                            '                            try: val = f.from_string(val)\n'
                            '                            except Exception: pass\n'
                            '                        kwargs[f.name] = val\n'
                            '                        continue\n'
                            '                raw = _parsed_values.get(f.name)\n'
                            '                if raw is not None:\n'
                            '                    if f.from_string is not None:\n'
                            '                        try: kwargs[f.name] = f.from_string(raw)\n'
                            '                        except Exception: kwargs[f.name] = raw\n'
                            '                    else: kwargs[f.name] = raw\n'
                            '                elif f.default is not None:\n'
                            '                    kwargs[f.name] = f.default\n'
                            '        original_init(self, *args, **kwargs)\n'
                            '    cls.__init__ = new_init\n'
                            '    return cls\n'
                            '\n'
                        )
                    _nvm_cfg_fields = os.path.join(_nvm_cfg_dir, 'fields.py')
                    with open(_nvm_cfg_fields, 'w') as _f:
                        _f.write('from enum import Enum, auto\n\n\n'
                                 'class AutoConfStrategy(Enum):\n'
                                 '    Default = auto()\n'
                                 '    DictUpdate = auto()\n'
                                 '    Override = auto()\n\n\n'
                                 'class Field:\n'
                                 '    def __init__(self, name, description="", from_string=None, '
                                 'default=None, autoconf_strategy=None, **kw):\n'
                                 '        self.name = name; self.description = description\n'
                                 '        self.from_string = from_string; self.default = default\n'
                                 '        self.autoconf_strategy = autoconf_strategy\n'
                                 '    def __repr__(self): return f"Field({self.name!r})"\n'
                                 '    def __hash__(self): return hash(self.name)\n'
                                 '    def __eq__(self, other):\n'
                                 '        return self.name == other.name if isinstance(other, Field) else NotImplemented\n')

                # Also export System from nvmitten.system if missing
                _nvm_sys_init = os.path.join(
                    _sp, 'nvmitten', 'system', '__init__.py')
                if os.path.isfile(_nvm_sys_init):
                    with open(_nvm_sys_init, 'r') as _f:
                        _sys_content = _f.read()
                    if 'from nvmitten.system.system import System' not in _sys_content:
                        with open(_nvm_sys_init, 'a') as _f:
                            _f.write(
                                '\nfrom nvmitten.system.system import System\n')

                # Fix nvmitten AliasedNameEnum.valstr: PyPI v0.2.0 defines valstr() as a plain
                # method, but v6.0 harness code accesses it as a property (arch.valstr, not arch.valstr()).
                # Add the @property decorator if missing.
                _nvm_alias = os.path.join(_sp, 'nvmitten', 'aliased_name.py')
                if os.path.isfile(_nvm_alias):
                    with open(_nvm_alias, 'r') as _f:
                        _alias_src = _f.read()
                    if '    def valstr(self)' in _alias_src and '    @property\n    def valstr(self)' not in _alias_src:
                        _alias_src = _alias_src.replace(
                            '    def valstr(self)',
                            '    @property\n    def valstr(self)')
                        with open(_nvm_alias, 'w') as _f:
                            _f.write(_alias_src)

                # Fix nvmitten/nvidia/builder.py: normalize enum-like input_dtype/input_format
                # to strings before the type assertion in TRTBuilder.
                _nvm_builder = os.path.join(
                    _sp, 'nvmitten', 'nvidia', 'builder.py')
                if os.path.isfile(_nvm_builder):
                    with open(_nvm_builder, 'r') as _f:
                        _builder_src = _f.read()
                    _builder_new = (
                        '        def _mlc_valstr_or_self(_value):\n'
                        '            return _value.valstr if hasattr(_value, "valstr") else _value\n'
                        '        self.input_dtype = _mlc_valstr_or_self(self.input_dtype)\n'
                        '        self.input_format = _mlc_valstr_or_self(self.input_format)\n'
                        '        assert type(self.input_dtype) == type(self.input_format), "input_dtype and input_format must be the same type"')
                    _builder_old_double = (
                        '        assert type(self.input_dtype) == type(self.input_format), '
                        '"input_dtype and input_format must be the same type"')
                    _builder_old_single = (
                        "        assert type(self.input_dtype) == type(self.input_format), "
                        "'input_dtype and input_format must be the same type'")
                    if '_mlc_valstr_or_self' not in _builder_src:
                        if _builder_old_double in _builder_src:
                            _builder_src = _builder_src.replace(
                                _builder_old_double, _builder_new, 1)
                        elif _builder_old_single in _builder_src:
                            _builder_src = _builder_src.replace(
                                _builder_old_single, _builder_new, 1)
                        if '_mlc_valstr_or_self' in _builder_src:
                            with open(_nvm_builder, 'w') as _f:
                                _f.write(_builder_src)

                # Fix nvmitten/pipeline/pipeline.py: preserve KeyboardInterrupt instance.
                # Upstream code sets `exc = KeyboardInterrupt` (the class), then traceback
                # extraction crashes on Python 3.12 with: "'getset_descriptor' object has
                # no attribute 'tb_frame'" and masks the real underlying
                # failure.
                _nvm_pipeline = os.path.join(
                    _sp, 'nvmitten', 'pipeline', 'pipeline.py')
                if os.path.isfile(_nvm_pipeline):
                    with open(_nvm_pipeline, 'r') as _f:
                        _pipeline_src = _f.read()
                    _needle = 'except KeyboardInterrupt as _exc:\n                exc = KeyboardInterrupt\n                status = OperationStatus.INTERRUPTED'
                    _fixed = 'except KeyboardInterrupt as _exc:\n                exc = _exc\n                status = OperationStatus.INTERRUPTED'
                    if _needle in _pipeline_src:
                        _pipeline_src = _pipeline_src.replace(
                            _needle, _fixed, 1)
                        with open(_nvm_pipeline, 'w') as _f:
                            _f.write(_pipeline_src)
                continue

        # Fix code/resnet50/tensorrt/builder.py:
        # 1. object.__init__() in the MRO does not accept calib_data_dir
        # 2. create_builder_config() accesses self.calibrator unconditionally but
        # set_calibrator() only sets it for INT8 precision. Guard the access.
        import subprocess as _sp
        _git_dir = os.path.abspath(
            os.path.join(
                nvidia_code_path,
                '..',
                '..'))  # repo root
        _resnet_builder_py = os.path.join(
            nvidia_code_path,
            'code',
            'resnet50',
            'tensorrt',
            'builder.py')
        if os.path.isfile(_resnet_builder_py):
            # Restore original from git to ensure current patch version applies
            _rel_rb_path = 'closed/NVIDIA/code/resnet50/tensorrt/builder.py'
            try:
                _sp.check_output(['git', 'checkout', 'HEAD', '--', _rel_rb_path],
                                 cwd=_git_dir, stderr=_sp.STDOUT)
            except Exception:
                # Fallback: if already patched, restore original line
                with open(_resnet_builder_py, 'r') as _f:
                    _tmp = _f.read()
                if '_MLC_PATCHED_' in _tmp or 'hasattr(self, "calibrator")' in _tmp:
                    _tmp = _tmp.replace(
                        'if hasattr(self, "calibrator") and self.calibrator is not None:\n'
                        '            builder_config.int8_calibrator = self.calibrator',
                        'builder_config.int8_calibrator = self.calibrator')
                    # Remove any previous MLC patch block
                    import re as _re
                    _tmp = _re.sub(r'\n        # _MLC_PATCHED_.*?(?=\n        if self\.energy_aware_kernels|\n        return builder_config)',
                                   '', _tmp, flags=_re.DOTALL)
                    with open(_resnet_builder_py, 'w') as _f:
                        _f.write(_tmp)
            with open(_resnet_builder_py, 'r') as _f:
                _resnet_builder_src = _f.read()
            _changed_rb = False
            _resnet_builder_src_escaped = _resnet_builder_src.replace(
                ' \\+ ', ' \\\\+ ')
            if _resnet_builder_src_escaped != _resnet_builder_src:
                _resnet_builder_src = _resnet_builder_src_escaped
                _changed_rb = True
            # Replace the unconditional self.calibrator access with a robust fallback:
            # If set_calibrator was called, use self.calibrator.
            # If not, but cache_file exists and precision is INT8, create a
            # cache-only calibrator.
            _old_calib_line = 'builder_config.int8_calibrator = self.calibrator'
            _new_calib_block = (
                '# _MLC_PATCHED_ calibrator access\n'
                '        if hasattr(self, "calibrator") and self.calibrator is not None:\n'
                '            builder_config.int8_calibrator = self.calibrator\n'
                '        elif self.precision == Precision.INT8 and hasattr(self, "cache_file") and self.cache_file.exists():\n'
                '            import tensorrt as _trt\n'
                '            class _FallbackCalib(_trt.IInt8EntropyCalibrator2):\n'
                '                def __init__(self, cache_path):\n'
                '                    super().__init__()\n'
                '                    self._cache = cache_path\n'
                '                def get_batch_size(self): return 1\n'
                '                def get_batch(self, names, p_gpu_mem): return None\n'
                '                def read_calibration_cache(self):\n'
                '                    return self._cache.read_bytes()\n'
                '                def write_calibration_cache(self, cache): pass\n'
                '            builder_config.int8_calibrator = _FallbackCalib(self.cache_file)')
            if _old_calib_line in _resnet_builder_src:
                _resnet_builder_src = _resnet_builder_src.replace(
                    _old_calib_line, _new_calib_block, 1)
                _changed_rb = True
            if _changed_rb:
                with open(_resnet_builder_py, 'w') as _f:
                    _f.write(_resnet_builder_src)

        # Patch generate_engines.py to handle calib_data_dir being None or calibration
        # data not existing on disk. When the calibration cache already exists, the TRT
        # builder only needs cache data (quantization ranges), not actual images.
        # We create a lightweight cache-only calibrator in that case.
        _gen_eng_path = os.path.join(
            nvidia_code_path, 'code', 'ops', 'generate_engines.py')
        if os.path.isfile(_gen_eng_path):
            # Restore the original file from git to ensure we always apply our CURRENT patch
            # (handles case where an older version of the patch was applied during Docker build)
            _rel_path = 'closed/NVIDIA/code/ops/generate_engines.py'
            try:
                _sp.check_output(['git', 'checkout', 'HEAD', '--', _rel_path],
                                 cwd=_git_dir, stderr=_sp.STDOUT)
            except Exception:
                # Fallback: if old patch is present, manually restore the
                # original pattern
                with open(_gen_eng_path, 'r') as _f:
                    _tmp = _f.read()
                if '_CacheCalib' in _tmp:
                    import re as _re
                    # Replace the entire patched isinstance block with the
                    # original
                    _pattern = _re.compile(
                        r'if isinstance\(builder, CalibratableTensorRTEngine\):.*?'
                        r'(?=\n                network = builder\.create_network)',
                        _re.DOTALL)
                    _orig_block = ('if isinstance(builder, CalibratableTensorRTEngine):\n'
                                   '                    builder.set_calibrator(scratch_space.path.joinpath("preprocessed_data",\n'
                                   '                                                                       builder.calib_data_dir))')
                    _tmp = _pattern.sub(_orig_block, _tmp)
                    with open(_gen_eng_path, 'w') as _f:
                        _f.write(_tmp)
            with open(_gen_eng_path, 'r') as _f:
                _gen_eng = _f.read()
            _changed_ge = False
            # Patch EngineBuilderOp.run()
            _old_pattern = (
                'if isinstance(builder, CalibratableTensorRTEngine):\n'
                '                    builder.set_calibrator(scratch_space.path.joinpath("preprocessed_data",\n'
                '                                                                       builder.calib_data_dir))'
            )
            _new_pattern = (
                'if isinstance(builder, CalibratableTensorRTEngine):\n'
                '                    _calib_data_path = None\n'
                '                    if builder.calib_data_dir is not None:\n'
                '                        _calib_data_path = scratch_space.path.joinpath("preprocessed_data", builder.calib_data_dir)\n'
                '                    logging.info(f"[MLC] calib_data_dir={builder.calib_data_dir!r}, exists={_calib_data_path.exists() if _calib_data_path else None}, need_calibration={builder.need_calibration}")\n'
                '                    if _calib_data_path is not None and _calib_data_path.exists():\n'
                '                        builder.set_calibrator(_calib_data_path)\n'
                '                        logging.info(f"[MLC] set_calibrator called, calibrator={getattr(builder, \'calibrator\', None)}")\n'
                '                    elif not builder.need_calibration:\n'
                '                        import tensorrt as _trt\n'
                '                        class _CacheCalib(_trt.IInt8EntropyCalibrator2):\n'
                '                            def __init__(self, cache_path):\n'
                '                                super().__init__()\n'
                '                                self._cache = cache_path\n'
                '                            def get_batch_size(self): return 1\n'
                '                            def get_batch(self, names, p_gpu_mem): return None\n'
                '                            def read_calibration_cache(self):\n'
                '                                if self._cache.exists():\n'
                '                                    return self._cache.read_bytes()\n'
                '                                return None\n'
                '                            def write_calibration_cache(self, cache): pass\n'
                '                        builder.calibrator = _CacheCalib(builder.cache_file)\n'
                '                        logging.info(f"[MLC] _CacheCalib fallback used, cache_file={builder.cache_file}, exists={builder.cache_file.exists()}")'
            )
            if _old_pattern in _gen_eng:
                _gen_eng = _gen_eng.replace(_old_pattern, _new_pattern)
                _changed_ge = True
            # Patch CalibrateEngineOp.run() - guard against None calib_data_dir
            _old_calib = (
                'if builder.need_calibration:\n'
                '                builder.set_calibrator(scratch_space.path.joinpath("preprocessed_data",\n'
                '                                                                   builder.calib_data_dir))'
            )
            _new_calib = (
                'if builder.need_calibration and builder.calib_data_dir is not None:\n'
                '                builder.set_calibrator(scratch_space.path.joinpath("preprocessed_data",\n'
                '                                                                   builder.calib_data_dir))'
            )
            if _old_calib in _gen_eng:
                _gen_eng = _gen_eng.replace(_old_calib, _new_calib)
                _changed_ge = True
            if _changed_ge:
                with open(_gen_eng_path, 'w') as _f:
                    _f.write(_gen_eng)

        # Patch code/main.py to tolerate class objects for power_context.
        # Some harness versions pass a class (ABCMeta) instead of an instance,
        # causing `with power_context:` to crash with TypeError.
        _main_py = os.path.join(nvidia_code_path, 'code', 'main.py')
        if os.path.isfile(_main_py):
            with open(_main_py, 'r') as _f:
                _main_src = _f.read()
            _main_old = 'with power_context:'
            _main_new = 'with (power_context() if isinstance(power_context, type) else power_context):  # _MLC_PATCHED_power_context'
            if '_MLC_PATCHED_power_context' not in _main_src and _main_old in _main_src:
                _main_src = _main_src.replace(_main_old, _main_new, 1)
                with open(_main_py, 'w') as _f:
                    _f.write(_main_src)

    # Patch rn50_graphsurgeon.py to disable custom TRT fusion plugins (RnRes2FullFusion_TRT,
    # SmallTileGEMM_TRT) which are broken on TensorRT 10.x with non-official NVIDIA GPUs.
    # These plugins produce garbage output (constant class 600). Disabling them lets TRT use
    # its native kernels which produce correct 76%+ accuracy.
    if env.get(
            'MLC_MODEL', '') == 'resnet50' and nvidia_code_path and _inference_version >= 'v6.0':
        _rn50_gs_path = os.path.join(
            nvidia_code_path,
            'code',
            'resnet50',
            'tensorrt',
            'rn50_graphsurgeon.py')
        if os.path.isfile(_rn50_gs_path):
            with open(_rn50_gs_path, 'r') as _f:
                _rn50_gs = _f.read()
            _changed_gs = False
            # Add 'import os' if missing
            if 'import os' not in _rn50_gs:
                _rn50_gs = _rn50_gs.replace(
                    'import argparse', 'import argparse\nimport os', 1)
                _changed_gs = True
            # Patch no_fuse logic to check MLPERF_RN50_DISABLE_FUSIONS env var
            _old_nofuse = "no_fuse = (device_type != 'gpu') or (need_calibration)"
            _new_nofuse = "no_fuse = (device_type != 'gpu') or (need_calibration) or os.environ.get('MLPERF_RN50_DISABLE_FUSIONS', '0') == '1'"
            if _old_nofuse in _rn50_gs and 'MLPERF_RN50_DISABLE_FUSIONS' not in _rn50_gs:
                _rn50_gs = _rn50_gs.replace(_old_nofuse, _new_nofuse)
                _changed_gs = True
            if _changed_gs:
                with open(_rn50_gs_path, 'w') as _f:
                    _f.write(_rn50_gs)
        env['MLPERF_RN50_DISABLE_FUSIONS'] = '1'

    # For retinanet on v6.0+: create minimal config if missing (v6.0 NVIDIA submission
    # dropped retinanet configs for B200/B300, so we need to provide one for
    # custom systems).
    if env.get(
            'MLC_MODEL', '') == 'retinanet' and _inference_version >= 'v6.0' and nvidia_code_path:
        _retinanet_config_content = (
            'import code.common.constants as C\n'
            'import code.fields.models as model_fields\n'
            'import code.fields.loadgen as loadgen_fields\n'
            'import code.fields.harness as harness_fields\n\n'
            'base = {\n'
            "    model_fields.gpu_batch_size: {\n"
            "        'retinanet': 2,\n"
            '    },\n'
            "    model_fields.precision: 'int8',\n"
            "    model_fields.input_dtype: 'int8',\n"
            "    model_fields.input_format: 'linear',\n"
            "    harness_fields.tensor_path: 'build/preprocessed_data/open-images-v6-mlperf/validation/Retinanet/int8_linear',\n"
            "    harness_fields.map_path: 'data_maps/open-images-v6-mlperf/val_map.txt',\n"
            '    loadgen_fields.offline_expected_qps: 100,\n'
            '    harness_fields.use_graphs: True,\n'
            '}\n\n'
            'EXPORTS = {\n'
            '    C.WorkloadSetting(C.HarnessType.Custom, C.AccuracyTarget(0.99), C.PowerSetting.MaxP): base,\n'
            '}\n'
        )
        for _scen_dir in ['Offline', 'SingleStream', 'MultiStream', 'Server']:
            _retinanet_cfg = os.path.join(
                nvidia_code_path,
                'configs',
                'minimal',
                _scen_dir,
                'retinanet.py')
            if os.path.isdir(os.path.dirname(_retinanet_cfg)
                             ) and not os.path.isfile(_retinanet_cfg):
                with open(_retinanet_cfg, 'w') as _f:
                    _f.write(_retinanet_config_content)

    # For GPTJ on post-5.0 NVIDIA harness: apply persistent patches that survive container restarts.
    # These are applied idempotently every run so a fresh container gets them
    # automatically.
    if "gptj" in env.get('MLC_MODEL', '') and is_true(
            env.get('MLC_MLPERF_INFERENCE_POST_5_0')) and nvidia_code_path:
        import json as _json
        import site as _site

        # --- Patch A: modelopt QKV merge OOM-safe fallback ---
        _sp_dirs = _site.getsitepackages() + [_site.getusersitepackages()]
        for _sp in _sp_dirs:
            _mc_path = os.path.join(
                _sp, 'modelopt', 'torch', 'export', 'model_config.py')
            if os.path.isfile(_mc_path):
                with open(_mc_path, 'r') as _f:
                    _mc = _f.read()
                if 'OutOfMemoryError' not in _mc:
                    _old = 'return torch.cat((self.q.weight, self.k.weight, self.v.weight))'
                    _new = ('try:\n'
                            '            return torch.cat((self.q.weight, self.k.weight, self.v.weight))\n'
                            '        except (torch.cuda.OutOfMemoryError, RuntimeError):\n'
                            '            import gc; gc.collect(); torch.cuda.empty_cache()\n'
                            '            return torch.cat((self.q.weight.cpu(), self.k.weight.cpu(), self.v.weight.cpu()))')
                    if _old in _mc:
                        with open(_mc_path, 'w') as _f:
                            _f.write(_mc.replace(_old, _new, 1))
                break

        # --- Patch B: write fp8 custom.py for all registered custom systems ---
        _custom_list_path = os.path.join(
            nvidia_code_path,
            'code',
            'common',
            'systems',
            'custom_list.json')
        if os.path.isfile(_custom_list_path):
            with open(_custom_list_path) as _f:
                _custom_systems = _json.load(_f)
            _gptj_scenarios = [
                'Offline',
                'Server',
                'SingleStream',
                'MultiStream']
            for _sys_name in _custom_systems:
                for _scen in _gptj_scenarios:
                    _custom_py = os.path.join(
                        nvidia_code_path, 'configs', 'gptj', _scen, 'custom.py')
                    if not os.path.isdir(os.path.dirname(_custom_py)):
                        continue
                    _needs_update = True
                    if os.path.isfile(_custom_py):
                        with open(_custom_py) as _f:
                            _content = _f.read()
                        if f'class {_sys_name}(' in _content and "'fp8'" in _content:
                            _needs_update = False
                    if _needs_update:
                        _header = ('# Generated file by scripts/custom_systems/add_custom_system.py\n'
                                   f'# Contains configs for all custom systems in code/common/systems/custom_list.json\n'
                                   '\nfrom . import *\n\n\n')
                        _base_cls = 'OfflineGPUBaseConfig' if _scen == 'Offline' else f'{_scen}GPUBaseConfig'
                        _cls_body = (
                            f'@ConfigRegistry.register(HarnessType.Custom, AccuracyTarget.k_99, PowerSetting.MaxP)\n'
                            f'class {_sys_name}({_base_cls}):\n'
                            f"    system = KnownSystem.{_sys_name}\n"
                            f"    precision = \"fp8\"\n"
                            f"    enable_sort = False\n"
                            f"    gpu_batch_size = {{'gptj': 8}}\n"
                            f"    offline_expected_qps = 2.0\n"
                            f"    trtllm_checkpoint_flags = {{\n"
                            f"        'kv_cache_dtype': 'fp8'\n"
                            f"    }}\n\n\n"
                            f'@ConfigRegistry.register(HarnessType.Custom, AccuracyTarget.k_99_9, PowerSetting.MaxP)\n'
                            f'class {_sys_name}_HighAccuracy({_sys_name}):\n'
                            f'    pass\n'
                        )
                        with open(_custom_py, 'w') as _f:
                            _f.write(_header + _cls_body)
        else:
            # custom_list.json doesn't exist yet — register the system first
            add_custom_script = os.path.join(
                nvidia_code_path,
                'scripts',
                'custom_systems',
                'add_custom_system.py')
            if os.path.isfile(add_custom_script):
                cmds.insert(
                    0,
                    f'cd {nvidia_code_path} && python3 scripts/custom_systems/add_custom_system.py')
            # else: v6.0+ uses SYSTEM_NAME env var, no add_custom_system.py

    if make_command == "prebuild":
        cmds.append(f"""make prebuild NETWORK_NODE=SUT""")

    if env['MLC_MODEL'] == "resnet50":
        target_data_path = os.path.join(
            env['MLPERF_SCRATCH_PATH'], 'data', 'imagenet')
        dataset_path = env['MLC_DATASET_IMAGENET_PATH']
        # Always update symlink in case it points to a stale/wrong path
        if not os.path.exists(target_data_path) or (
                os.path.islink(target_data_path) and
                os.readlink(target_data_path) != dataset_path):
            cmds.append(
                f"""ln -sfn {dataset_path} {target_data_path}""")

        model_path = os.path.join(
            env['MLPERF_SCRATCH_PATH'],
            'models',
            'ResNet50',
            'resnet50_v1.onnx')

        if not os.path.exists(os.path.dirname(model_path)):
            cmds.append(f"""mkdir -p {os.path.dirname(model_path)}""")

        if not os.path.exists(model_path):
            cmds.append(
                f"""ln -sf {env['MLC_ML_MODEL_FILE_WITH_PATH']} {model_path}""")

        model_name = "resnet50"

    elif "bert" in env['MLC_MODEL']:
        target_data_path = os.path.join(
            env['MLPERF_SCRATCH_PATH'], 'data', 'squad')
        if not os.path.exists(target_data_path):
            cmds.append("make download_data BENCHMARKS='bert'")

        fp32_model_path = os.path.join(
            env['MLPERF_SCRATCH_PATH'],
            'models',
            'bert',
            'bert_large_v1_1.onnx')
        int8_model_path = os.path.join(
            env['MLPERF_SCRATCH_PATH'],
            'models',
            'bert',
            'bert_large_v1_1_fake_quant.onnx')
        vocab_path = os.path.join(
            env['MLPERF_SCRATCH_PATH'],
            'models',
            'bert',
            'vocab.txt')

        if not os.path.exists(os.path.dirname(fp32_model_path)):
            cmds.append(f"""mkdir -p {os.path.dirname(fp32_model_path)}""")

        if not os.path.exists(fp32_model_path):
            cmds.append(
                f"""cp -r --remove-destination {env['MLC_ML_MODEL_BERT_LARGE_FP32_PATH']} {fp32_model_path}""")
        if not os.path.exists(int8_model_path):
            cmds.append(
                f"""cp -r --remove-destination {env['MLC_ML_MODEL_BERT_LARGE_INT8_PATH']} {int8_model_path}""")
        if not os.path.exists(vocab_path):
            cmds.append(
                f"""cp -r --remove-destination {env['MLC_ML_MODEL_BERT_VOCAB_FILE_WITH_PATH']} {vocab_path}""")
        model_name = "bert"
        model_path = fp32_model_path

    elif "stable-diffusion" in env["MLC_MODEL"]:
        target_data_path = os.path.join(
            env['MLPERF_SCRATCH_PATH'], 'data', 'coco', 'SDXL')
        tsv_file = os.path.join(target_data_path, "captions_5k_final.tsv")
        if os.path.exists(tsv_file):
            with open(tsv_file, "r") as file:
                line_count = sum(1 for line in file)
            if env.get('MLC_MLPERF_SUBMISSION_GENERATION_STYLE', '') == 'full':
                if line_count < 5000:
                    shutil.rmtree(target_data_path)
        if not os.path.exists(tsv_file):
            os.makedirs(target_data_path, exist_ok=True)
            # cmds.append("make download_data
            # BENCHMARKS='stable-diffusion-xl'")
            env['MLC_REQUIRE_COCO2014_DOWNLOAD'] = 'yes'
            cmds.append(
                f"""cp -r \\$MLC_DATASET_PATH_ROOT/captions/captions.tsv {target_data_path}/captions_5k_final.tsv""")
            cmds.append(
                f"""cp -r \\$MLC_DATASET_PATH_ROOT/latents/latents.pt {target_data_path}/latents.pt""")
        fp16_model_path = os.path.join(
            env['MLPERF_SCRATCH_PATH'],
            'models',
            'SDXL',
            'official_pytorch',
            'fp16',
            'stable_diffusion_fp16')

        if not os.path.exists(os.path.dirname(fp16_model_path)):
            cmds.append(f"""mkdir -p {os.path.dirname(fp16_model_path)}""")

        if not os.path.exists(fp16_model_path):
            if os.path.islink(fp16_model_path):
                cmds.append(f"rm -f {fp16_model_path}")
            env['MLC_REQUIRE_SDXL_MODEL_DOWNLOAD'] = 'yes'
            cmds.append(f"cp -r \\$SDXL_CHECKPOINT_PATH {fp16_model_path}")

        model_name = "stable-diffusion-xl"
        model_path = fp16_model_path

    elif "3d-unet" in env['MLC_MODEL']:
        target_data_path = os.path.join(
            env['MLPERF_SCRATCH_PATH'],
            'data',
            'KiTS19',
            'kits19',
            'data')
        target_data_path_base_dir = os.path.dirname(target_data_path)
        if not os.path.exists(target_data_path_base_dir):
            cmds.append(f"mkdir -p {target_data_path_base_dir}")

        inference_cases_json_path = os.path.join(
            env['MLPERF_SCRATCH_PATH'], 'data', 'KiTS19', 'inference_cases.json')
        calibration_cases_json_path = os.path.join(
            env['MLPERF_SCRATCH_PATH'], 'data', 'KiTS19', 'calibration_cases.json')

        if not os.path.exists(target_data_path) or not os.path.exists(
                inference_cases_json_path) or not os.path.exists(calibration_cases_json_path):
            # cmds.append(f"ln -sf {env['MLC_DATASET_PATH']}
            # {target_data_path}")
            cmds.append("make download_data BENCHMARKS='3d-unet'")

        model_path = os.path.join(
            env['MLPERF_SCRATCH_PATH'],
            'models',
            '3d-unet-kits19',
            '3dUNetKiTS19.onnx')
        model_name = "3d-unet"

    elif "rnnt" in env['MLC_MODEL']:
        target_data_path = os.path.join(
            env['MLPERF_SCRATCH_PATH'],
            'data',
            'LibriSpeech',
            'dev-clean')
        target_data_path_base_dir = os.path.dirname(target_data_path)
        if not os.path.exists(target_data_path_base_dir):
            cmds.append(f"mkdir -p {target_data_path_base_dir}")
        if not os.path.exists(target_data_path):
            # cmds.append(f"ln -sf {env['MLC_DATASET_LIBRISPEECH_PATH']}
            # {target_data_path}")
            cmds.append("make download_data BENCHMARKS='rnnt'")

        model_path = os.path.join(
            env['MLPERF_SCRATCH_PATH'],
            'models',
            'rnn-t',
            'DistributedDataParallel_1576581068.9962234-epoch-100.pt')
        model_name = "rnnt"

    elif "pdlrm" in env['MLC_MODEL']:
        target_data_path = os.path.join(
            env['MLPERF_SCRATCH_PATH'], 'data', 'criteo')
        if not os.path.exists(target_data_path):
            cmds.append(
                f"ln -sf {env['MLC_DATASET_PREPROCESSED_PATH']} {target_data_path}")

        model_path = os.path.join(
            env['MLPERF_SCRATCH_PATH'],
            'models',
            'dlrm',
            'tb00_40M.pt')
        if not os.path.exists(os.path.dirname(model_path)):
            cmds.append(f"mkdir -p {os.path.dirname(model_path)}")

        if not os.path.exists(model_path):
            cmds.append(
                f"ln -sf {env['MLC_ML_MODEL_FILE_WITH_PATH']} {model_path}")
        model_name = "dlrm"

    elif "dlrm-v2" in env['MLC_MODEL']:
        model_name = "dlrm-v2"

    elif env['MLC_MODEL'] == "retinanet":
        # print(env)
        dataset_path = env['MLC_DATASET_OPENIMAGES_PATH']
        # return {'return': 1, 'error': 'error'}

        annotations_path = env['MLC_DATASET_OPENIMAGES_ANNOTATIONS_DIR_PATH']
        target_data_path_dir = os.path.join(
            env['MLPERF_SCRATCH_PATH'], 'data', 'open-images-v6-mlperf')
        if not os.path.exists(target_data_path_dir):
            cmds.append(f"mkdir -p {target_data_path_dir}")
        target_data_path = os.path.join(target_data_path_dir, 'annotations')
        if not os.path.exists(target_data_path):
            cmds.append(f"ln -sf {annotations_path} {target_data_path}")

        target_data_path_dir = os.path.join(
            env['MLPERF_SCRATCH_PATH'],
            'data',
            'open-images-v6-mlperf',
            'validation')
        if not os.path.exists(target_data_path_dir):
            cmds.append(f"mkdir -p {target_data_path_dir}")
        target_data_path = os.path.join(target_data_path_dir, 'data')
        if not os.path.exists(target_data_path):
            cmds.append(f"ln -sf {dataset_path} {target_data_path}")

        calibration_dataset_path = env['MLC_OPENIMAGES_CALIBRATION_DATASET_PATH']
        target_data_path_dir = os.path.join(
            env['MLPERF_SCRATCH_PATH'],
            'data',
            'open-images-v6-mlperf',
            'calibration',
            'calibration')
        if not os.path.exists(target_data_path_dir):
            cmds.append(f"mkdir -p {target_data_path_dir}")
        target_data_path = os.path.join(target_data_path_dir, 'data')
        if not os.path.exists(target_data_path):
            cmds.append(
                f"ln -sf {calibration_dataset_path} {target_data_path}")

        preprocessed_data_path = os.path.join(
            env['MLPERF_SCRATCH_PATH'], 'preprocessed_data')
        target_model_path_dir = os.path.join(
            env['MLPERF_SCRATCH_PATH'],
            'models',
            'retinanet-resnext50-32x4d')
        if not os.path.exists(target_model_path_dir):
            cmds.append(f"mkdir -p {target_model_path_dir}")
        model_path = os.path.join(
            target_model_path_dir,
            'retinanet-fpn-torch2.1-postprocessed.onnx')
        alt_model_versions = ["2.2", "2.6"]
        alt_model_path = os.path.join(
            target_model_path_dir,
            'retinanet-fpn-torch2.2-postprocessed.onnx')
        if not os.path.exists(model_path):
            for alt_model_version in alt_model_versions:
                alt_model_path = os.path.join(
                    target_model_path_dir,
                    f'retinanet-fpn-torch{alt_model_version}-postprocessed.onnx')
                if os.path.exists(alt_model_path):
                    cmds.append(f"ln -s {alt_model_path} {model_path}")
                    break

        model_name = "retinanet"

    elif "gptj" in env['MLC_MODEL']:
        target_data_path = os.path.join(
            env['MLPERF_SCRATCH_PATH'],
            'data',
            'cnn-daily-mail',
            'cnn_eval.json')
        if not os.path.exists(target_data_path):
            cmds.append("make download_data BENCHMARKS='gptj'")

        fp32_model_path = os.path.join(
            env['MLPERF_SCRATCH_PATH'],
            'models',
            'GPTJ-6B',
            'checkpoint-final')
        fp8_model_path = os.path.join(
            env['MLPERF_SCRATCH_PATH'],
            'models',
            'GPTJ-6B',
            'fp8-quantized-ammo',
            env['MLC_MLPERF_GPTJ_MODEL_FP8_PATH_SUFFIX'])
        vocab_path = os.path.join(
            env['MLPERF_SCRATCH_PATH'],
            'models',
            'bert',
            'vocab.txt')

        if not os.path.exists(os.path.dirname(fp32_model_path)):
            cmds.append(f"mkdir -p {os.path.dirname(fp32_model_path)}")
        if not os.path.exists(os.path.dirname(fp8_model_path)):
            cmds.append(f"mkdir -p {os.path.dirname(fp8_model_path)}")

        if not os.path.exists(fp32_model_path):
            # download via prehook_deps
            env['MLC_REQUIRE_GPTJ_MODEL_DOWNLOAD'] = 'yes'
            if make_command in ["build_engine", "preprocess_data"]:
                cmds.append(
                    f"cp -r $MLC_ML_MODEL_FILE_WITH_PATH {fp32_model_path}")

        model_name = "gptj"
        model_path = fp8_model_path

    elif "llama2" in env["MLC_MODEL"]:
        preprocessed_data_for_accuracy_checker = os.path.join(
            env['MLPERF_SCRATCH_PATH'],
            'preprocessed_data',
            'open_orca',
            'open_orca_gpt4_tokenized_llama.sampled_24576.pkl')

        if not env.get('LLAMA2_PRE_QUANTIZED_CHECKPOINT_PATH'):
            target_calibration_data_file_path = os.path.join(
                env['MLPERF_SCRATCH_PATH'],
                'data',
                'llama2-70b',
                'open_orca_gpt4_tokenized_llama.calibration_1000.pkl')

        tmp_tp_size = env['MLC_NVIDIA_TP_SIZE']
        tmp_pp_size = env['MLC_NVIDIA_PP_SIZE']

        fp8_model_path = os.path.join(
            env['MLPERF_SCRATCH_PATH'],
            'models',
            'Llama2',
            'fp8-quantized-ammo',
            f'llama-2-70b-chat-hf-tp{tmp_tp_size}pp{tmp_pp_size}-fp8')

        if not os.path.exists(preprocessed_data_for_accuracy_checker):
            if not os.path.exists(preprocessed_data_for_accuracy_checker):
                cmds.append(
                    f"mkdir -p {os.path.dirname(preprocessed_data_for_accuracy_checker)}")
            cmds.append(
                f"cp {env['MLC_DATASET_OPENORCA_PREPROCESSED_PATH']} {preprocessed_data_for_accuracy_checker}")

        model_name = "llama2-70b"
        model_path = fp8_model_path

    # cmds.append(f"make prebuild")
    if make_command == "download_model":
        if not os.path.exists(model_path):
            if "llama2" in env['MLC_MODEL']:
                if not os.path.exists(os.path.join(model_path, 'config.json')):
                    return {
                        'return': 1, 'error': f'Quantised model absent - did not detect config.json in path {model_path}'}
            elif "gptj" in env['MLC_MODEL'] and os.path.exists(fp32_model_path):
                # checkpoint-final already present; FP8 quantization will
                # happen during engine build
                pass
            else:
                cmds.append(f"make download_model BENCHMARKS='{model_name}'")
        elif "stable-diffusion" in env['MLC_MODEL']:
            if is_true(env.get('MLC_MLPERF_INFERENCE_POST_5_0')):
                # Define folder mappings for each model type
                model_folders = {
                    'onnx_models': ["clip1", "clip2", "unetxl", "vae"],
                    'modelopt_models': ["unetxl.fp8", "vae.int8"]
                }

                model_found = True

                # Check all required models across both directories
                for model_type, folders in model_folders.items():
                    for folder in folders:
                        onnx_model_path = os.path.join(
                            env['MLPERF_SCRATCH_PATH'],
                            'models',
                            'SDXL',
                            model_type,
                            folder,
                            'model.onnx'
                        )
                        if not os.path.exists(onnx_model_path):
                            model_found = False
                            break
                    if not model_found:
                        break
                if not model_found:
                    env['MLC_REQUIRE_SDXL_MODEL_DOWNLOAD'] = 'yes'
                    cmds.append(
                        f"make download_model BENCHMARKS='{model_name}'")
            else:
                folders = ["clip1", "clip2", "unetxl", "vae"]
                for folder in folders:
                    onnx_model_path = os.path.join(
                        env['MLPERF_SCRATCH_PATH'],
                        'models',
                        'SDXL',
                        'onnx_models',
                        folder,
                        'model.onnx')
                    if not os.path.exists(onnx_model_path):
                        env['MLC_REQUIRE_SDXL_MODEL_DOWNLOAD'] = 'yes'
                        cmds.append(
                            f"make download_model BENCHMARKS='{model_name}'")
                        break

            if scenario.lower() == "singlestream":
                ammo_model_path = os.path.join(
                    env['MLPERF_SCRATCH_PATH'],
                    'models',
                    'SDXL',
                    'ammo_models',
                    'unetxl.int8',
                    'unet.onnx')
                if not os.path.exists(ammo_model_path):
                    env['MLC_REQUIRE_SDXL_MODEL_DOWNLOAD'] = 'yes'
                    cmds.append(
                        f"make download_model BENCHMARKS='{model_name}'")
        else:
            return {'return': 0}

    elif make_command == "preprocess_data":
        if env['MLC_MODEL'] == "rnnt":
            cmds.append(
                f"rm -rf {os.path.join(env['MLPERF_SCRATCH_PATH'], 'preprocessed_data', 'rnnt_dev_clean_500_raw')}")
            cmds.append(
                f"rm -rf {os.path.join(env['MLPERF_SCRATCH_PATH'], 'preprocessed_data', 'rnnt_train_clean_512_wav')}")
        if "llama2" in env["MLC_MODEL"]:
            # Preprocessing script in the inference results repo is not checking whether the preprocessed
            # file is already there, so we are handling it here.
            target_preprocessed_data_path = os.path.join(
                env['MLPERF_SCRATCH_PATH'],
                'preprocessed_data',
                'open_orca',
                'input_ids_padded.npy')
            if not os.path.exists(target_preprocessed_data_path):
                cmds.append(
                    f"mkdir -p {os.path.dirname(target_preprocessed_data_path)}")
                if env.get('MLC_DATASET_OPENORCA_PREPROCESSED_PATH'):
                    cmds.append(
                        f"cp -r {env['MLC_DATASET_OPENORCA_NVIDIA_PREPROCESSED_PATH']}/* {os.path.join(env['MLPERF_SCRATCH_PATH'], 'preprocessed_data', 'open_orca')}"
                    )
                else:
                    cmds.append(
                        f"make preprocess_data BENCHMARKS='{model_name}'")
        else:
            cmds.append(f"make preprocess_data BENCHMARKS='{model_name}'")

    else:
        scenario = scenario.lower()

        if env['MLC_MLPERF_LOADGEN_MODE'] == "accuracy":
            test_mode = "AccuracyOnly"
        elif env['MLC_MLPERF_LOADGEN_MODE'] == "performance":
            test_mode = "PerformanceOnly"
        elif env['MLC_MLPERF_LOADGEN_MODE'] == "compliance":
            test_mode = ""
            test_name = env.get(
                'MLC_MLPERF_LOADGEN_COMPLIANCE_TEST',
                'test01').lower()
            env['MLC_MLPERF_NVIDIA_RUN_COMMAND'] = "run_audit_{}_once".format(
                test_name)
            make_command = "run_audit_{}_once".format(test_name)
        else:
            return {'return': 1, 'error': 'Unsupported mode: {}'.format(
                env['MLC_MLPERF_LOADGEN_MODE'])}

        run_config = ''

        target_qps = env.get('MLC_MLPERF_LOADGEN_TARGET_QPS')
        offline_target_qps = env.get('MLC_MLPERF_LOADGEN_OFFLINE_TARGET_QPS')
        server_target_qps = env.get('MLC_MLPERF_LOADGEN_SERVER_TARGET_QPS')
        if target_qps:
            target_qps = int(float(target_qps))
            if scenario == "offline" and not offline_target_qps:
                run_config += f" --offline_expected_qps={target_qps}"
            elif scenario == "server" and not server_target_qps:
                run_config += f" --server_target_qps={target_qps}"

        if offline_target_qps:
            offline_target_qps = int(float(offline_target_qps))
            run_config += f" --offline_expected_qps={offline_target_qps}"
        if server_target_qps:
            server_target_qps = int(float(server_target_qps))
            run_config += f" --server_target_qps={server_target_qps}"

        target_latency = env.get('MLC_MLPERF_LOADGEN_TARGET_LATENCY')
        singlestream_target_latency = env.get(
            'MLC_MLPERF_LOADGEN_SINGLESTREAM_TARGET_LATENCY')
        multistream_target_latency = env.get(
            'MLC_MLPERF_LOADGEN_MULTISTREAM_TARGET_LATENCY')
        if target_latency:
            target_latency_ns = int(float(target_latency) * 1000000)
            if scenario == "singlestream" and not singlestream_target_latency:
                run_config += f" --single_stream_expected_latency_ns={target_latency_ns}"
            elif scenario == "multistream" and not multistream_target_latency:
                run_config += f" --multi_stream_expected_latency_ns={target_latency_ns}"

        if singlestream_target_latency:
            singlestream_target_latency_ns = int(
                float(singlestream_target_latency) * 1000000)
            run_config += f" --single_stream_expected_latency_ns={singlestream_target_latency_ns}"
        if multistream_target_latency:
            multistream_target_latency_ns = int(
                float(multistream_target_latency) * 1000000)
            run_config += f" --multi_stream_expected_latency_ns={multistream_target_latency_ns}"

        high_accuracy = "99.9" in env['MLC_MODEL']

        config_ver_list = []

        use_lon = env.get('MLC_MLPERF_NVIDIA_HARNESS_LON')
        if use_lon:
            config_ver_list.append("lon_node")
            # run_config += " --lon_node"

        maxq = env.get('MLC_MLPERF_NVIDIA_HARNESS_MAXQ')
        if maxq:
            config_ver_list.append("maxq")

        if high_accuracy:
            config_ver_list.append("high_accuracy")

        use_triton = env.get('MLC_MLPERF_NVIDIA_HARNESS_USE_TRITON')
        if use_triton:
            run_config += " --use_triton "
            config_ver_list.append("triton")

        if config_ver_list:
            run_config += f" --config_ver={'_'.join(config_ver_list)}"

        user_conf_path = env.get('MLC_MLPERF_USER_CONF')
        if user_conf_path and env['MLC_MLPERF_NVIDIA_HARNESS_RUN_MODE'] == "run_harness":
            run_config += f" --user_conf_path={user_conf_path}"

        mlperf_conf_path = env.get('MLC_MLPERF_INFERENCE_CONF_PATH')
        if mlperf_conf_path and env['MLC_MLPERF_NVIDIA_HARNESS_RUN_MODE'] == "run_harness":
            run_config += f" --mlperf_conf_path={mlperf_conf_path}"

        power_setting = env.get('MLC_MLPERF_NVIDIA_HARNESS_POWER_SETTING')
        if power_setting and env['MLC_MLPERF_NVIDIA_HARNESS_RUN_MODE'] == "run_harness":
            run_config += f" --power_setting={power_setting}"

        gpu_copy_streams = env.get(
            'MLC_MLPERF_NVIDIA_HARNESS_GPU_COPY_STREAMS')
        if gpu_copy_streams:
            run_config += f" --gpu_copy_streams={gpu_copy_streams}"

        gpu_inference_streams = env.get(
            'MLC_MLPERF_NVIDIA_HARNESS_GPU_INFERENCE_STREAMS')
        if gpu_inference_streams:
            run_config += f" --gpu_inference_streams={gpu_inference_streams}"

        _raw_model_precision = env.get('MLC_MLPERF_MODEL_PRECISION')
        model_precision = _raw_model_precision.replace(
            'float', 'fp') if _raw_model_precision else ''
        # by default we use the precision from the custom config
        if model_precision and "fp32" not in model_precision:
            run_config += f" --precision={model_precision}"

        dla_copy_streams = env.get(
            'MLC_MLPERF_NVIDIA_HARNESS_DLA_COPY_STREAMS')
        if dla_copy_streams:
            run_config += f" --dla_copy_streams={dla_copy_streams}"

        dla_inference_streams = env.get(
            'MLC_MLPERF_NVIDIA_HARNESS_DLA_INFERENCE_STREAMS')
        if dla_inference_streams:
            run_config += f" --dla_inference_streams={dla_inference_streams}"

        gpu_batch_size = env.get('MLC_MLPERF_NVIDIA_HARNESS_GPU_BATCH_SIZE')
        if gpu_batch_size:
            # v6.0+ requires component:batch_size format
            inference_version = env.get(
                'MLC_MLPERF_INFERENCE_CODE_VERSION', '')
            if inference_version >= 'v6.0' and ':' not in str(gpu_batch_size):
                gpu_batch_size = f"{model_name}:{gpu_batch_size}"
            run_config += f" --gpu_batch_size={gpu_batch_size}".replace(
                "##", ",")

        dla_batch_size = env.get('MLC_MLPERF_NVIDIA_HARNESS_DLA_BATCH_SIZE')
        if dla_batch_size:
            run_config += f" --dla_batch_size={dla_batch_size}".replace(
                "##", ",")

        input_format = env.get('MLC_MLPERF_NVIDIA_HARNESS_INPUT_FORMAT')
        if input_format:
            run_config += f" --input_format={input_format}"

        performance_sample_count = env.get(
            'MLC_MLPERF_LOADGEN_PERFORMANCE_SAMPLE_COUNT')
        if performance_sample_count:
            run_config += f" --performance_sample_count={performance_sample_count}"

        devices = env.get('MLC_MLPERF_NVIDIA_HARNESS_DEVICES')
        if devices:
            run_config += f" --devices={devices}"

        audio_batch_size = env.get(
            'MLC_MLPERF_NVIDIA_HARNESS_AUDIO_BATCH_SIZE')
        if audio_batch_size:
            run_config += f" --audio_batch_size={audio_batch_size}"

        disable_encoder_plugin = str(
            env.get('MLC_MLPERF_NVIDIA_HARNESS_DISABLE_ENCODER_PLUGIN', ''))
        if disable_encoder_plugin and disable_encoder_plugin.lower() not in [
                "no", "false", "0", ""]:
            run_config += " --disable_encoder_plugin"

        disable_beta1_smallk = str(
            env.get('MLC_MLPERF_NVIDIA_HARNESS_DISABLE_BETA1_SMALLK', ''))
        if disable_beta1_smallk and disable_beta1_smallk.lower() in [
                "yes", "true", "1"]:
            run_config += " --disable_beta1_smallk"

        workspace_size = env.get('MLC_MLPERF_NVIDIA_HARNESS_WORKSPACE_SIZE')
        if workspace_size:
            run_config += f" --workspace_size={workspace_size}"

        if env.get('MLC_MLPERF_LOADGEN_LOGS_DIR'):
            env['MLPERF_LOADGEN_LOGS_DIR'] = env['MLC_MLPERF_LOADGEN_LOGS_DIR']

        log_dir = env.get('MLC_MLPERF_NVIDIA_HARNESS_LOG_DIR', '')
        if not log_dir and env.get('MLC_MLPERF_LOADGEN_LOGS_DIR'):
            log_dir = env['MLC_MLPERF_LOADGEN_LOGS_DIR']
        if log_dir:
            run_config += f" --log_dir={log_dir}"

        use_graphs = str(env.get('MLC_MLPERF_NVIDIA_HARNESS_USE_GRAPHS', ''))
        if use_graphs and use_graphs.lower() not in ["no", "false", "0", ""]:
            run_config += " --use_graphs"

        use_deque_limit = str(
            env.get('MLC_MLPERF_NVIDIA_HARNESS_USE_DEQUE_LIMIT'))
        if use_deque_limit and use_deque_limit.lower() not in [
                "no", "false", "0"]:
            run_config += " --use_deque_limit"

            deque_timeout_usec = env.get(
                'MLC_MLPERF_NVIDIA_HARNESS_DEQUE_TIMEOUT_USEC')
            if deque_timeout_usec:
                run_config += f" --deque_timeout_usec={deque_timeout_usec}"

        use_cuda_thread_per_device = str(
            env.get('MLC_MLPERF_NVIDIA_HARNESS_USE_CUDA_THREAD_PER_DEVICE', ''))
        if use_cuda_thread_per_device and use_cuda_thread_per_device.lower() not in [
                "no", "false", "0", ""]:
            run_config += " --use_cuda_thread_per_device"

        run_infer_on_copy_streams = str(
            env.get('MLC_MLPERF_NVIDIA_HARNESS_RUN_INFER_ON_COPY_STREAMS', ''))
        if run_infer_on_copy_streams and not is_false(
                run_infer_on_copy_streams):
            run_config += " --run_infer_on_copy_streams"

        start_from_device = str(
            env.get(
                'MLC_MLPERF_NVIDIA_HARNESS_START_FROM_DEVICE',
                ''))
        if start_from_device and start_from_device.lower() not in [
                "no", "false", "0", ""]:
            run_config += " --start_from_device"

        end_on_device = str(
            env.get(
                'MLC_MLPERF_NVIDIA_HARNESS_END_ON_DEVICE',
                ''))
        if end_on_device and end_on_device.lower() not in [
                "no", "false", "0", ""]:
            run_config += " --end_on_device"

        max_dlas = env.get('MLC_MLPERF_NVIDIA_HARNESS_MAX_DLAS')
        if max_dlas:
            run_config += f" --max_dlas={max_dlas}"

        graphs_max_seqlen = env.get(
            'MLC_MLPERF_NVIDIA_HARNESS_GRAPHS_MAX_SEQLEN')
        if graphs_max_seqlen:
            run_config += f" --graphs_max_seqlen={graphs_max_seqlen}"

        num_issue_query_threads = env.get(
            'MLC_MLPERF_NVIDIA_HARNESS_NUM_ISSUE_QUERY_THREADS')
        if num_issue_query_threads:
            run_config += f" --num_issue_query_threads={num_issue_query_threads}"

        soft_drop = env.get('MLC_MLPERF_NVIDIA_HARNESS_SOFT_DROP')
        if soft_drop:
            run_config += f" --soft_drop={soft_drop}"

        use_small_tile_gemm_plugin = str(
            env.get('MLC_MLPERF_NVIDIA_HARNESS_USE_SMALL_TILE_GEMM_PLUGIN', ''))
        if use_small_tile_gemm_plugin and use_small_tile_gemm_plugin.lower() not in [
                "no", "false", "0", ""]:
            run_config += f" --use_small_tile_gemm_plugin"

        audio_buffer_num_lines = env.get(
            'MLC_MLPERF_NVIDIA_HARNESS_AUDIO_BUFFER_NUM_LINES')
        if audio_buffer_num_lines:
            run_config += f" --audio_buffer_num_lines={audio_buffer_num_lines}"

        use_fp8 = str(env.get('MLC_MLPERF_NVIDIA_HARNESS_USE_FP8', ''))
        if use_fp8 and not is_false(use_fp8):
            run_config += f" --use_fp8"

        if "llama2" in env["MLC_MODEL"]:
            run_config += f" --checkpoint_dir={fp8_model_path}"
            run_config += f" --tensor_path={os.path.join(env['MLPERF_SCRATCH_PATH'], 'preprocessed_data', 'open_orca')}"
            if is_true(env.get('MLC_MLPERF_INFERENCE_POST_5_0')):
                run_config += f" --trtllm_build_flags=tensor_parallelism:{tmp_tp_size},pipeline_parallelism:{tmp_pp_size}"
            else:
                run_config += f" --tensor_parallelism={tmp_tp_size}"
                run_config += f" --pipeline_parallelism={tmp_pp_size}"

        enable_sort = env.get('MLC_MLPERF_NVIDIA_HARNESS_ENABLE_SORT')
        is_post5_gptj = is_true(
            env.get('MLC_MLPERF_INFERENCE_POST_5_0')) and "gptj" in env.get(
            'MLC_MODEL', '')
        if enable_sort and not is_false(enable_sort) and not is_post5_gptj:
            run_config += f" --enable_sort"

        sdxl_server_batcher_time_limit = env.get(
            'MLC_MLPERF_NVIDIA_HARNESS_ENABLE_SORT')
        if sdxl_server_batcher_time_limit and not is_post5_gptj:
            run_config += f" --sdxl_batcher_time_limit {sdxl_server_batcher_time_limit}"

        num_sort_segments = env.get(
            'MLC_MLPERF_NVIDIA_HARNESS_NUM_SORT_SEGMENTS')
        if num_sort_segments and not is_post5_gptj:
            run_config += f" --num_sort_segments={num_sort_segments}"

        embedding_weights_on_gpu_part = env.get(
            'MLC_MLPERF_NVIDIA_HARNESS_EMBEDDING_WEIGHTS_ON_GPU_PART', '')
        if embedding_weights_on_gpu_part != '':
            run_config += f" --embedding_weights_on_gpu_part={embedding_weights_on_gpu_part}"

        num_warmups = env.get('MLC_MLPERF_NVIDIA_HARNESS_NUM_WARMUPS', '')
        if num_warmups != '':
            run_config += f" --num_warmups={num_warmups}"

        skip_postprocess = str(
            env.get(
                'MLC_MLPERF_NVIDIA_HARNESS_SKIP_POSTPROCESS',
                ''))
        if skip_postprocess and not is_false(
                skip_postprocess) and not is_post5_gptj:
            run_config += f" --skip_postprocess"

        if test_mode:
            test_mode_string = " --test_mode={}".format(test_mode)
        else:
            test_mode_string = ""

        extra_build_engine_options_string = env.get(
            'MLC_MLPERF_NVIDIA_HARNESS_EXTRA_BUILD_ENGINE_OPTIONS', '')

        extra_run_options_string = env.get(
            'MLC_MLPERF_NVIDIA_HARNESS_EXTRA_RUN_OPTIONS',
            '')  # will be ignored during build engine

        if "stable-diffusion" in env["MLC_MODEL"]:
            extra_build_engine_options_string += f""" --model_path {
                os.path.join(
                    env['MLPERF_SCRATCH_PATH'],
                    'models',
                    'SDXL/')}"""

        run_config += " --no_audit_verify"

        cmds.append(f"""make {make_command} RUN_ARGS=' --benchmarks={model_name} --scenarios={scenario} {test_mode_string} {run_config} {extra_build_engine_options_string} {extra_run_options_string}'""")

    # Build TensorRT plugins for models that need them (retinanet, dlrm-v2).
    # Plugins must be built inside the runtime code directory, not just during Docker image build,
    # because the NVIDIA code repo may be freshly cloned at container startup.
    _plugin_models = {'retinanet', 'dlrm-v2', 'dlrm-v2-99', 'dlrm-v2-99.9'}
    if env.get('MLC_MODEL', '') in _plugin_models and nvidia_code_path:
        _plugin_dir = os.path.join(nvidia_code_path, 'code', 'plugin')
        if os.path.isdir(_plugin_dir):
            _plugin_cmds = []
            # Patch NMSOptPlugin for CUDA 13+ (cub::Sum removed in CCCL 3.0)
            _nms_gather = os.path.join(
                _plugin_dir,
                'NMSOptPlugin',
                'src',
                'gatherTopDetectionsOpt.cu')
            _plugin_cmds.append(
                f"sed -i 's/cub::Sum()/::cuda::std::plus<>{{}}/' {_nms_gather} 2>/dev/null || true"
            )
            _plugin_cmds.append(
                f"grep -q 'cuda/std/functional' {_nms_gather} || sed -i '1i #include <cuda/std/functional>' {_nms_gather} 2>/dev/null || true"
            )
            for _entry in sorted(os.listdir(_plugin_dir)):
                _cmake_file = os.path.join(
                    _plugin_dir, _entry, 'CMakeLists.txt')
                if os.path.isfile(_cmake_file):
                    _pbuild = os.path.join(
                        nvidia_code_path, 'build', 'plugins', _entry)
                    _plugin_cmds.append(
                        f'mkdir -p {_pbuild} && cd {_pbuild} && CPLUS_INCLUDE_PATH=/usr/local/cuda/include cmake -DCMAKE_BUILD_TYPE=Release {os.path.join(_plugin_dir, _entry)} && CPLUS_INCLUDE_PATH=/usr/local/cuda/include make -j'
                    )
            # Fix retinanet ONNX model path: builder.py hardcodes 'torch2.1' but the
            # actual PyTorch version may differ (e.g., 2.10 in newer containers).
            # Patch builder.py to use the installed torch version.
            if env.get('MLC_MODEL', '') == 'retinanet':
                _retinanet_builder = os.path.join(
                    nvidia_code_path, 'code', 'retinanet', 'tensorrt', 'builder.py')
                _plugin_cmds.append(
                    f'TORCH_VER=$(python3 -c "import torch; print(\\".\\".join(torch.__version__.split(\\".\\")[:2]))") && '
                    f'sed -i "s/torch2.1-postprocessed/torch${{TORCH_VER}}-postprocessed/g" {_retinanet_builder} 2>/dev/null || true'
                )

            if _plugin_cmds:
                # cd back to nvidia_code_path after plugin builds so subsequent
                # cmds run from correct dir
                cmds = _plugin_cmds + [f'cd {nvidia_code_path}'] + cmds

    run_cmd = " && ".join(cmds)
    env['MLC_MLPERF_RUN_CMD'] = run_cmd
    env['MLC_RUN_CMD'] = run_cmd
    env['MLC_RUN_DIR'] = env['MLC_MLPERF_INFERENCE_NVIDIA_CODE_PATH']

    if '+LD_LIBRARY_PATH' not in env:
        env['+LD_LIBRARY_PATH'] = []

    hpcx_paths = []
    if os.path.exists("/opt/hpcx/ucx/lib"):
        hpcx_paths.append("/opt/hpcx/ucx/lib")
    if os.path.exists("/opt/hpcx/ucc/lib"):
        hpcx_paths.append("/opt/hpcx/ucc/lib")
    if os.path.exists("/opt/hpcx/ompi/lib"):
        hpcx_paths.append("/opt/hpcx/ompi/lib")

    env['+LD_LIBRARY_PATH'] = hpcx_paths + env['+LD_LIBRARY_PATH']
    env['+PYTHONPATH'] = []
    #    print(env)

    return {'return': 0}


def postprocess(i):

    env = i['env']
    state = i['state']

    return {'return': 0}
