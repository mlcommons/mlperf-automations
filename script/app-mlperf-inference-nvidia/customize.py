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

    if is_true(env.get('MLC_RUN_STATE_DOCKER', '')):
        return {'return': 0}

    # Patch submission_checker/__init__.py if empty to expose ACC_PATTERN / MODEL_CONFIG
    # The NVIDIA harness does `import submission_checker; submission_checker.ACC_PATTERN`
    # but upstream __init__.py is empty; constants live in submission_checker/constants.py
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
        # so that _verify_path() sees the symlink/dir and doesn't try to create empty directories.
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
                _nvm_cfg_file = os.path.join(_sp, 'nvmitten', 'configurator.py')
                # Check if proper configurator package is missing or is the old no-op version
                _nvm_core = os.path.join(_nvm_cfg_dir, '_core.py')
                _needs_install = (not os.path.isdir(_nvm_cfg_dir) and not os.path.isfile(_nvm_cfg_file))
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
                _nvm_sys_init = os.path.join(_sp, 'nvmitten', 'system', '__init__.py')
                if os.path.isfile(_nvm_sys_init):
                    with open(_nvm_sys_init, 'r') as _f:
                        _sys_content = _f.read()
                    if 'from nvmitten.system.system import System' not in _sys_content:
                        with open(_nvm_sys_init, 'a') as _f:
                            _f.write('\nfrom nvmitten.system.system import System\n')

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
                _nvm_builder = os.path.join(_sp, 'nvmitten', 'nvidia', 'builder.py')
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
                            _builder_src = _builder_src.replace(_builder_old_double, _builder_new, 1)
                        elif _builder_old_single in _builder_src:
                            _builder_src = _builder_src.replace(_builder_old_single, _builder_new, 1)
                        if '_mlc_valstr_or_self' in _builder_src:
                            with open(_nvm_builder, 'w') as _f:
                                _f.write(_builder_src)

                # Fix nvmitten/pipeline/pipeline.py: preserve KeyboardInterrupt instance.
                # Upstream code sets `exc = KeyboardInterrupt` (the class), then traceback
                # extraction crashes on Python 3.12 with: "'getset_descriptor' object has
                # no attribute 'tb_frame'" and masks the real underlying failure.
                _nvm_pipeline = os.path.join(_sp, 'nvmitten', 'pipeline', 'pipeline.py')
                if os.path.isfile(_nvm_pipeline):
                    with open(_nvm_pipeline, 'r') as _f:
                        _pipeline_src = _f.read()
                    _needle = 'except KeyboardInterrupt as _exc:\n                exc = KeyboardInterrupt\n                status = OperationStatus.INTERRUPTED'
                    _fixed = 'except KeyboardInterrupt as _exc:\n                exc = _exc\n                status = OperationStatus.INTERRUPTED'
                    if _needle in _pipeline_src:
                        _pipeline_src = _pipeline_src.replace(_needle, _fixed, 1)
                        with open(_nvm_pipeline, 'w') as _f:
                            _f.write(_pipeline_src)
                continue

        # Fix code/harness/lwis/CMakeLists.txt: missing ${CUDA_INCLUDE_DIRS} causes
        # "fatal error: cuda.h: No such file or directory" when building the v6.0 harness.
        _lwis_cmake = os.path.join(nvidia_code_path, 'code', 'harness', 'lwis', 'CMakeLists.txt')
        if os.path.isfile(_lwis_cmake):
            with open(_lwis_cmake, 'r') as _f:
                _lwis_src = _f.read()
            if '${CUDA_INCLUDE_DIRS}' not in _lwis_src and 'target_include_directories(lwis' in _lwis_src:
                _lwis_src = _lwis_src.replace(
                    'target_include_directories(lwis\n    PUBLIC\n        ${LOADGEN_INCLUDE_DIR}',
                    'target_include_directories(lwis\n    PUBLIC\n        ${CUDA_INCLUDE_DIRS}\n        ${LOADGEN_INCLUDE_DIR}')
                with open(_lwis_cmake, 'w') as _f:
                    _f.write(_lwis_src)

        # Fix code/plugin/__init__.py: base_plugin_map lacks entries for benchmarks without plugins
        # (e.g. ResNet50), causing KeyError crash. Use .get() with [] default instead.
        _plugin_init = os.path.join(nvidia_code_path, 'code', 'plugin', '__init__.py')
        if os.path.isfile(_plugin_init):
            with open(_plugin_init, 'r') as _f:
                _plugin_src = _f.read()
            if 'base_plugin_map[benchmark]' in _plugin_src:
                _plugin_src = _plugin_src.replace(
                    'for plugin in base_plugin_map[benchmark]:',
                    'for plugin in base_plugin_map.get(benchmark, []):')
                with open(_plugin_init, 'w') as _f:
                    _f.write(_plugin_src)

        # Fix code/common/paths.py: SUBMODULES_DIR calls _verify_path() at module import time,
        # raising FileNotFoundError if 3rdparty is absent. Patch to use create_if_missing=True
        # for SUBMODULES_DIR only; mlc-inference and trtllm are created as symlinks/dirs above.
        _paths_py = os.path.join(nvidia_code_path, 'code', 'common', 'paths.py')
        if os.path.isfile(_paths_py):
            with open(_paths_py, 'r') as _f:
                _paths_src = _f.read()
            _paths_old = (
                'SUBMODULES_DIR: Final[Path] = _verify_path(PROJECT_BASE_DIR / "3rdparty")\n'
                'TRTLLM_DIR: Final[Path] = _verify_path(SUBMODULES_DIR / "trtllm")\n'
                'MLCOMMONS_INF_REPO: Final[Path] = _verify_path(SUBMODULES_DIR / "mlc-inference")'
            )
            _paths_new = (
                'SUBMODULES_DIR: Final[Path] = _verify_path(PROJECT_BASE_DIR / "3rdparty", create_if_missing=True)\n'
                'TRTLLM_DIR: Final[Path] = _verify_path(SUBMODULES_DIR / "trtllm", create_if_missing=True)\n'
                'MLCOMMONS_INF_REPO: Final[Path] = _verify_path(SUBMODULES_DIR / "mlc-inference", create_if_missing=True)'
            )
            if _paths_old in _paths_src:
                _paths_src = _paths_src.replace(_paths_old, _paths_new)
                with open(_paths_py, 'w') as _f:
                    _f.write(_paths_src)

        # Fix code/common/mlcommons/loadgen.py: import_from() gets pathlib.Path objects in the
        # import_path list, but Python's import machinery requires strings. Also guard the
        # mlperf.conf export copy against SameFileError when src and dst resolve to the same path.
        _loadgen_py = os.path.join(nvidia_code_path, 'code', 'common', 'mlcommons', 'loadgen.py')
        if os.path.isfile(_loadgen_py):
            with open(_loadgen_py, 'r') as _f:
                _loadgen_src = _f.read()
            _loadgen_changed = False
            _lg_old = ('submission_checker_constants = import_from(\n'
                       '    [paths.MLCOMMONS_INF_REPO / "tools" / "submission" / "submission_checker"] + sys.path,\n'
                       '    "constants"\n'
                       ')')
            _lg_new = ('submission_checker_constants = import_from(\n'
                       '    [str(paths.MLCOMMONS_INF_REPO / "tools" / "submission" / "submission_checker")] + [str(p) for p in sys.path],\n'
                       '    "constants"\n'
                       ')')
            if _lg_old in _loadgen_src:
                _loadgen_src = _loadgen_src.replace(_lg_old, _lg_new)
                _loadgen_changed = True
            if '_mlc_copy_if_different' not in _loadgen_src and 'shutil.copy(' in _loadgen_src:
                if 'import os\n' not in _loadgen_src:
                    _loadgen_src = _loadgen_src.replace('import shutil\n', 'import os\nimport shutil\n', 1)
                _loadgen_src = _loadgen_src.replace(
                    'import shutil\n',
                    'import shutil\n\n'
                    'def _mlc_copy_if_different(src, dst):\n'
                    '    if os.path.realpath(src) != os.path.realpath(dst):\n'
                    '        shutil.copy(src, dst)\n\n',
                    1)
                _loadgen_src = _loadgen_src.replace('shutil.copy(', '_mlc_copy_if_different(', 1)
                _loadgen_changed = True
            if _loadgen_changed:
                with open(_loadgen_py, 'w') as _f:
                    _f.write(_loadgen_src)

        # Fix code/resnet50/tensorrt/builder.py: object.__init__() in the MRO does not accept
        # calib_data_dir, so do not forward it in the super().__init__ call.
        _resnet_builder_py = os.path.join(nvidia_code_path, 'code', 'resnet50', 'tensorrt', 'builder.py')
        if os.path.isfile(_resnet_builder_py):
            with open(_resnet_builder_py, 'r') as _f:
                _resnet_builder_src = _f.read()
            if 'calib_data_dir=calib_data_dir,' in _resnet_builder_src:
                _resnet_builder_src = _resnet_builder_src.replace('calib_data_dir=calib_data_dir,', '', 1)
                with open(_resnet_builder_py, 'w') as _f:
                    _f.write(_resnet_builder_src)

        # Fix code/common/workload.py: Workload.from_fields classmethod is missing in v6.0
        # but main.py calls Workload.from_fields(...) at line 531.
        # Add it as a classmethod that bypasses autoconfigure and constructs directly.
        _workload_py = os.path.join(nvidia_code_path, 'code', 'common', 'workload.py')
        if os.path.isfile(_workload_py):
            with open(_workload_py, 'r') as _f:
                _workload_src = _f.read()
            if 'def from_fields' not in _workload_src and 'def __eq__(self, other):' in _workload_src:
                _from_fields = (
                    '\n'
                    '    @classmethod\n'
                    '    def from_fields(cls, benchmark, scenario, system=None, setting=None, **kwargs):\n'
                    '        from code.common.systems.system_list import DETECTED_SYSTEM as _DS\n'
                    '        import code.common.constants as _C\n'
                    '        if system is None:\n'
                    '            system = _DS\n'
                    '        if setting is None:\n'
                    '            setting = _C.WorkloadSetting()\n'
                    '        return cls(benchmark, scenario, system=system, setting=setting, **kwargs)\n'
                    '\n'
                )
                _workload_src = _workload_src.replace(
                    '    def __eq__(self, other):', _from_fields + '    def __eq__(self, other):', 1)
                with open(_workload_py, 'w') as _f:
                    _f.write(_workload_src)

    if "bert" in env.get('MLC_MODEL', '') and _inference_version >= 'v6.0' and nvidia_code_path:
        # 1. Create code/bert/tensorrt/fields.py with Field definitions needed by bert configs
        _bert_fields_path = os.path.join(
            nvidia_code_path, 'code', 'bert', 'tensorrt', 'fields.py')
        if not os.path.isfile(_bert_fields_path):
            os.makedirs(os.path.dirname(_bert_fields_path), exist_ok=True)
            _bert_fields_content = (
                '# Auto-generated by mlc-automations for v6.0+ custom system support\n'
                'from nvmitten.configurator import Field\n\n'
                'bert_opt_seqlen = Field(\n'
                '    "bert_opt_seqlen",\n'
                '    description="Opt sequence length for BERT TRT optimization profile",\n'
                '    from_string=int)\n\n'
                'graphs_max_seqlen = Field(\n'
                '    "graphs_max_seqlen",\n'
                '    description="Maximum sequence length for CUDA graphs in BERT",\n'
                '    from_string=int)\n\n'
                'use_small_tile_gemm_plugin = Field(\n'
                '    "use_small_tile_gemm_plugin",\n'
                '    description="Enable Small Tile GEMM plugin for BERT",\n'
                '    from_string=bool)\n'
            )
            with open(_bert_fields_path, 'w') as _f:
                _f.write(_bert_fields_content)

        # 2. Create configs/minimal/{scenario}/bert.py for all applicable scenarios
        #    (Offline and SingleStream for edge; Server for datacenter)
        _bert_config_template = '''\
# Auto-generated by mlc-automations for v6.0+ custom system support
import code.common.constants as C
import code.bert.tensorrt.fields as bert_fields
import code.fields.harness as harness_fields
import code.fields.models as model_fields
import code.fields.loadgen as loadgen_fields
import code.fields.gen_engines as gen_engines_fields

_base_99 = {{
    bert_fields.bert_opt_seqlen: 384,
    harness_fields.coalesced_tensor: True,
    model_fields.gpu_batch_size: {{'bert': {gpu_batch_size}}},
    harness_fields.gpu_copy_streams: 2,
    harness_fields.gpu_inference_streams: 2,
    model_fields.input_dtype: 'int32',
    model_fields.input_format: 'linear',
    {qps_field}: {qps_value},
    model_fields.precision: 'int8',
    harness_fields.tensor_path: 'build/preprocessed_data/squad_tokenized/input_ids.npy,build/preprocessed_data/squad_tokenized/segment_ids.npy,build/preprocessed_data/squad_tokenized/input_mask.npy',
    harness_fields.use_graphs: False,
    bert_fields.use_small_tile_gemm_plugin: False,
    gen_engines_fields.workspace_size: 5368709120,
}}

_base_999 = dict(_base_99)
_base_999[model_fields.precision] = 'fp16'

EXPORTS = {{
    C.WorkloadSetting(C.HarnessType.Custom, C.AccuracyTarget(0.99), C.PowerSetting.MaxP): _base_99,
    C.WorkloadSetting(C.HarnessType.Custom, C.AccuracyTarget(0.999), C.PowerSetting.MaxP): _base_999,
}}
'''
        _scenario_qps_map = {
            'Offline': ('loadgen_fields.offline_expected_qps', 1500),
            'SingleStream': ('loadgen_fields.single_stream_expected_latency_ns', 2000000),
            'Server': ('loadgen_fields.server_target_qps', 1000),
        }
        for _scen, (_qps_field, _qps_value) in _scenario_qps_map.items():
            _minimal_scen_dir = os.path.join(nvidia_code_path, 'configs', 'minimal', _scen)
            os.makedirs(_minimal_scen_dir, exist_ok=True)
            _bert_cfg_path = os.path.join(_minimal_scen_dir, 'bert.py')
            if not os.path.isfile(_bert_cfg_path):
                _gpu_batch_size = {'Offline': 256, 'SingleStream': 32, 'Server': 64}[_scen]
                _content = _bert_config_template.format(
                    gpu_batch_size=_gpu_batch_size,
                    qps_field=_qps_field,
                    qps_value=_qps_value,
                )
                with open(_bert_cfg_path, 'w') as _f:
                    _f.write(_content)

    # For resnet50 on NVIDIA harness: create or fix the minimal config.
    # Keep this unconditional on version string formatting (e.g. "6.0" vs "v6.0").
    if env.get('MLC_MODEL', '') == 'resnet50' and nvidia_code_path:
        _resnet_minimal_dir = os.path.join(nvidia_code_path, 'configs', 'minimal', 'Offline')
        os.makedirs(_resnet_minimal_dir, exist_ok=True)
        _resnet_cfg_path = os.path.join(_resnet_minimal_dir, 'resnet50.py')
        if not os.path.isfile(_resnet_cfg_path):
            # Create from scratch in v6.0 dict-based format
            _resnet_cfg = (
                '# Auto-generated by mlc-automations for v6.0+ custom system support\n'
                'import code.common.constants as C\n'
                'import code.fields.harness as harness_fields\n'
                'import code.fields.models as model_fields\n'
                'import code.fields.loadgen as loadgen_fields\n'
                '\n'
                '_base = {\n'
                "    model_fields.gpu_batch_size: {'resnet50': 2048},\n"
                '    loadgen_fields.offline_expected_qps: 30000,\n'
                "    model_fields.precision: 'int8',\n"
                "    model_fields.input_dtype: 'int8',\n"
                "    model_fields.input_format: 'linear',\n"
                "    harness_fields.tensor_path: 'build/preprocessed_data/imagenet/ResNet50/int8_linear',\n"
                "    harness_fields.map_path: 'data_maps/imagenet/val_map.txt',\n"
                '}\n\n'
                'EXPORTS = {\n'
                '    C.WorkloadSetting(C.HarnessType.Custom, C.AccuracyTarget(0.99), C.PowerSetting.MaxP): _base,\n'
                '}\n'
            )
            with open(_resnet_cfg_path, 'w') as _f:
                _f.write(_resnet_cfg)
        else:
            with open(_resnet_cfg_path, 'r') as _f:
                _resnet_cfg = _f.read()
            _changed = False
            if 'from nvmitten.constants import Precision\n' in _resnet_cfg:
                _resnet_cfg = _resnet_cfg.replace('from nvmitten.constants import Precision\n', '')
                _changed = True
            if 'Precision.INT8' in _resnet_cfg:
                _resnet_cfg = _resnet_cfg.replace('Precision.INT8', "'int8'")
                _changed = True
            if 'model_fields.input_dtype' not in _resnet_cfg and "model_fields.precision: 'int8'," in _resnet_cfg:
                _resnet_cfg = _resnet_cfg.replace(
                    "    model_fields.precision: 'int8',",
                    "    model_fields.precision: 'int8',\n"
                    "    model_fields.input_dtype: 'int8',\n"
                    "    model_fields.input_format: 'linear',")
                _changed = True
            # Normalize legacy base tensor path to int8_linear preprocessed data.
            if "imagenet/ResNet50/'," in _resnet_cfg:
                _resnet_cfg = _resnet_cfg.replace(
                    "harness_fields.tensor_path: 'build/preprocessed_data/imagenet/ResNet50/',",
                    "harness_fields.tensor_path: 'build/preprocessed_data/imagenet/ResNet50/int8_linear',")
                _changed = True
            if "model_fields.input_dtype: 'fp32'" in _resnet_cfg:
                _resnet_cfg = _resnet_cfg.replace("model_fields.input_dtype: 'fp32'", "model_fields.input_dtype: 'int8'")
                _changed = True
            if 'ResNet50/fp32' in _resnet_cfg:
                _resnet_cfg = _resnet_cfg.replace('ResNet50/fp32', 'ResNet50/int8_linear')
                _changed = True
            # Add map_path if missing
            if 'map_path' not in _resnet_cfg:
                _resnet_cfg = _resnet_cfg.replace(
                    "harness_fields.tensor_path: 'build/preprocessed_data/imagenet/ResNet50/int8_linear',",
                    "harness_fields.tensor_path: 'build/preprocessed_data/imagenet/ResNet50/int8_linear',\n"
                    "    harness_fields.map_path: 'data_maps/imagenet/val_map.txt',")
                _changed = True
            if _changed:
                with open(_resnet_cfg_path, 'w') as _f:
                    _f.write(_resnet_cfg)

    # Patch generate_engines.py to guard against calib_data_dir being None.
    # The nvmitten autoconfigure mechanism can leave builder.calib_data_dir unset
    # when the field is not bound on the builder class. Use a fallback path so that
    # set_calibrator can still configure the calibration cache reader for INT8 engines.
    if nvidia_code_path:
        _gen_eng_path = os.path.join(nvidia_code_path, 'code', 'ops', 'generate_engines.py')
        if os.path.isfile(_gen_eng_path):
            with open(_gen_eng_path, 'r') as _f:
                _gen_eng = _f.read()
            _changed_ge = False
            # Patch EngineBuilderOp.run() (line ~199)
            _old_pattern = (
                'if isinstance(builder, CalibratableTensorRTEngine):\n'
                '                    builder.set_calibrator(scratch_space.path.joinpath("preprocessed_data",\n'
                '                                                                       builder.calib_data_dir))'
            )
            _new_pattern = (
                'if isinstance(builder, CalibratableTensorRTEngine):\n'
                '                    from pathlib import Path as _Path\n'
                '                    _calib_dir = builder.calib_data_dir or _Path(".")\n'
                '                    builder.set_calibrator(scratch_space.path.joinpath("preprocessed_data",\n'
                '                                                                       _calib_dir))'
            )
            if _old_pattern in _gen_eng and '_calib_dir = builder.calib_data_dir' not in _gen_eng:
                _gen_eng = _gen_eng.replace(_old_pattern, _new_pattern)
                _changed_ge = True
            # Patch CalibrateEngineOp.run() (line ~115)
            _old_calib = (
                'if builder.need_calibration:\n'
                '                builder.set_calibrator(scratch_space.path.joinpath("preprocessed_data",\n'
                '                                                                   builder.calib_data_dir))'
            )
            _new_calib = (
                'if builder.need_calibration:\n'
                '                from pathlib import Path as _Path\n'
                '                _calib_dir = builder.calib_data_dir or _Path(".")\n'
                '                builder.set_calibrator(scratch_space.path.joinpath("preprocessed_data",\n'
                '                                                                   _calib_dir))'
            )
            if _old_calib in _gen_eng and _new_calib not in _gen_eng:
                _gen_eng = _gen_eng.replace(_old_calib, _new_calib)
                _changed_ge = True
            if _changed_ge:
                with open(_gen_eng_path, 'w') as _f:
                    _f.write(_gen_eng)

    # For GPTJ on post-5.0 NVIDIA harness: apply persistent patches that survive container restarts.
    # These are applied idempotently every run so a fresh container gets them automatically.
    if "gptj" in env.get('MLC_MODEL', '') and is_true(env.get('MLC_MLPERF_INFERENCE_POST_5_0')) and nvidia_code_path:
        import json as _json
        import site as _site

        # --- Patch A: modelopt QKV merge OOM-safe fallback ---
        _sp_dirs = _site.getsitepackages() + [_site.getusersitepackages()]
        for _sp in _sp_dirs:
            _mc_path = os.path.join(_sp, 'modelopt', 'torch', 'export', 'model_config.py')
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
        _custom_list_path = os.path.join(nvidia_code_path, 'code', 'common', 'systems', 'custom_list.json')
        if os.path.isfile(_custom_list_path):
            with open(_custom_list_path) as _f:
                _custom_systems = _json.load(_f)
            _gptj_scenarios = ['Offline', 'Server', 'SingleStream', 'MultiStream']
            for _sys_name in _custom_systems:
                for _scen in _gptj_scenarios:
                    _custom_py = os.path.join(nvidia_code_path, 'configs', 'gptj', _scen, 'custom.py')
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
            add_custom_script = os.path.join(nvidia_code_path, 'scripts', 'custom_systems', 'add_custom_system.py')
            if os.path.isfile(add_custom_script):
                cmds.insert(0, f'cd {nvidia_code_path} && python3 scripts/custom_systems/add_custom_system.py')
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
                # checkpoint-final already present; FP8 quantization will happen during engine build
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
        model_precision = _raw_model_precision.replace('float', 'fp') if _raw_model_precision else ''
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
            inference_version = env.get('MLC_MLPERF_INFERENCE_CODE_VERSION', '')
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

        log_dir = env.get('MLC_MLPERF_NVIDIA_HARNESS_LOG_DIR')
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
        is_post5_gptj = is_true(env.get('MLC_MLPERF_INFERENCE_POST_5_0')) and "gptj" in env.get('MLC_MODEL', '')
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
        if skip_postprocess and not is_false(skip_postprocess) and not is_post5_gptj:
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
