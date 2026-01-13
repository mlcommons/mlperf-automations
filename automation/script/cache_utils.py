import os
import mlc.utils as utils
from utils import compare_versions


def check_versions(action_object, cached_script_version,
                   version_min, version_max):
    """
    Internal: check versions of the cached script

    If cached_script_version is less than version_min or greater than version_max,
        return True to skip using the cached script
    """
    skip_cached_script = False

    if cached_script_version != '':
        if version_min != '':
            ry = compare_versions({
                'version1': cached_script_version,
                'version2': version_min})
            if ry['return'] > 0:
                return ry

            if ry['comparison'] < 0:
                skip_cached_script = True

        if not skip_cached_script and version_max != '':
            ry = compare_versions({
                'version1': cached_script_version,
                'version2': version_max})
            if ry['return'] > 0:
                return ry

            if ry['comparison'] > 0:
                skip_cached_script = True

    return skip_cached_script


def get_version_tag_from_version(version, cached_tags):
    tags_to_add = []
    if version != '':
        version = str(version)
        if 'version-' + version not in cached_tags:
            cached_tags.append('version-' + version)
        if '-git-' in version:
            version_without_git_commit = version.split("-git-")[0]
            if 'version-' + version_without_git_commit not in cached_tags:
                cached_tags.append('version-' + version_without_git_commit)
    return {'return': 0}


def prepare_cache_tags(i):
    '''
    Prepare cache tags for searching and creating cache entries
    '''
    i['logger'].debug(
        i['recursion_spaces'] +
        f'  - Preparing cache tags...'
    )
    cached_tags = []
    explicit_cached_tags = []

    # Create a search query to find that we already ran this script with the same or similar input
    # It will be gradually enhanced with more "knowledge"  ...

    # script tags
    if len(i['script_tags']) > 0:
        for x in i['script_tags']:
            if x not in cached_tags:
                cached_tags.append(x)

    # found tags
    if len(i['found_script_tags']) > 0:
        for x in i['found_script_tags']:
            if x not in cached_tags:
                cached_tags.append(x)

    explicit_cached_tags = cached_tags.copy()

    # explicit variations
    if len(i['explicit_variation_tags']) > 0:
        explicit_variation_tags_string = ''

        for t in i['explicit_variation_tags']:
            if explicit_variation_tags_string != '':
                explicit_variation_tags_string += ','
            if t.startswith("-"):
                x = "-_" + t[1:]
            else:
                x = '_' + t
            explicit_variation_tags_string += x

            if x not in explicit_cached_tags:
                explicit_cached_tags.append(x)

        i['logger'].debug(
            i['recursion_spaces'] +
            '    - Prepared explicit variations: {}'.format(explicit_variation_tags_string))

    # normal variations
    if len(i['variation_tags']) > 0:
        variation_tags_string = ''

        for t in i['variation_tags']:
            if variation_tags_string != '':
                variation_tags_string += ','
            if t.startswith("-"):
                x = "-_" + t[1:]
            else:
                x = '_' + t
            variation_tags_string += x

            if x not in cached_tags:
                cached_tags.append(x)

        i['logger'].debug(
            i['recursion_spaces'] +
            '    - Prepared variations: {}'.format(variation_tags_string))

    # version tags
    r = get_version_tag_from_version(i['version'], cached_tags)
    if r['return'] > 0:
        return r

    r = get_version_tag_from_version(i['version'], explicit_cached_tags)
    if r['return'] > 0:
        return r

    # Add extra cache tags (such as "virtual" for python)
    if len(i['extra_cache_tags']) > 0:
        for t in i['extra_cache_tags']:
            if t not in cached_tags:
                cached_tags.append(t)
                explicit_cached_tags.append(t)

    # env-driven tags
    # Add tags from deps (will be also duplicated when creating new cache
    # entry)
    extra_cache_tags_from_env = i['meta'].get('extra_cache_tags_from_env', [])
    for extra_cache_tags in extra_cache_tags_from_env:
        key = extra_cache_tags['env']
        prefix = extra_cache_tags.get('prefix', '')

        v = i['env'].get(key, '').strip()
        if v != '':
            for t in v.split(','):
                x = 'deps-' + prefix + t
                if x not in cached_tags:
                    cached_tags.append(x)
                    explicit_cached_tags.append(x)

    return cached_tags, explicit_cached_tags


