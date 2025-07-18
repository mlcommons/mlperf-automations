from mlc import utils
import os
import hashlib
from utils import *


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

    logger = automation.logger

    quiet = is_true(env.get('MLC_QUIET', False))

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
        if os.path.isfile(extract_path):
            extract_path = os.path.dirname(extract_path)
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
    elif filename.endswith(".tar.bz2"):
        if windows:
            x = '"' if ' ' in filename else ''
            env['MLC_EXTRACT_CMD0'] = 'bzip2 -d ' + x + filename + x
            filename = filename[:-4]  # leave only .tar
            env['MLC_EXTRACT_TOOL_OPTIONS'] = ' -xvf'
            env['MLC_EXTRACT_TOOL'] = 'tar '
        elif os_info['platform'] == 'darwin':
            env['MLC_EXTRACT_TOOL_OPTIONS'] = ' -xvjf '
            env['MLC_EXTRACT_TOOL'] = 'tar '
        else:
            env['MLC_EXTRACT_TOOL_OPTIONS'] = ' --skip-old-files -xvjf '
            env['MLC_EXTRACT_TOOL'] = 'tar '
    elif filename.endswith(".tar"):
        env['MLC_EXTRACT_TOOL_OPTIONS'] = ' -xvf'
        env['MLC_EXTRACT_TOOL'] = 'tar '
    elif filename.endswith(".7z"):
        if windows:
            env['MLC_EXTRACT_TOOL'] = '7z'
            env['MLC_EXTRACT_TOOL_OPTIONS'] = ' x -y '
        else:
            # Assumes p7zip is installed and provides the `7z` or `7zr` binary
            env['MLC_EXTRACT_TOOL'] = '7z'
            env['MLC_EXTRACT_TOOL_OPTIONS'] = ' x -y '

    elif filename.endswith(".rar"):
        if windows:
            env['MLC_EXTRACT_TOOL'] = 'unrar'
            env['MLC_EXTRACT_TOOL_OPTIONS'] = ' x -y '
        else:
            # unrar or unar may be available on Unix-like systems
            env['MLC_EXTRACT_TOOL'] = 'unrar'
            env['MLC_EXTRACT_TOOL_OPTIONS'] = ' x -y '
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
    elif is_true(env.get('MLC_EXTRACT_UNZIP', '')):
        env['MLC_EXTRACT_TOOL'] = 'unzip '
    elif is_true(env.get('MLC_EXTRACT_UNTAR', '')):
        env['MLC_EXTRACT_TOOL_OPTIONS'] = ' -xvf'
        env['MLC_EXTRACT_TOOL'] = 'tar '
    elif is_true(env.get('MLC_EXTRACT_GZIP', '')):
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
            env['MLC_EXTRACT_TOOL_OPTIONS'] = ' -d ' + \
                q + extract_to_folder + q
            env['MLC_EXTRACT_EXTRACTED_FILENAME'] = extract_to_folder

    x = q if ' ' in filename else ''
    env['MLC_EXTRACT_CMD'] = env['MLC_EXTRACT_PRE_CMD'] + env['MLC_EXTRACT_TOOL'] + ' ' + \
        env.get('MLC_EXTRACT_TOOL_EXTRA_OPTIONS', '') + \
        ' ' + env.get('MLC_EXTRACT_TOOL_OPTIONS', '') + ' ' + x + filename + x

    logger.info('')
    logger.info('Current directory: {}'.format(os.getcwd()))
    logger.info('Command line: "{}"'.format(env['MLC_EXTRACT_CMD']))
    logger.info('')

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
    folderpath = None
    extracted_file = env.get('MLC_EXTRACT_EXTRACTED_FILENAME', '')

    # Preparing filepath
    # Can be either the full extracted filename (such as model file) or folder

    if extracted_file != '':
        filename = os.path.basename(extracted_file)

# We do not use this env variable anymore
#        folderpath = env.get('MLC_EXTRACT_EXTRACT_TO_PATH', '')
        folderpath = extract_path if extract_path != '' else os.getcwd()

        filepath = os.path.join(folderpath, filename)
    else:
        filepath = os.getcwd()  # Extracted to the root cache folder
        folderpath = os.getcwd()

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
    if is_true(env.get('MLC_EXTRACT_REMOVE_EXTRACTED', '')):
        archive_filepath = env.get('MLC_EXTRACT_FILEPATH', '')
        if archive_filepath != '' and os.path.isfile(archive_filepath):
            os.remove(archive_filepath)

    # Check if only a single folder is created and if so, export the folder
    # name
    if folderpath:
        sub_items = os.listdir(folderpath)
        sub_folders = [
            item for item in sub_items if os.path.isdir(
                os.path.join(
                    folderpath, item))]
        if len(sub_folders) == 1:
            env['MLC_EXTRACT_EXTRACTED_SUBDIR_PATH'] = os.path.join(
                folderpath, sub_folders[0])

    # Since may change directory, check if need to clean some temporal files
    automation.clean_some_tmp_files({'env': env})

    return {'return': 0}
