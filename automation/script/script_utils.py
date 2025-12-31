def get_variation_and_script_tags(tags_string):

    tags = [] if tags_string == '' else tags_string.split(',')

    script_tags = []
    variation_tags = []

    for t in tags:
        t = t.strip()
        if t != '':
            if t.startswith('_'):
                tx = t[1:]
                if tx not in variation_tags:
                    variation_tags.append(tx)
            elif t.startswith('-_'):
                tx = '-' + t[2:]
                if tx not in variation_tags:
                    variation_tags.append(tx)
            else:
                script_tags.append(t)
    return {'return': 0, 'script_tags': script_tags,
            'variation_tags': variation_tags}


def select_script_and_cache(
    self,
    i,
    script_tags,
    variation_tags,
    parsed_script_alias,
    quiet,
    skip_remembered_selections=False,
    force_cache=False,
    force_skip_cache=False,
):
    """
    Search scripts by tags, resolve ambiguity, apply cache pruning,
    select a script (quiet or interactive), and return pruned cache entries.
    """

    logger = self.logger
    recursion_spaces = self.recursion_spaces

    # ---------------------------------------------------------
    # STEP 1: Script search
    ii = {
        "script_tags": script_tags,
        "variation_tags": variation_tags,
        "out": None,
    }
    for key in ["automation", "artifact", "item", "details"]:
        if i.get(key):
            ii[key] = i[key]

    r = self.search(ii)
    if r["return"] > 0:
        return r

    list_of_found_scripts = r["list"]
    script_tags_string = ",".join(script_tags)

    # ---------------------------------------------------------
    # STEP 2: Report found scripts
    mlc_script_info = i.get("script_call_prefix", "").strip() or "mlcr "
    if not mlc_script_info.endswith(" "):
        mlc_script_info += " "

    if parsed_script_alias:
        mlc_script_info += parsed_script_alias + '"'

    if script_tags or variation_tags:
        if script_tags:
            mlc_script_info += script_tags_string
        if variation_tags:
            if script_tags:
                mlc_script_info += ","
            mlc_script_info += ",".join("_" + v for v in variation_tags)

    logger.info(recursion_spaces + "* " + mlc_script_info)

    # ---------------------------------------------------------
    # STEP 3: Error handling
    if not r["found_scripts"]:
        return {
            "return": 1,
            "error": f"no scripts were found with tags: {script_tags} (when variations ignored)",
        }

    if not list_of_found_scripts:
        return {
            "return": 16,
            "error": f"no scripts were found with tags: {script_tags}\n{r.get('warning', '')}",
        }

    if (
        len(list_of_found_scripts) > 1
        and script_tags_string == ""
        and parsed_script_alias
        and "?" not in parsed_script_alias
        and "*" not in parsed_script_alias
    ):
        msg = (
            "Ambiguity in the following scripts have the same UID:\n"
            + "\n".join(" * " + s.path for s in list_of_found_scripts)
        )
        return {"return": 1, "error": msg}

    # ---------------------------------------------------------
    # STEP 4: Sort deterministically
    list_of_found_scripts = sorted(
        list_of_found_scripts,
        key=lambda s: (s.meta.get("sort", 0), s.path),
    )

    # ---------------------------------------------------------
    # STEP 5: Apply remembered selection
    if not skip_remembered_selections and len(list_of_found_scripts) > 1:
        for sel in self.remembered_selections:
            if (
                sel["type"] == "script"
                and set(sel["tags"].split(",")) == set(script_tags_string.split(","))
            ):
                list_of_found_scripts = [sel["cached_script"]]
                break

    # ---------------------------------------------------------
    # STEP 6: Determine if cache preload is needed
    preload_cached_scripts = any(
        s.meta.get("cache", False)
        or (s.meta.get("can_force_cache", False) and force_cache)
        for s in list_of_found_scripts
    )

    cache_list = []

    # STEP: cache handling
    cache_list = []

    if should_preload_cache(list_of_found_scripts,
                            force_cache) and not force_skip_cache:
        rc = search_script_cache(
            self.cache_action,
            script_tags_string,
            variation_tags,
            recursion_spaces,
            logger,
        )
        if rc["return"] > 0:
            return rc

        cache_list = rc["cache_list"]

        rc = prune_scripts_using_cache(list_of_found_scripts, cache_list)
        if rc["return"] > 0:
            return rc

        list_of_found_scripts = rc["scripts"]
        cache_list = rc["cache_list"]

    # STEP: select script (unchanged)
    if len(list_of_found_scripts) > 1:
        selected_index = select_script_item(
            list_of_found_scripts,
            "script",
            recursion_spaces,
            False,
            script_tags_string,
            quiet,
            logger,
        )
    else:
        selected_index = 0

    selected_script = list_of_found_scripts[selected_index]

    # STEP: prune cache to selected script
    cache_list = prune_cache_for_selected_script(cache_list, selected_script)

    return {
        "return": 0,
        "script": selected_script,
        "scripts": list_of_found_scripts,
        "cache_list": cache_list,
    }


def select_script_item(lst, text, recursion_spaces,
                       can_skip, script_tags_string, quiet, logger=None):
    """
    Internal: select script
    """

    string1 = recursion_spaces + \
        '    - More than 1 {} found for "{}":'.format(text, script_tags_string)

    if not logger:
        return {'return': 1, 'error': 'No logger provided'}

    # If quiet, select 0 (can be sorted for determinism)
    if quiet:
        logger.debug(string1)
        logger.debug('Selected default due to "quiet" mode')

        return 0

    # Select 1 and proceed
    logger.info(string1)
    num = 0

    for a in lst:
        meta = a.meta

        name = meta.get('name', '')

        s = a.path
        if name != '':
            s = '"' + name + '" ' + s

        x = recursion_spaces + \
            '      {}) {} ({})'.format(num, s, ','.join(meta['tags']))

        version = meta.get('version', '')
        if version != '':
            x += ' (Version {})'.format(version)

        logger.info(x)
        num += 1

    s = 'Make your selection or press Enter for 0'
    if can_skip:
        s += ' or use -1 to skip'

    x = input(recursion_spaces + '      ' + s + ': ')
    x = x.strip()
    if x == '':
        x = '0'

    selection = int(x)

    if selection < 0 and not can_skip:
        selection = 0

    if selection < 0:
        logger.info(recursion_spaces + '      Skipped')
    else:
        if selection >= num:
            selection = 0
        logger.info(
            recursion_spaces +
            '      Selected {}: {}'.format(
                selection,
                lst[selection].path))

    return selection


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


def prune_cache_for_selected_script(cache_list, selected_script):
    """
    Keep only cache entries associated with selected script.
    """
    selected_uid = selected_script.meta["uid"]

    return [
        c for c in cache_list
        if c.meta.get("associated_script_item_uid") == selected_uid
    ]
