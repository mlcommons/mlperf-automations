"""
Schema specification for script meta.yaml files.

Defines all valid keys, their types, and nesting rules for script meta.yaml.
Used by validate_meta() to check meta files during indexing and linting.
"""

# ─── Type aliases ───────────────────────────────────────────────
# Each value is a set of allowed Python type names (from type().__name__).
# "optional" means the key may be absent; all keys are optional unless in REQUIRED_KEYS.

STR = {"str"}
BOOL = {"bool"}
INT = {"int"}
LIST = {"list"}
DICT = {"dict"}
STR_OR_BOOL = {"str", "bool"}
INT_OR_FLOAT = {"int", "float"}
STR_OR_FLOAT = {"str", "float"}
STR_OR_LIST = {"str", "list"}

# ─── Required top-level keys ───────────────────────────────────
REQUIRED_KEYS = {"alias", "uid", "automation_alias", "automation_uid"}

# ─── Top-level key specification ───────────────────────────────
# key -> set of allowed type names
TOP_LEVEL_SCHEMA = {
    # Identity (required)
    "alias": STR,
    "uid": STR,
    "automation_alias": STR,
    "automation_uid": STR,

    # Metadata
    "name": STR,
    "category": STR,
    "tags": LIST,        # list[str]
    "tags_help": STR,
    "developers": STR,
    "sort": INT,
    "category_sort": INT,
    "private": BOOL,
    "min_mlc_version": STR,

    # Environment
    "env": DICT,        # dict[str, str]
    "default_env": DICT,        # dict[str, str]
    "new_env_keys": LIST,        # list[str]
    "new_state_keys": LIST,        # list[str]
    "local_env_keys": LIST,        # list[str]
    "file_path_env_keys": LIST,        # list[str]
    "folder_path_env_keys": LIST,        # list[str]

    # Cache
    "cache": STR_OR_BOOL,
    "can_force_cache": BOOL,
    "cache_expiration": STR,
    "extra_cache_tags_from_env": LIST,       # list[str]
    "clean_files": LIST,        # list[str]
    "clean_output_files": LIST,        # list[str]

    # Input mapping
    # dict[str, str]  input_name -> ENV_KEY (or null)
    "input_mapping": {*DICT, "NoneType"},
    # dict[str, dict] input_name -> {desc, choices, ...} (or null)
    "input_description": {*DICT, "NoneType"},
    "env_key_mappings": DICT,        # dict[str, str]

    # Dependencies
    "deps": LIST,        # list[dep_entry]
    "prehook_deps": LIST,        # list[dep_entry]
    "posthook_deps": LIST,        # list[dep_entry]
    "post_deps": LIST,        # list[dep_entry]
    "predeps": BOOL,

    # Variations
    "variations": DICT,        # dict[str, variation_entry]
    "variation_groups_order": LIST,        # list[str]
    "default_variation": STR,
    "default_variations": DICT,        # dict[str, str]
    "invalid_variation_combinations": LIST,  # list[list[str]]
    "valid_variation_combinations": LIST,  # list[list[str]]

    # Versions
    "versions": DICT,        # dict[str, version_entry]
    "default_version": STR,

    # Docker
    "docker": DICT,        # dict - see DOCKER_SCHEMA

    # Output / debugging
    "print_env_at_the_end": DICT,        # dict[str, list[str]]
    "print_files_if_script_error": LIST,     # list[str]
    "warnings": LIST,        # list[str]
    "sudo_install": BOOL,

    # Conditional meta update
    "update_meta_if_env": LIST,        # list[dict]
    "remote_run": DICT,

    # Tests
    "tests": DICT,        # dict - see TESTS_SCHEMA
}

