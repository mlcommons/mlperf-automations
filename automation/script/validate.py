import os
from mlc import utils
from script.meta_schema import validate_meta


def validate_scripts(self_module, input_params):
    """
    Validate script meta.yaml files against the schema.

    Can target a specific script (via tags/alias) or all scripts (--all).

    Args:
        self_module: Reference to the current module.
        input_params: Dictionary containing input parameters.

    Returns:
        Dictionary with 'return' code and validation summary.
    """
    quiet = input_params.get('quiet', False)
    logger = self_module.logger

    search_result = self_module.search(input_params.copy())
    if search_result['return'] > 0:
        return search_result

    scripts_list = search_result['list']
    if not scripts_list:
        return {'return': 1, 'error': 'No scripts were found'}

    total_errors = 0
    total_warnings = 0
    scripts_with_errors = []

    for script in sorted(scripts_list, key=lambda x: x.meta.get('alias', '')):
        metadata = script.meta
        script_alias = metadata.get('alias', metadata.get('uid', ''))
        script_path = script.path

        errors, warnings = validate_meta(metadata, script_alias)

        if errors:
            total_errors += len(errors)
            scripts_with_errors.append(script_alias)
            for e in errors:
                logger.error(e)

        if warnings and not quiet:
            total_warnings += len(warnings)
            for w in warnings:
                logger.warning(w)

    # Summary
    num_scripts = len(scripts_list)
    print("")
    print("=" * 60)
    print(f"  Validation Summary: {num_scripts} script(s) checked")
    print(f"  Errors:   {total_errors}")
    print(f"  Warnings: {total_warnings}")
    if scripts_with_errors:
        print(f"  Scripts with errors: {', '.join(scripts_with_errors)}")
    print("=" * 60)
    print("")

    if total_errors > 0:
        return {'return': 1,
                'error': f'{total_errors} validation error(s) found'}

    return {'return': 0}
