from mlc import utils
import os
import hashlib


def preprocess(i):

    variation_tags = i.get('variation_tags', [])

    os_info = i['os_info']

    windows = os_info['platform'] == 'windows'

#    xsep = '^&^&' if windows else '&&'
    xsep = '&&'
    q = '"' if os_info['platform'] == 'windows' else "'"

    env = i['env']

    meta = i['meta']

    automation = i['automation']

    quiet = (env.get('MLC_QUIET', False) == 'yes')

    filename = env.get('MLC_EXTRACT_FILEPATH', '')
    if filename == '':
        return {
            'return': 1, 'error': 'Extract with no download requested and MLC_EXTRACT_FILEPATH is not set'}

    if windows:
        filename = filename.replace("%", "%%")

    env['MLC_EXTRACT_FILENAME'] = filename

    # Check if extract to some path outside CM cache (to reuse large files
    # later if cache is cleaned)
    extract_path = env.get('MLC_EXTRACT_PATH', '')
    if extract_path != '':
        if not os.path.exists(extract_path):
            os.makedirs(extract_path, exist_ok=True)

        os.chdir(extract_path)

    # By default remove archive after extraction
    remove_extracted = False if env.get(
        'MLC_EXTRACT_REMOVE_EXTRACTED',
        '').lower() == 'no' else True

    if filename.endswith(".zip") or filename.endswith(".pth"):
        env['MLC_EXTRACT_TOOL'] = "unzip"
    elif filename.endswith(".tar.gz"):
        if windows:
            x = '"' if ' ' in filename else ''
            env['MLC_EXTRACT_CMD0'] = 'gzip -d ' + x + filename + x
            filename = filename[:-3]  # leave only .tar
            env['MLC_EXTRACT_TOOL_OPTIONS'] = ' -xvf'
            env['MLC_EXTRACT_TOOL'] = 'tar '
        elif os_info['platform'] == 'darwin':
            env['MLC_EXTRACT_TOOL_OPTIONS'] = ' -xvzf '
            env['MLC_EXTRACT_TOOL'] = 'tar '
        else:
            env['MLC_EXTRACT_TOOL_OPTIONS'] = ' --skip-old-files -xvzf '
            env['MLC_EXTRACT_TOOL'] = 'tar '
    elif filename.endswith(".tar.xz"):
        if windows:
            x = '"' if ' ' in filename else ''
            env['MLC_EXTRACT_CMD0'] = 'xz -d ' + x + filename + x
            filename = filename[:-3]  # leave only .tar
            env['MLC_EXTRACT_TOOL_OPTIONS'] = ' -xvf'
            env['MLC_EXTRACT_TOOL'] = 'tar '
        else:
            env['MLC_EXTRACT_TOOL_OPTIONS'] = ' -xvJf'
            env['MLC_EXTRACT_TOOL'] = 'tar '
    elif filename.endswith(".tar"):
        env['MLC_EXTRACT_TOOL_OPTIONS'] = ' -xvf'
        env['MLC_EXTRACT_TOOL'] = 'tar '
    elif filename.endswith(".gz"):
        # Check target filename
        extracted_filename = env.get('MLC_EXTRACT_EXTRACTED_FILENAME', '')
        if extracted_filename == '':
            extracted_filename = os.path.basename(filename)[:-3]
            env['MLC_EXTRACT_EXTRACTED_FILENAME'] = extracted_filename

        x = '-c' if windows else '-k'
        env['MLC_EXTRACT_TOOL_OPTIONS'] = ' -d ' + \
            (x + ' ' if not remove_extracted else '') + \
            ' > ' + q + extracted_filename + q + ' < '

        env['MLC_EXTRACT_TOOL'] = 'gzip '
    elif env.get('MLC_EXTRACT_UNZIP', '') == 'yes':
        env['MLC_EXTRACT_TOOL'] = 'unzip '
    elif env.get('MLC_EXTRACT_UNTAR', '') == 'yes':
        env['MLC_EXTRACT_TOOL_OPTIONS'] = ' -xvf'
        env['MLC_EXTRACT_TOOL'] = 'tar '
    elif env.get('MLC_EXTRACT_GZIP', '') == 'yes':
        env['MLC_EXTRACT_CMD'] = 'gzip '
        env['MLC_EXTRACT_TOOL_OPTIONS'] = ' -d ' + \
            ('-k ' if not remove_extracted else '')
    else:
        return {'return': 1,
                'error': 'Neither MLC_EXTRACT_UNZIP nor MLC_EXTRACT_UNTAR is yes'}

    env['MLC_EXTRACT_PRE_CMD'] = ''

    extract_to_folder = env.get('MLC_EXTRACT_TO_FOLDER', '')

    # Check if extract to additional folder in the current directory (or external path)
    # to avoid messing up other files and keep clean directory structure
    # particularly if archive has many sub-directories and files
    if extract_to_folder != '':
        if 'tar ' in env['MLC_EXTRACT_TOOL']:
            x = '' if windows else '-p'
            y = '"' if ' ' in extract_to_folder else ''

            # env['MLC_EXTRACT_TOOL_OPTIONS'] = ' --one-top-level='+ env['MLC_EXTRACT_TO_FOLDER'] + env.get('MLC_EXTRACT_TOOL_OPTIONS', '')
            env['MLC_EXTRACT_TOOL_OPTIONS'] = ' -C ' + y + extract_to_folder + \
                y + ' ' + env.get('MLC_EXTRACT_TOOL_OPTIONS', '')
            env['MLC_EXTRACT_PRE_CMD'] = 'mkdir ' + x + ' ' + \
                y + extract_to_folder + y + ' ' + xsep + ' '
            env['MLC_EXTRACT_EXTRACTED_FILENAME'] = extract_to_folder

        elif 'unzip' in env['MLC_EXTRACT_TOOL']:
            env['MLC_EXTRACT_TOOL_OPTIONS'] = ' -d ' + q + extract_to_folder + q
            env['MLC_EXTRACT_EXTRACTED_FILENAME'] = extract_to_folder

    x = '"' if ' ' in filename else ''
    env['MLC_EXTRACT_CMD'] = env['MLC_EXTRACT_PRE_CMD'] + env['MLC_EXTRACT_TOOL'] + ' ' + \
        env.get('MLC_EXTRACT_TOOL_EXTRA_OPTIONS', '') + \
        ' ' + env.get('MLC_EXTRACT_TOOL_OPTIONS', '') + ' ' + x + filename + x

    print('')
    print('Current directory: {}'.format(os.getcwd()))
    print('Command line: "{}"'.format(env['MLC_EXTRACT_CMD']))
    print('')

    final_file = env.get('MLC_EXTRACT_EXTRACTED_FILENAME', '')

    if final_file != '':
        if env.get('MLC_EXTRACT_EXTRACTED_CHECKSUM_FILE', '') != '':
            env['MLC_EXTRACT_EXTRACTED_CHECKSUM_CMD'] = f"cd {q}{final_file}{q} {xsep}  md5sum -c {q}{env['MLC_EXTRACT_EXTRACTED_CHECKSUM_FILE']}{q}"
        elif env.get('MLC_EXTRACT_EXTRACTED_CHECKSUM', '') != '':
            x = '*' if os_info['platform'] == 'windows' else ''
            env['MLC_EXTRACT_EXTRACTED_CHECKSUM_CMD'] = "echo {} {}{q}{}{q} | md5sum -c".format(
                env.get('MLC_EXTRACT_EXTRACTED_CHECKSUM'), x, env['MLC_EXTRACT_EXTRACTED_FILENAME'])
        else:
            env['MLC_EXTRACT_EXTRACTED_CHECKSUM_CMD'] = ""
    else:
        env['MLC_EXTRACT_EXTRACTED_CHECKSUM_CMD'] = ""