# ─── Dependency entry keys ──────────────────────────────────────
DEP_ENTRY_SCHEMA = {
    "tags": STR,
    "names": STR_OR_LIST,
    "env": DICT,
    "enable_if_env": DICT,
    "skip_if_env": DICT,
    "skip_if_any_env": DICT,
    "enable_if_any_env": DICT,
    "extra_cache_tags": STR,
    "update_tags_from_env_with_prefix": DICT,
    "update_tags_from_env": LIST,
    "force_env_keys": LIST,
    "force_cache": BOOL,
    "reuse_version": BOOL,
    "inherit_variation_tags": STR_OR_BOOL,
    "skip_inherit_variation_groups": LIST,
    "version": STR,
    "version_min": STR,
    "version_max": STR_OR_FLOAT,
    "version_max_usable": STR_OR_FLOAT,
    "dynamic": BOOL,
    "ignore_missing": BOOL,
    "skip_if_fake_run": BOOL,
    "verify": BOOL,
    "md5sum": STR,
    "revision": STR,
    "model_filename": STR,
    "full_subfolder": STR,
    "env_key": STR,
    "continue_on_error": BOOL,
    "ignore_script_error": BOOL,
    "inherit_cache_expiration": BOOL,
    "update_tags_if_env": DICT,
    "update_meta_if_env": LIST,
}

# ─── Variation entry keys ───────────────────────────────────────
VARIATION_ENTRY_SCHEMA = {
    "env": {*DICT, "NoneType"},
    "group": STR,
    "default": STR_OR_BOOL,
    "default_variations": DICT,
    "deps": LIST,
    "prehook_deps": LIST,
    "posthook_deps": LIST,
    "post_deps": LIST,
    "add_deps": DICT,
    "add_deps_recursive": DICT,
    "add_deps_tags": DICT,
    "new_env_keys": LIST,
    "new_state_keys": LIST,
    "base": LIST,
    "adr": DICT,
    "ad": DICT,
    "default_env": DICT,
    "state": DICT,
    "const": DICT,
    "docker": DICT,
    "alias": STR,
    "default_version": STR_OR_FLOAT,
    "required_disk_space": INT,
    "cache_expiration": {*STR, *INT},
    "cache": BOOL,
    "force_cache": BOOL,
    "update_meta_if_env": LIST,
    "warning": STR,
    "warnings": LIST,
    "names": LIST,
    "default_variation": DICT,
}

# ─── Docker section keys ────────────────────────────────────────
DOCKER_SCHEMA = {
    "real_run": BOOL,
    "run": BOOL,
    "skip_run_cmd": STR_OR_BOOL,
    "interactive": BOOL,
    "pre_run_cmds": LIST,
    "deps": LIST,
    "mounts": LIST,
    "input_mapping": DICT,
    "input_paths": LIST,
    "skip_input_for_fake_run": LIST,
    "os": STR,
    "os_version": STR,
    "base_image": STR,
    "mlc_repo": STR,
    "mlc_repo_branch": STR,
    "mlc_repo_flags": STR,
    "extra_run_args": STR,
    "all_gpus": STR,
    "user": STR,
    "use_host_user_id": BOOL,
    "use_host_group_id": STR_OR_BOOL,
    "skip_mlc_sys_upgrade": STR,
    "shm_size": STR,
    "port_maps": LIST,
    "image_tag_extra": STR,
    "fake_run_deps": BOOL,
    "pass_docker_to_script": BOOL,
    "mount_current_dir": STR,
    "use_google_dns": BOOL,
    "add_quotes_to_keys": LIST,
    "device": STR,
    "run_cmd_prefix": STR,
    "pass_user_group": BOOL,
    "default_env": DICT,
    "env": DICT,
}

# ─── Tests section keys ─────────────────────────────────────────
TESTS_SCHEMA = {
    "run_inputs": LIST,   # list[dict] - each has variations_list, env, etc.
    "needs_pat": BOOL,
}

# ─── Tests run_inputs entry keys ────────────────────────────────
TESTS_RUN_INPUT_SCHEMA = {
    "variations_list": LIST,   # list[str]
    "env": DICT,
    "test_input_index": STR,
    "disable_run_script": BOOL,
}