def search_cache(i, explicit_cached_tags):
    '''
    Prune cache_lists based on prepared cache tags
    '''

    i['logger'].debug(
        i['recursion_spaces'] +
        '    - Pruning cache list outputs with the following tags: {}'.format(explicit_cached_tags))

    cache_list = i['cache_list']
    pruned_cache_list = [
        item
        for item in cache_list
        if set(explicit_cached_tags) <= set(item.meta.get('tags', []))
    ]

    return pruned_cache_list


def apply_remembered_cache_selection(
        i, explicit_search_tags, found_cached_scripts):
    '''
    Apply remembered cache selection if any
    '''
    if i['skip_remembered_selections'] or len(found_cached_scripts) <= 1:
        #i['logger'].debug(
        #    i['recursion_spaces'] +
        #    f'  - Skipping remembered cache selections...'
        #)
        return found_cached_scripts

    for selection in i['remembered_selections']:
        if selection['type'] == 'cache' and set(
                selection['tags'].split(',')) == set(explicit_search_tags):
            tmp_version_in_cached_script = selection['cached_script'].meta.get(
                'version', '')
            skip_cached_script = check_versions(
                i['self'].action_object,
                tmp_version_in_cached_script,
                i['version_min'],
                i['version_max']
            )
            if skip_cached_script:
                return {'return': 2, 'error': 'The version of the previously remembered selection for a given script ({}) mismatches the newly requested one'.format(
                    tmp_version_in_cached_script)}
            else:
                found_cached_scripts = [selection['cached_script']]
                i['logger'].debug(
                    i['recursion_spaces'] +
                    '  - Found remembered selection with tags "{}"!'.format(explicit_search_tags))
                return [selection['cached_script']]

    return found_cached_scripts


def validate_cached_scripts(i, found_cached_scripts):
    '''
    Validate found cached scripts and return only valid ones
    '''
    valid = []
    if len(found_cached_scripts) > 0:
        for cached_script in found_cached_scripts:
            if is_cached_entry_valid(i, cached_script):
                valid.append(cached_script)

    return valid


def is_cached_entry_valid(i, cached_script):
    '''
    Validate a cached script entry
    Returns True if valid, False otherwise
    '''
    # Check dependent paths
    if not validate_dependent_paths(i, cached_script):
        return False

    # Run validate_cache script if present
    detected_version = run_validate_cache_if_present(i, cached_script)
    # Get cached version
    cached_version = cached_script.meta.get('version', '')

    if cached_version and detected_version and cached_version != detected_version:
        # Cached version mismatch
        return False

    # check_versions returns True if cache should be skipped
    return not check_versions(
        i['self'].action_object,
        cached_version,
        i['version_min'],
        i['version_max']
    )


def validate_dependent_paths(i, cached_script):
    '''
    Validate dependent paths for a cached script entry
    Returns True if all dependent paths are present, False otherwise
    '''
    dependent_paths = []

    # single dependent path
    dependent_cached_path = cached_script.meta.get('dependent_cached_path')
    if dependent_cached_path:
        dependent_paths.append(dependent_cached_path)

    # multiple dependent paths (colon-separated)
    dependent_cached_paths = cached_script.meta.get(
        'dependent_cached_paths', '').split(':')
    dependent_paths += [p for p in dependent_cached_paths if p]

    if not dependent_paths:
        return True

    for dep in dependent_paths:
        if os.path.exists(dep):
            continue

        # TODO Need to restrict the below check to within container
        # env
        i['env']['tmp_dep_cached_path'] = dep
        from script import docker_utils
        r = docker_utils.get_container_path_script(i['env'])
        if not os.path.exists(r.get('value_env', '')):
            i['logger'].debug(
                i['recursion_spaces'] +
                f'  - Skipping cached entry as dependent path is missing: {r.get("value_env")}'
            )
            return False

    return True


