from utils import is_true
import mlc
import os
import shutil


def _parse_node(node_str):
    """Parse 'user@host:port' into (user, host, port) with sensible defaults.

    Kept identical in behaviour to the helper of the same name in
    get-mlperf-multi-node-system-info so both scripts agree on how a single
    --ssh_ids entry is interpreted.
    """
    parts = [p.strip() for p in node_str.split(':') if p.strip()]
    port = parts[1] if len(parts) > 1 else '22'
    at_parts = [p.strip() for p in parts[0].split('@') if p.strip()]
    if len(at_parts) > 1:
        user, host = at_parts[0], at_parts[1]
    else:
        host = parts[0]
        user = 'user'
    return user, host, port


def preprocess(i):

    env = i['env'] # anything you write here is visible to run.sh and to postprocess
    logger = i['automation'].logger

    # Only set via input_mapping (--out_dir_path) if the caller passed it;
    # fall back to cwd and write the resolved value back so downstream deps
    # and postprocess() see a consistent path either way.
    out_dir = env.get('MLC_MULTI_NODE_INFRAGRAPH_DIR_PATH', '')
    if not out_dir:
        out_dir = os.getcwd()
        env['MLC_MULTI_NODE_INFRAGRAPH_DIR_PATH'] = out_dir
    os.makedirs(out_dir, exist_ok=True)

    env['MLC_MULTI_NODE_INFRAGRAPH_FILE_PATH'] = os.path.join(
        out_dir, env['MLC_MULTI_NODE_INFRAGRAPH_FILE_NAME'])

    exclude_current = is_true(env.get('MLC_EXCLUDE_CURRENT_NODE', False))

    # Node ids must line up with the ones get-mlperf-multi-node-system-info
    # used when it wrote mlperf-system-info-single-node-<id>.json, otherwise
    # the merge annotates the wrong node's topology with the wrong sysinfo.
    # That script numbers the current node 0 and starts remotes at 1, unless
    # the current node is excluded, in which case remotes start at 0.
    remote_node_id_start = 0 if exclude_current else 1

    node_ids = []

    if not exclude_current:
        local_xml = env.get('MLC_LSTOPO_XML_FILE_PATH', '')
        if not local_xml or not os.path.isfile(local_xml):
            return {'return': 1,
                    'error': 'MLC_LSTOPO_XML_FILE_PATH is not set or does not '
                             'point at a file -- the get,lstopo dependency did '
                             'not run. Use _exclude_current_node if this host '
                             'is not part of the system being described.'}
        local_copy = os.path.join(out_dir, 'topo-node-0.xml')
        shutil.copyfile(local_xml, local_copy)
        logger.info(f'Local node topology captured at {local_copy}')
        node_ids.append(0)

    ssh_ids = [s.strip() for s in env.get(
        'MLC_MULTINODE_SYSTEM_SSH_IDS', '').split(',') if s.strip()]

    if not ssh_ids and exclude_current:
        return {'return': 1,
                'error': 'Either MLC_EXCLUDE_CURRENT_NODE should be False or '
                         'MLC_MULTINODE_SYSTEM_SSH_IDS should be provided'}

    failed_nodes = []

    for index, sshid in enumerate(ssh_ids):
        user, host, port = _parse_node(sshid)
        node_id = remote_node_id_start + index
        remote_dir = f'/tmp/mlperf-lstopo-node-{node_id}'
        remote_file = f'topo-node-{node_id}.xml'
        rr_tags = 'get,lstopo'

        # Clear any same-named artifact from an earlier run so the
        # post-copy existence check below cannot be satisfied by a stale file.
        local_expected = os.path.join(out_dir, remote_file)
        if os.path.isfile(local_expected):
            os.remove(local_expected)

        try:
            # Control the remote output path with pre/post shell commands
            # rather than with --out_dir_path.
            #
            # get,lstopo writes topo.xml into the shell's cwd and has no
            # input_mapping for an output path, so cd-ing before the remote
            # mlcr is what puts the file somewhere predictable. remote_run
            # joins these commands into a single SSH shell with ';', so the cd
            # persists into the mlcr call.
            #
            # Doing it this way keeps the fan-out working against whatever
            # version of mlperf-automations the remote node happens to have
            # checked out. Passing --out_dir_path would instead require every
            # remote clone to carry a matching get-lstopo change, and when it
            # does not, the flag is silently ignored, the file lands in $HOME,
            # and only the copy-back fails -- with a confusing rsync error
            # rather than anything pointing at the version skew.
            #
            # The rename is needed because rsync preserves the basename, so
            # every node would otherwise copy back to out_dir/topo.xml and
            # overwrite the previous node's topology.
            remote_pre_run_cmds = [
                f'mkdir -p {remote_dir}',
                f'cd {remote_dir}',
            ]
            remote_post_run_cmds = [
                f'mv -f {remote_dir}/topo.xml {remote_dir}/{remote_file}',
            ]
            # A fresh run_state per node: run_state is passed by reference into
            # mlc.access and comes back carrying the previous node's script
            # state, which would otherwise be replayed onto the next node.
            run_state = {'remote_run': {}}

            # mlcrr get,lstopo --remote_host=host1 --remote_user=user --remote_port=22 does the same thing as mlc.acces
            r = mlc.access({
                'action': 'remote_run',
                'automation': 'script',
                'tags': rr_tags,
                'run_cmd': rr_tags,
                'mlc_run_cmd': f'mlcr {rr_tags}',
                'remote_host': host,
                'remote_user': user,
                'remote_port': port,
                'remote_pre_run_cmds': remote_pre_run_cmds,
                'remote_post_run_cmds': remote_post_run_cmds,
                'files_to_copy_back': [f'{remote_dir}/{remote_file}'],
                'path_to_copy_back_files': out_dir,
                'run_state': run_state,
                'skip_ssh_key_file': env.get('MLC_SKIP_SSH_KEY_FILE', ''),
                'quiet': True,
            })
            if r['return'] > 0:
                logger.error(
                    f'Error obtaining lstopo topology from remote node {sshid}!')
                failed_nodes.append(sshid)
            elif not os.path.isfile(local_expected):
                # remote_run reported success but the artifact is not here.
                # Treat it as a failure rather than letting a stale file from
                # an earlier run stand in for this node's topology.
                logger.error(
                    f'{sshid}: remote_run succeeded but {remote_file} was not '
                    f'copied into {out_dir}')
                failed_nodes.append(sshid)
            else:
                logger.info(
                    f'Successfully obtained lstopo topology from remote node {sshid}')
                node_ids.append(node_id)
        except Exception as e:
            logger.error(
                f'Exception during lstopo remote_run for node {sshid}: {e}')
            failed_nodes.append(sshid)

    if not node_ids:
        return {'return': 1,
                'error': 'No node topology could be collected. Failed nodes: '
                         + ', '.join(failed_nodes)}

    if failed_nodes:
        # Fail loudly rather than silently emitting a graph that is missing
        # nodes -- a partial topology reads as a complete one downstream.
        return {'return': 1,
                'error': 'Topology collection failed for '
                         f'{len(failed_nodes)} of {len(ssh_ids)} remote '
                         f'node(s): {", ".join(failed_nodes)}'}

    # Passed to run.sh as a comma-separated list; the merge step needs to know
    # exactly which node ids have a topology file before it starts merging.
    env['MLC_MULTI_NODE_INFRAGRAPH_NODE_IDS'] = ','.join(
        str(n) for n in node_ids)

    # Reuse the MLPerf system name if the caller didn't pass --graph_name,
    # so the graph and the submission it describes stay identifiable together.
    if not env.get('MLC_MULTI_NODE_INFRAGRAPH_NAME', ''):
        env['MLC_MULTI_NODE_INFRAGRAPH_NAME'] = env.get(
            'MLC_MLPERF_SYSTEM_NAME', 'multi-node-system')

    return {'return': 0}


def postprocess(i):

    env = i['env']
    logger = i['automation'].logger

    # run.sh is expected to have written the merged graph by now; treat a
    # missing file as a failure rather than reporting success with a
    # dangling path.
    out_path = env.get('MLC_MULTI_NODE_INFRAGRAPH_FILE_PATH', '')
    if not out_path or not os.path.isfile(out_path):
        return {'return': 1,
                'error': f'Expected merged infragraph at {out_path}, but it '
                         'was not produced.'}

    out_dir = env['MLC_MULTI_NODE_INFRAGRAPH_DIR_PATH']

    env['MLC_MULTI_NODE_INFRAGRAPH_DEV_YAML_PATH'] = os.path.join(
        out_dir, 'dev-multi-node.yaml')

    # Visuals are only generated when _no_visualize isn't set, so only
    # publish the path if run.sh actually produced the directory.
    visuals_dir = os.path.join(out_dir, 'visuals')
    if os.path.isdir(visuals_dir):
        env['MLC_MULTI_NODE_INFRAGRAPH_VISUALS_DIR_PATH'] = visuals_dir

    logger.info(f'Merged multi-node infragraph written to {out_path}')

    return {'return': 0}