# ─── update_meta_if_env entry keys ──────────────────────────────
UPDATE_META_IF_ENV_SCHEMA = {
    "enable_if_env": DICT,
    "enable_if_any_env": DICT,
    "skip_if_env": DICT,
    "skip_if_any_env": DICT,
    "env": DICT,
    "default_env": DICT,
    "default_variations": DICT,
    "docker": DICT,
    "adr": DICT,
    "ad": DICT,
}


def validate_meta(data, file_path=""):
    """
    Validate a script meta.yaml dict against the schema.

    Args:
        data (dict): Parsed meta.yaml content.
        file_path (str): Path to meta file (for error messages).

    Returns:
        list[str]: List of warning/error messages. Empty if valid.
    """
    errors = []
    warnings = []

    if not isinstance(data, dict):
        return ["Meta is not a dictionary"], []

    prefix = f"{file_path}: " if file_path else ""

    # Check required keys
    for key in REQUIRED_KEYS:
        if key not in data:
            errors.append(f"{prefix}Missing required key '{key}'")

    # Check top-level keys
    for key, value in data.items():
        if key not in TOP_LEVEL_SCHEMA:
            # Check if it looks like a misplaced env variable
            if key.startswith("MLC_"):
                warnings.append(
                    f"{prefix}Key '{key}' looks like an env variable - should it be under 'env' or 'default_env'?")
            else:
                warnings.append(f"{prefix}Unknown top-level key '{key}'")
            continue

        actual_type = type(value).__name__
        allowed = TOP_LEVEL_SCHEMA[key]
        if actual_type not in allowed:
            errors.append(
                f"{prefix}Key '{key}' has type '{actual_type}', expected {allowed}")

    # Validate dependency lists
    for dep_list_key in ["deps", "prehook_deps",
                         "posthook_deps", "post_deps", "post_deps_off"]:
        deps = data.get(dep_list_key)
        if deps is None:
            continue
        if not isinstance(deps, list):
            continue
        for i, dep in enumerate(deps):
            if not isinstance(dep, dict):
                errors.append(
                    f"{prefix}{dep_list_key}[{i}] is not a dict")
                continue
            for dk, dv in dep.items():
                if dk not in DEP_ENTRY_SCHEMA:
                    warnings.append(
                        f"{prefix}{dep_list_key}[{i}]: unknown dep key '{dk}'")
                    continue
                actual = type(dv).__name__
                allowed = DEP_ENTRY_SCHEMA[dk]
                if actual not in allowed:
                    errors.append(
                        f"{prefix}{dep_list_key}[{i}].{dk} has type '{actual}', expected {allowed}")

            # Validate enable_if_env/skip_if_env values are single
            # strings/lists, not nested dicts
            for ck in ["enable_if_env", "skip_if_env",
                       "skip_if_any_env", "enable_if_any_env"]:
                cv = dep.get(ck)
                if isinstance(cv, dict):
                    for ek, ev in cv.items():
                        if isinstance(ev, (dict, list)
                                      ) and not isinstance(ev, str):
                            if isinstance(ev, list):
                                for item in ev:
                                    if not isinstance(
                                            item, (str, int, float, bool)):
                                        errors.append(
                                            f"{prefix}{dep_list_key}[{i}].{ck}.{ek} list contains non-scalar: {type(item).__name__}")

    # Validate update_meta_if_env entries
    umie = data.get("update_meta_if_env")
    if isinstance(umie, list):
        for i, entry in enumerate(umie):
            if not isinstance(entry, dict):
                errors.append(f"{prefix}update_meta_if_env[{i}] is not a dict")
                continue
            for ek, ev in entry.items():
                if ek not in UPDATE_META_IF_ENV_SCHEMA:
                    warnings.append(
                        f"{prefix}update_meta_if_env[{i}]: unknown key '{ek}'")
                    continue
                actual = type(ev).__name__
                allowed = UPDATE_META_IF_ENV_SCHEMA[ek]
                if actual not in allowed:
                    errors.append(
                        f"{prefix}update_meta_if_env[{i}].{ek} has type '{actual}', expected {allowed}")
            # Validate enable_if_env/skip_if_env values inside
            # update_meta_if_env
            for ck in ["enable_if_env", "skip_if_env",
                       "skip_if_any_env", "enable_if_any_env"]:
                cv = entry.get(ck)
                if isinstance(cv, dict):
                    for ek2, ev2 in cv.items():
                        if isinstance(ev2, (dict, list)
                                      ) and not isinstance(ev2, str):
                            if isinstance(ev2, list):
                                for item in ev2:
                                    if not isinstance(
                                            item, (str, int, float, bool)):
                                        errors.append(
                                            f"{prefix}update_meta_if_env[{i}].{ck}.{ek2} list contains non-scalar: {type(item).__name__}")

    # Validate variations
    variations = data.get("variations")
    if isinstance(variations, dict):
        for vname, vattrs in variations.items():
            if vattrs is None:
                continue  # empty variation is ok
            if not isinstance(vattrs, dict):
                warnings.append(
                    f"{prefix}variations.{vname} is not a dict (type: {type(vattrs).__name__})")
                continue
            for vk, vv in vattrs.items():
                if vk not in VARIATION_ENTRY_SCHEMA:
                    if not vk.startswith("MLC_"):
                        warnings.append(
                            f"{prefix}variations.{vname}: unknown variation key '{vk}'")
                    continue
                actual = type(vv).__name__
                allowed = VARIATION_ENTRY_SCHEMA[vk]
                if actual not in allowed:
                    errors.append(
                        f"{prefix}variations.{vname}.{vk} has type '{actual}', expected {allowed}")

    # Validate docker section
    docker = data.get("docker")
    if isinstance(docker, dict):
        for dk, dv in docker.items():
            if dk not in DOCKER_SCHEMA:
                warnings.append(
                    f"{prefix}docker: unknown key '{dk}'")
                continue
            actual = type(dv).__name__
            allowed = DOCKER_SCHEMA[dk]
            if actual not in allowed:
                errors.append(
                    f"{prefix}docker.{dk} has type '{actual}', expected {allowed}")

    # Validate tests section
    tests = data.get("tests")
    if isinstance(tests, dict):
        for tk, tv in tests.items():
            if tk not in TESTS_SCHEMA:
                warnings.append(
                    f"{prefix}tests: unknown key '{tk}'")
                continue
            actual = type(tv).__name__
            allowed = TESTS_SCHEMA[tk]
            if actual not in allowed:
                errors.append(
                    f"{prefix}tests.{tk} has type '{actual}', expected {allowed}")

        run_inputs = tests.get("run_inputs")
        if isinstance(run_inputs, list):
            for i, entry in enumerate(run_inputs):
                if entry is None:
                    continue
                if not isinstance(entry, dict):
                    errors.append(
                        f"{prefix}tests.run_inputs[{i}] is not a dict")

    # Check for variation entry keys mistakenly used as variation names
    # Exclude common short words that are legitimately used as both
    _variation_name_allowlist = {
        "default",
        "base",
        "env",
        "ad",
        "cache",
        "state",
        "alias",
        "warning",
        "const"}
    if isinstance(variations, dict):
        for vname in variations:
            if vname in VARIATION_ENTRY_SCHEMA and vname not in _variation_name_allowlist:
                warnings.append(
                    f"{prefix}variation '{vname}' looks like a variation property key used as a variation name")
            # Also check if variation attrs contain keys that look like
            # variation names
            vattrs = variations[vname]
            if isinstance(vattrs, dict):
                for vk in vattrs:
                    if vk in VARIATION_ENTRY_SCHEMA:
                        continue  # valid property
                    if vk.startswith("MLC_"):
                        continue  # env override
                    # Check if this unknown key is actually a known variation
                    # name in this script
                    if vk in variations and vk != vname:
                        warnings.append(
                            f"{prefix}variations.{vname}: key '{vk}' matches another variation name - possible indentation error")

    # Cross-key validations
    default_variation = data.get("default_variation")
    if default_variation and isinstance(variations, dict):
        if default_variation not in variations:
            errors.append(
                f"{prefix}default_variation '{default_variation}' not found in variations")

    return errors, warnings