def run_validate_cache_if_present(i, cached_script):
    '''
    Run validate_cache script if present in the script directory
    Returns detected version if validation passes, None otherwise
    '''
    import copy

    os_info = i['self'].os_info
    # Bat extension for this host OS
    bat_ext = os_info['bat_ext']
    script_path = i['found_script_path']

    validate_script = os.path.join(script_path, f'validate_cache{bat_ext}')
    if not os.path.exists(validate_script):
        return None

    i['logger'].debug(
        i['recursion_spaces'] +
        f'  - Validating cached entry: {cached_script.path}'
    )

    # reconstruct env/state from cached metadata
    env_tmp = copy.deepcopy(i['env'])
    state_tmp = copy.deepcopy(i['state'])

    path_to_cached_state_file = os.path.join(
        cached_script.path,
        i['self'].file_with_cached_state
    )

    r = utils.load_json(file_name=path_to_cached_state_file)
    if r['return'] > 0:
        return None

    cached_meta = r.get("meta")
    if not cached_meta:
        return None
    new_env = cached_meta.get("new_env", {})
    if new_env:
        env_tmp.update(new_env)
    new_state = cached_meta.get("new_state", {})
    if new_state:
        state_tmp.update(new_state)

    # re-run deps
    deps = i['meta'].get('deps')
    if deps:
        r = i['self']._call_run_deps(
            deps,
            i['self'].local_env_keys,
            i['meta'].get('local_env_keys', []),
            i['recursion_spaces'] + i['extra_recursion_spaces'],
            i['variation_tags_string'],
            True,
            '',
            i['show_time'],
            i['extra_recursion_spaces'],
            i['run_state']
        )
        if r['return'] > 0:
            return None

    run_script_input = {
        'path': script_path,
        'bat_ext': bat_ext,
        'os_info': os_info,
        'recursion_spaces': i['recursion_spaces'],
        'tmp_file_run': i['self'].tmp_file_run,
        'self': i['self'],
        'meta': i['meta'],
        'customize_code': i['customize_code'],
        'customize_common_input': i['customize_common_input'],
    }

    r = i['self'].run_native_script({
        'run_script_input': run_script_input,
        'env': env_tmp,
        'script_name': 'validate_cache',
        'detect_version': True
    })

    if r['return'] > 0:
        return None

    return r.get('version')

##############################################################################


def find_cached_script(i):
    """
    Internal automation function: find cached script

    Args:
      (MLC input dict):

      deps (dict): deps dict
      update_deps (dict): key matches "names" in deps

    Returns:
       (MLC return dict):
       * return (int): return code == 0 if no error and >0 if error
       * (error) (str): error string if return>0
    """
    # 1. Prepare cache tags
    # 2. If new_cache_entry, return empty
    # 3. Search cache
    # 4. Apply remembered cache selection
    # 5. Validate cached scripts

    i['logger'].debug(
        i['recursion_spaces'] +
        '  - Checking if script execution is already cached ...')

    cached_tags, explicit_cached_tags = prepare_cache_tags(i)

    if i['new_cache_entry']:
        i['logger'].debug(
            i['recursion_spaces'] +
            f'  - New cache entry requested, skipping cache search.'
        )
        return {'return': 0, 'cached_tags': cached_tags,
                'search_tags': '', 'found_cached_scripts': []}

    found_cached_scripts = search_cache(i, explicit_cached_tags)

    found_cached_scripts = apply_remembered_cache_selection(
        i, explicit_cached_tags, found_cached_scripts)
    found_cached_scripts = validate_cached_scripts(i, found_cached_scripts)

    search_tags = '-tmp'
    if len(explicit_cached_tags) > 0:
        search_tags += ',' + ','.join(explicit_cached_tags)

    return {'return': 0, 'cached_tags': cached_tags,
            'search_tags': search_tags, 'found_cached_scripts': found_cached_scripts}


