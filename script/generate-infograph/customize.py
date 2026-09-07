from utils import is_true
import os
import glob


# The lstopo capture written by get-mlperf-single-node-system-info,_lstopo
# shares its stem with that node's sysinfo JSON:
#   mlperf-system-info-single-node-2.json
#   mlperf-system-info-single-node-2.lstopo.xml
# Pairing on the stem is what lets this script work for a directory produced by
# any caller, single node or multi node, without being told a node list.
_TOPOLOGY_SUFFIX = '.lstopo.xml'

# infragraph >= 3.0 uses PEP 604 annotations (`str | None`) at class-definition
# time, so on an older interpreter it does not fail to install -- it fails to
# import, with a TypeError that says nothing about Python versions.
_MIN_PYTHON = (3, 10)


def _python_version(env):
    """(major, minor) of the interpreter MLC selected, or None if unreadable."""
    raw = env.get('MLC_PYTHON_VERSION', '')
    parts = str(raw).split('.')
    if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
        return (int(parts[0]), int(parts[1]))
    return None


def _discover_nodes(input_dir):
    """Every (stem, xml, sysinfo_or_None) triple found in input_dir.

    Sorted so that node-2 lands after node-10 in numeric rather than
    lexicographic order -- the ordering shows up in the merged graph's
    instance list, and a jumbled one is confusing to read against the
    submission's node numbering.
    """
    nodes = []
    for xml in glob.glob(os.path.join(input_dir, '*' + _TOPOLOGY_SUFFIX)):
        stem = os.path.basename(xml)[:-len(_TOPOLOGY_SUFFIX)]
        sysinfo = os.path.join(input_dir, stem + '.json')
        nodes.append((stem, xml, sysinfo if os.path.isfile(sysinfo) else None))
    return sorted(nodes, key=lambda n: _sort_key(n[0]))


def _sort_key(stem):
    """Natural sort: trailing digits compare numerically, rest lexically."""
    head = stem.rstrip('0123456789')
    tail = stem[len(head):]
    return (head, int(tail) if tail else -1)


def preprocess(i):

    env = i['env']
    logger = i['automation'].logger

    # version_min on the python dep is ignored when MLC_PYTHON_BIN_WITH_PATH
    # is already set by an enclosing script -- get-python3 keeps the inherited
    # interpreter rather than searching for one. Check here so the failure
    # names the real problem instead of surfacing as an import TypeError.
    version = _python_version(env)
    if version and version < _MIN_PYTHON:
        want = '.'.join(str(v) for v in _MIN_PYTHON)
        return {'return': 1,
                'error': f'infragraph needs Python >= {want}, but MLC selected '
                         f'{env.get("MLC_PYTHON_BIN_WITH_PATH", "?")} '
                         f'(version {env.get("MLC_PYTHON_VERSION", "?")}). '
                         'Point MLC at a newer interpreter, e.g. '
                         '`mlc rm cache --tags=get,python3` then re-run, or '
                         'pass --adr.python.version_min=' + want + ' to the '
                         'top-level script.'}

    input_dir = env.get('MLC_INFRAGRAPH_INPUT_DIR_PATH', '') or os.getcwd()
    input_dir = os.path.abspath(input_dir)
    if not os.path.isdir(input_dir):
        return {'return': 1,
                'error': f'Input directory does not exist: {input_dir}'}
    env['MLC_INFRAGRAPH_INPUT_DIR_PATH'] = input_dir

    out_dir = env.get('MLC_INFRAGRAPH_OUT_DIR_PATH', '') or input_dir
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    env['MLC_INFRAGRAPH_OUT_DIR_PATH'] = out_dir

    file_name = env.get('MLC_INFRAGRAPH_FILE_NAME', '') or 'infragraph.json'
    env['MLC_INFRAGRAPH_FILE_PATH'] = os.path.join(out_dir, file_name)
    env['MLC_INFRAGRAPH_YAML_FILE_PATH'] = os.path.join(
        out_dir, os.path.splitext(file_name)[0] + '.yaml')
    env['MLC_INFRAGRAPH_VISUALS_DIR_PATH'] = os.path.join(out_dir, 'visuals')

    nodes = _discover_nodes(input_dir)
    if not nodes:
        return {'return': 1,
                'error': f'No *{_TOPOLOGY_SUFFIX} topology files found in '
                         f'{input_dir}. Run the system-info collection with '
                         'the _infragraph variation (or get,mlperf,single-'
                         'node,system-info with _lstopo) so each node writes '
                         'its hwloc topology next to its sysinfo JSON.'}

    for stem, _xml, sysinfo in nodes:
        if sysinfo is None:
            logger.warning(
                f'{stem}: topology found but no matching {stem}.json sysinfo; '
                'this node will appear in the graph without processor or '
                'accelerator attributes.')
    logger.info(
        f'Building infrastructure graph from {len(nodes)} node topology '
        f'file(s) in {input_dir}')

    env['MLC_INFRAGRAPH_NODE_COUNT'] = str(len(nodes))

    # An empty MLC_MLPERF_SYSTEM_NAME templates through to an empty string
    # rather than being absent, so test for content, not for the key.
    if not env.get('MLC_INFRAGRAPH_NAME', '').strip():
        env['MLC_INFRAGRAPH_NAME'] = (
            'single-node-system' if len(nodes) == 1 else 'multi-node-system')

    return {'return': 0}


def postprocess(i):

    env = i['env']
    logger = i['automation'].logger

    out_path = env.get('MLC_INFRAGRAPH_FILE_PATH', '')
    if not out_path or not os.path.isfile(out_path):
        return {'return': 1,
                'error': f'Expected the infrastructure graph at {out_path}, '
                         'but it was not produced.'}

    # Visuals are optional, so only advertise the directory when it is there.
    if not os.path.isdir(env.get('MLC_INFRAGRAPH_VISUALS_DIR_PATH', '')):
        del env['MLC_INFRAGRAPH_VISUALS_DIR_PATH']

    logger.info(f'Infrastructure graph written to {out_path}')

    return {'return': 0}