# Not needed - can be simpler with cmd /c {empty}
#    if os_info['platform'] == 'windows':
#        # Check that if empty CMD, should add ""
#        for x in ['MLC_EXTRACT_CMD', 'MLC_EXTRACT_EXTRACTED_CHECKSUM_CMD']:
#            env[x+'_USED']='YES' if env.get(x,'')!='' else 'NO'

    # If force cache, add filepath to tag unless _path is used ...
    path_tag = 'path.' + filename

    add_extra_cache_tags = []
    if path_tag not in variation_tags:
        add_extra_cache_tags.append(path_tag)

    return {'return': 0, 'add_extra_cache_tags': add_extra_cache_tags}


def postprocess(i):

    automation = i['automation']

    env = i['env']

    extract_to_folder = env.get('MLC_EXTRACT_TO_FOLDER', '')
    extract_path = env.get('MLC_EXTRACT_PATH', '')

    extracted_file = env.get('MLC_EXTRACT_EXTRACTED_FILENAME', '')

    # Preparing filepath
    #   Can be either full extracted filename (such as model) or folder

    if extracted_file != '':
        filename = os.path.basename(extracted_file)

# We do not use this env variable anymore
#        folderpath = env.get('MLC_EXTRACT_EXTRACT_TO_PATH', '')
        folderpath = extract_path if extract_path != '' else os.getcwd()

        filepath = os.path.join(folderpath, filename)
    else:

        filepath = os.getcwd()  # Extracted to the root cache folder

    if not os.path.exists(filepath):
        return {
            'return': 1, 'error': 'Path {} was not created or doesn\'t exist'.format(filepath)}
# return {'return':1, 'error': 'MLC_EXTRACT_EXTRACTED_FILENAME and
# MLC_EXTRACT_TO_FOLDER are not set'}

    env['MLC_EXTRACT_EXTRACTED_PATH'] = filepath

    # Set external environment variable with the final path
    if env.get('MLC_EXTRACT_FINAL_ENV_NAME', '') != '':
        env[env['MLC_EXTRACT_FINAL_ENV_NAME']] = filepath

    # Detect if this file will be deleted or moved
    env['MLC_GET_DEPENDENT_CACHED_PATH'] = filepath

    # Check if need to remove archive after extraction
    if env.get('MLC_EXTRACT_REMOVE_EXTRACTED', '').lower() != 'no':
        archive_filepath = env.get('MLC_EXTRACT_FILEPATH', '')
        if archive_filepath != '' and os.path.isfile(archive_filepath):
            os.remove(archive_filepath)

    # Since may change directory, check if need to clean some temporal files
    automation.clean_some_tmp_files({'env': env})

    return {'return': 0}