##########################################################################


def fix_cache_paths(cached_path, env):

    current_cache_path = cached_path

    new_env = env  # just a reference

    for key, val in new_env.items():
        # Check for a path separator in a string and determine the
        # separator
        if isinstance(val, str) and any(sep in val for sep in [
                "/local/cache/", "\\local\\cache\\"]):
            sep = "/" if "/local/cache/" in val else "\\"

            path_split = val.split(sep)
            repo_entry_index = path_split.index("local")
            loaded_cache_path = sep.join(
                path_split[0:repo_entry_index + 2])
            if loaded_cache_path != current_cache_path and os.path.exists(
                    current_cache_path):
                new_env[key] = val.replace(
                    loaded_cache_path, current_cache_path).replace(sep, "/")

        elif isinstance(val, list):
            for i, val2 in enumerate(val):
                if isinstance(val2, str) and any(sep in val2 for sep in [
                        "/local/cache/", "\\local\\cache\\"]):
                    sep = "/" if "/local/cache/" in val2 else "\\"

                    path_split = val2.split(sep)
                    repo_entry_index = path_split.index("local")
                    loaded_cache_path = sep.join(
                        path_split[0:repo_entry_index + 2])
                    if loaded_cache_path != current_cache_path and os.path.exists(
                            current_cache_path):
                        new_env[key][i] = val2.replace(
                            loaded_cache_path, current_cache_path).replace(sep, "/")

    return {'return': 0, 'new_env': new_env}


def prune_cache_for_selected_script(cache_list, selected_script):
    """
    Keep only cache entries associated with selected script.
    """
    selected_uid = selected_script.meta["uid"]

    return [
        c for c in cache_list
        if c.meta.get("associated_script_item_uid") == selected_uid
    ]


def prune_scripts_using_cache(scripts, cache_list):
    """
    Retain only scripts that have matching cache entries.
    """
    pruned_scripts = []

    for cache_entry in cache_list:
        assoc = cache_entry.meta.get("associated_script_item", "")
        if "," not in assoc:
            return {
                "return": 1,
                "error": f'MLC artifact format is wrong "{assoc}" - no comma found',
            }

        uid = assoc.split(",", 1)[1]
        cache_entry.meta["associated_script_item_uid"] = uid

        for script in scripts:
            if script.meta.get("uid") == uid and script not in pruned_scripts:
                pruned_scripts.append(script)

    # Avoid over-pruning
    if pruned_scripts:
        scripts = pruned_scripts

    return {
        "return": 0,
        "scripts": scripts,
        "cache_list": cache_list,
    }


def search_script_cache(
    cache_action,
    script_tags_string,
    variation_tags,
    recursion_spaces,
    logger,
):
    """
    Search cache entries for given script & variation tags.
    """
    cache_tags = "-tmp"

    if script_tags_string:
        cache_tags += "," + script_tags_string

    if variation_tags:
        cache_tags += ",_" + ",_".join(variation_tags)

    # Fix variation exclusion syntax
    cache_tags = cache_tags.replace(",_-", ",-_")

    logger.debug(
        recursion_spaces +
        f"  - Searching for cached script outputs with tags: {cache_tags}"
    )

    rc = cache_action.access(
        {
            "action": "search",
            "target_name": "cache",
            "tags": cache_tags,
        }
    )

    if rc["return"] > 0:
        return rc

    return {
        "return": 0,
        "cache_list": rc["list"],
    }


def should_preload_cache(scripts, force_cache=False):
    """
    Return True if at least one script requires or allows caching.
    """
    for script in scripts:
        if script.meta.get("cache", False):
            return True
        if script.meta.get("can_force_cache", False) and force_cache:
            return True
    return False
