from mlc.utils import *


def is_true(val):
    return str(val).lower() in ["1", "true", "on", "yes"]


def is_false(val):
    return str(val).lower() in ["0", "false", "off", "no"]


def get_host_os_info(i={}):
    """
    Get some host platform name (currently windows or linux) and OS bits

    Args:
       (input dict):

       (bits) (str): force host platform bits

    Returns:
       (dict):

       * return (int): return code == 0 if no error and >0 if error
       * (error) (str): error string if return>0

       * info (dict):
         * platform (str): "windows", "linux" or "darwin"
         * bat_ext (str): ".bat" or ".sh"
         * bits (str): 32 or 64 bits
         * python_bits 9str): python bits

    """

    import os
    import platform
    import struct

    info = {}

    pbits = str(8 * struct.calcsize("P"))

    if platform.system().lower().startswith('win'):
        platform_name = 'windows'
        info['bat_ext'] = '.bat'
        info['set_env'] = 'set ${key}=${value}'
        info['env_separator'] = ';'
        info['env_var'] = '%env_var%'
        info['bat_rem'] = 'rem ${rem}'
        info['run_local_bat'] = 'call ${bat_file}'
        info['run_local_bat_from_python'] = 'call ${bat_file}'
        info['run_bat'] = 'call ${bat_file}'
        info['start_script'] = ['@echo off', '']
        info['env'] = {
            "MLC_WINDOWS": "yes"
        }
    else:
        if platform.system().lower().startswith('darwin'):
            platform_name = 'darwin'
        else:
            platform_name = 'linux'

        info['bat_ext'] = '.sh'
        info['set_env'] = 'export ${key}="${value}"'
        info['env_separator'] = ':'
        info['env_var'] = '${env_var}'
        info['set_exec_file'] = 'chmod 755 "${file_name}"'
        info['bat_rem'] = '# ${rem}'
        info['run_local_bat'] = '. ./${bat_file}'
        info['run_local_bat_from_python'] = 'bash -c ". ./${bat_file}"'
        info['run_bat'] = '. ${bat_file}'
        info['start_script'] = ['#!/bin/bash', '']
        info['env'] = {}

    info['platform'] = platform_name
    info['env']['MLC_HOST_PLATFORM_FLAVOR'] = platform.machine()
    info['env']['MLC_HOST_OS_TYPE'] = platform_name

    obits = i.get('bits', '')
    if obits == '':
        obits = '32'
        if platform_name == 'windows':
            # Trying to get fast way to detect bits
            if os.environ.get('ProgramW6432', '') != '' or os.environ.get(
                    'ProgramFiles(x86)', '') != '':  # pragma: no cover
                obits = '64'
        else:
            # On Linux use first getconf LONG_BIT and if doesn't work use
            # python bits

            obits = pbits

            r = generate_temp_file({})
            if r['return'] > 0:
                return r

            fn = r['file_name']

            cmd = 'getconf LONG_BIT > ' + fn
            rx = os.system(cmd)

            if rx == 0:
                r = load_txt(file_name=fn, remove_after_read=True)

                if r['return'] == 0:
                    s = r['string'].strip()
                    if len(s) > 0 and len(s) < 4:
                        obits = s
            else:
                if os.path.isfile(fn):
                    os.remove(fn)

    info['bits'] = obits
    info['python_bits'] = pbits

    return {'return': 0, 'info': info}

##########################################################################


def download_file(i):
    """
    Download file using requests

    Args:
       (CM input dict):

       url (str): URL with file
       (filename) (str): explicit file name
       (path) (str): path to record file (or current if empty)
       (chunk_size) (int): chunck size in bytes (65536 by default)
       (text) (str): print text before downloaded status ("Downloaded: " by default)
       (verify) (bool): verify SSL certificate if True (True by default)
                        can be switched by global env MLC_UTILS_DOWNLOAD_VERIFY_SSL = no

    Returns:
       (CM return dict):

       * return (int): return code == 0 if no error and >0 if error
       * (error) (str): error string if return>0

       * filename (str): file name
       * path (str): path to file
       * size (int): file size

    """

    import requests
    import time
    import sys
    from urllib import parse

    # Get URL
    url = i['url']

    # Check file name
    file_name = i.get('filename', '')
    if file_name == '':
        parsed_url = parse.urlparse(url)
        file_name = os.path.basename(parsed_url.path)

    # Check path
    path = i.get('path', '')
    if path is None or path == '':
        path = os.getcwd()

    # Output file
    path_to_file = os.path.join(path, file_name)

    if os.path.isfile(path_to_file):
        os.remove(path_to_file)

    print('Downloading to {}'.format(path_to_file))
    print('')

    # Download
    size = -1
    downloaded = 0
    chunk_size = i.get('chunk_size', 65536)

    text = i.get('text', 'Downloaded: ')

    if 'MLC_VERIFY_SSL' in os.environ:
        verify = is_true(os.environ['MLC_VERIFY_SSL'])
    else:
        verify = is_true(i.get('verify_ssl', True))

    try:
        with requests.get(url, stream=True, allow_redirects=True, verify=verify) as download:
            download.raise_for_status()

            size_string = download.headers.get('Content-Length')

            if size_string is None:
                transfer_encoding = download.headers.get(
                    'Transfer-Encoding', '')
                if transfer_encoding != 'chunked':
                    return {'return': 1, 'error': 'did not receive file'}
                else:
                    size_string = "0"

            size = int(size_string)

            with open(path_to_file, 'wb') as output:
                for chunk in download.iter_content(chunk_size=chunk_size):

                    if chunk:
                        output.write(chunk)
                    if size == 0:
                        continue
                    downloaded += 1
                    percent = downloaded * chunk_size * 100 / size

                    sys.stdout.write("\r{}{:3.0f}%".format(text, percent))
                    sys.stdout.flush()

                sys.stdout.write("\r{}{:3.0f}%".format(text, 100))
                sys.stdout.flush()

    except Exception as e:
        return {'return': 1, 'error': format(e)}

    print('')
    if size == 0:
        file_stats = os.stat(path_to_file)
        size = file_stats.st_size

    return {'return': 0, 'filename': file_name,
            'path': path_to_file, 'size': size}

##########################################################################


def unzip_file(i):
    """
    Unzip file

    Args:
       (CM input dict):

       filename (str): explicit file name
       (path) (str): path where to unzip file (current path otherwise)
       (strip_folders) (int): strip first folders

    Returns:
       (CM return dict):

       * return (int): return code == 0 if no error and >0 if error
       * (error) (str): error string if return>0

    """

    import zipfile

    # Check file name
    file_name = i['filename']

    if not os.path.isfile(file_name):
        return {'return': 1,
                'error': 'file {} not found'.format(file_name)}

    console = i.get('out') == 'con'

    file_name_handle = open(file_name, 'rb')
    file_name_zip = zipfile.ZipFile(file_name_handle)

    info_files = file_name_zip.infolist()

    path = i.get('path', '')
    if path is None or path == '':
        path = os.getcwd()

    strip_folders = i.get('strip_folders', 0)

    # Unpacking zip
    for info in info_files:
        f = info.filename
        permissions = info.external_attr

        if not f.startswith('..') and not f.startswith(
                '/') and not f.startswith('\\'):
            f_zip = f

            if strip_folders > 0:
                fsplit = f.split('/')  # Zip standard on all OS
                f = '/'.join(fsplit[strip_folders:])

            file_path = os.path.join(path, f)

            if f.endswith('/'):
                # create directory
                if not os.path.exists(file_path):
                    os.makedirs(file_path)
            else:
                dir_name = os.path.dirname(file_path)
                if not os.path.exists(dir_name):
                    os.makedirs(dir_name)

                # extract file
                file_out = open(file_path, 'wb')
                file_out.write(file_name_zip.read(f_zip))
                file_out.close()

                if permissions > 0xffff:
                    os.chmod(file_path, permissions >> 16)

    file_name_zip.close()
    file_name_handle.close()

    return {'return': 0}

##########################################################################


def compare_versions(i):
    """
    Compare versions

    Args:

       version1 (str): version 1
       version2 (str): version 2

    Returns:
       (CM return dict):

       * comparison (int):  1 - version 1 > version 2
                            0 - version 1 == version 2
                           -1 - version 1 < version 2

       * return (int): return code == 0 if no error and >0 if error
       * (error) (str): error string if return>0
    """

    version1 = i['version1']
    version2 = i['version2']

    l_version1 = version1.split('.')
    l_version2 = version2.split('.')

    # 3.9.6 vs 3.9
    # 3.9 vs 3.9.6

    i_version1 = [int(v) for v in l_version1 if v.isdigit()]
    i_version2 = [int(v) for v in l_version2 if v.isdigit()]

    comparison = 0

    for index in range(max(len(i_version1), len(i_version2))):
        v1 = i_version1[index] if index < len(i_version1) else 0
        v2 = i_version2[index] if index < len(i_version2) else 0

        if v1 > v2:
            comparison = 1
            break
        elif v1 < v2:
            comparison = -1
            break

    return {'return': 0, 'comparison': comparison}

##########################################################################


def json2yaml(i):
    """
    Convert JSON file to YAML

    Args:

       input (str): input file (.json)
       (output) (str): output file (.yaml)

    Returns:
       (CM return dict):

       * return (int): return code == 0 if no error and >0 if error
       * (error) (str): error string if return>0
    """

    input_file = i.get('input', '')

    if input_file == '':
        return {'return': 1, 'error': 'please specify --input={json file}'}

    output_file = i.get('output', '')

    r = load_json(input_file, check_if_exists=True)
    if r['return'] > 0:
        return r

    meta = r['meta']

    if output_file == '':
        output_file = input_file[:-
                                 5] if input_file.endswith('.json') else input_file
        output_file += '.yaml'

    r = save_yaml(output_file, meta)
    if r['return'] > 0:
        return r

    return {'return': 0}

##########################################################################


def yaml2json(i):
    """
    Convert YAML file to JSON

    Args:

       input (str): input file (.yaml)
       (output) (str): output file (.json)

    Returns:
       (CM return dict):

       * return (int): return code == 0 if no error and >0 if error
       * (error) (str): error string if return>0
    """

    input_file = i.get('input', '')

    if input_file == '':
        return {'return': 1, 'error': 'please specify --input={yaml file}'}

    output_file = i.get('output', '')

    r = load_yaml(input_file, check_if_exists=True)
    if r['return'] > 0:
        return r

    meta = r['meta']

    if output_file == '':
        output_file = input_file[:-
                                 5] if input_file.endswith('.yaml') else input_file
        output_file += '.json'

    r = save_json(output_file, meta)
    if r['return'] > 0:
        return r

    return {'return': 0}

##########################################################################


def sort_json(i):
    """
    Sort JSON file

    Args:

       input (str): input file (.json)
       (output) (str): output file

    Returns:
       (CM return dict):

       * return (int): return code == 0 if no error and >0 if error
       * (error) (str): error string if return>0
    """

    input_file = i.get('input', '')

    if input_file == '':
        return {'return': 1, 'error': 'please specify --input={json file}'}

    r = load_json(input_file, check_if_exists=True)
    if r['return'] > 0:
        return r

    meta = r['meta']

    output_file = i.get('output', '')

    if output_file == '':
        output_file = input_file

    r = save_json(output_file, meta, sort_keys=True)
    if r['return'] > 0:
        return r

    return {'return': 0}

##########################################################################


def dos2unix(i):
    """
    Convert DOS file to UNIX (remove \r)

    Args:

       input (str): input file (.txt)
       (output) (str): output file

    Returns:
       (CM return dict):

       * return (int): return code == 0 if no error and >0 if error
       * (error) (str): error string if return>0
    """

    input_file = i.get('input', '')

    if input_file == '':
        return {'return': 1, 'error': 'please specify --input={txt file}'}

    r = load_txt(input_file, check_if_exists=True)
    if r['return'] > 0:
        return r

    s = r['string'].replace('\r', '')

    output_file = i.get('output', '')

    if output_file == '':
        output_file = input_file

    r = save_txt(output_file, s)
    if r['return'] > 0:
        return r

    return {'return': 0}

##########################################################################


def replace_string_in_file(i):
    """
    Convert DOS file to UNIX (remove \r)

    Args:

       input (str): input file (.txt)
       (output) (str): output file
       string (str): string to replace
       replacement (str): replacement string

    Returns:
       (CM return dict):

       * return (int): return code == 0 if no error and >0 if error
       * (error) (str): error string if return>0

       (update) (bool): True if file was upated
    """

    input_file = i.get('input', '')
    if input_file == '':
        return {'return': 1, 'error': 'please specify --input={txt file}'}

    string = i.get('string', '')
    if string == '':
        return {'return': 1,
                'error': 'please specify --string={string to replace}'}

    replacement = i.get('replacement', '')
    if replacement == '':
        return {'return': 1,
                'error': 'please specify --replacement={string to replace}'}

    output_file = i.get('output', '')

    if output_file == '':
        output_file = input_file

    r = load_txt(input_file, check_if_exists=True)
    if r['return'] > 0:
        return r

    s = r['string'].replace('\r', '')

    s = s.replace(string, replacement)

    r = save_txt(output_file, s)
    if r['return'] > 0:
        return r

    return {'return': 0}

##########################################################################


def create_toc_from_md(i):
    """
    Convert DOS file to UNIX (remove \r)

    Args:

       input (str): input file (.md)
       (output) (str): output file (input+'.toc)

    Returns:
       (CM return dict):

       * return (int): return code == 0 if no error and >0 if error
       * (error) (str): error string if return>0
    """

    input_file = i.get('input', '')
    if input_file == '':
        return {'return': 1, 'error': 'please specify --input={txt file}'}

    output_file = i.get('output', '')

    if output_file == '':
        output_file = input_file + '.toc'

    r = load_txt(input_file, check_if_exists=True)
    if r['return'] > 0:
        return r

    lines = r['string'].split('\n')

    toc = []

    toc.append('<details>')
    toc.append('<summary>Click here to see the table of contents.</summary>')
    toc.append('')

    for line in lines:
        line = line.strip()

        if line.startswith('#'):
            j = line.find(' ')
            if j >= 0:
                title = line[j:].strip()

                x = title.lower().replace(' ', '-')

                for k in range(0, 2):
                    if x.startswith('*'):
                        x = x[1:]
                    if x.endswith('*'):
                        x = x[:-1]

                for z in [':', '+', '.', '(', ')', ',']:
                    x = x.replace(z, '')

                y = ' ' * (2 * (j - 1)) + '* [' + title + '](#' + x + ')'

                toc.append(y)

    toc.append('')
    toc.append('</details>')

    r = save_txt(output_file, '\n'.join(toc) + '\n')
    if r['return'] > 0:
        return r

    return {'return': 0}

##########################################################################


def copy_to_clipboard(i):
    """
    Copy string to a clipboard

    Args:

       string (str): string to copy to a clipboard
       (add_quotes) (bool): add quotes to the string in a clipboard
       (skip_fail) (bool): if True, do not fail

    Returns:
       (CM return dict):

       * return (int): return code == 0 if no error and >0 if error
       * (error) (str): error string if return>0
    """

    s = i.get('string', '')

    if i.get('add_quotes', False):
        s = '"' + s + '"'

    failed = False
    warning = ''

    # Try to load pyperclip (seems to work fine on Windows)
    try:
        import pyperclip
    except Exception as e:
        warning = format(e)
        failed = True
        pass

    if not failed:
        pyperclip.copy(s)
    else:
        failed = False

        # Try to load Tkinter
        try:
            from Tkinter import Tk
        except ImportError as e:
            warning = format(e)
            failed = True
            pass

        if failed:
            failed = False
            try:
                from tkinter import Tk
            except ImportError as e:
                warning = format(e)
                failed = True
                pass

        if not failed:
            # Copy to clipboard
            try:
                r = Tk()
                r.withdraw()
                r.clipboard_clear()
                r.clipboard_append(s)
                r.update()
                r.destroy()
            except Exception as e:
                failed = True
                warning = format(e)

    rr = {'return': 0}

    if failed:
        if not i.get('skip_fail', False):
            return {'return': 1, 'error': warning}

        rr['warning'] = warning

    return rr

##########################################################################


def list_files_recursively(i):
    """
    List files and concatenate into string separate by comma

    Args:

    Returns:
       (CM return dict):

       * return (int): return code == 0 if no error and >0 if error
       * (error) (str): error string if return>0
    """

    files = os.walk('.')

    s = ''

    for (dir_path, dir_names, file_names) in files:
        for f in file_names:
            if s != '':
                s += ','

            if dir_path == '.':
                dir_path2 = ''
            else:
                dir_path2 = dir_path[2:].replace('\\', '/') + '/'

            s += dir_path2 + f

    print(s)

    return {'return': 0}

##########################################################################


def generate_secret(i):
    """
    Generate secret for web apps

    Args:

    Returns:
       (CM return dict):

       secret (str): secret

       * return (int): return code == 0 if no error and >0 if error
       * (error) (str): error string if return>0
    """

    import secrets
    s = secrets.token_urlsafe(16)

    print(s)

    return {'return': 0, 'secret': s}

##########################################################################


def detect_tags_in_artifact(i):
    """
    Detect if there are tags in an artifact name (spaces) and update input

    Args:

       input (dict) : original input

    Returns:
       (CM return dict):

       * return (int): return code == 0 if no error and >0 if error
       * (error) (str): error string if return>0
    """

    inp = i['input']

    artifact = inp.get('artifact', '')
    if artifact == '.':
        del (inp['artifact'])
    elif ' ' in artifact:  # or ',' in artifact:
        del (inp['artifact'])
        if 'parsed_artifact' in inp:
            del (inp['parsed_artifact'])
        # Force substitute tags
        inp['tags'] = artifact.replace(' ', ',')

    return {'return': 0}

##########################################################################


def prune_input(i):
    """
    Leave only input keys and remove the rest (to regenerate CM commands)

    Args:

       input (dict) : original input
       (extra_keys_starts_with) (list): remove keys that starts
                                        with the ones from this list

    Returns:
       (CM return dict):

       new_input (dict): pruned input

       * return (int): return code == 0 if no error and >0 if error
       * (error) (str): error string if return>0
    """

    import copy

    inp = i['input']
    extra_keys = i.get('extra_keys_starts_with', [])

    i_run_cmd_arc = copy.deepcopy(inp)
    for k in inp:
        remove = False
        if k in ['action', 'automation', 'cmd', 'out',
                 'parsed_automation', 'parsed_artifact', 'self_module']:
            remove = True
        if not remove:
            for ek in extra_keys:
                if k.startswith(ek):
                    remove = True
                    break

        if remove:
            del (i_run_cmd_arc[k])

    return {'return': 0, 'new_input': i_run_cmd_arc}

##########################################################################


def uid(i):
    """
    Generate CM UID.

    Args:
      (CM input dict): empty dict

    Returns:
      (CM return dict):

      * return (int): return code == 0 if no error and >0 if error
      * (error) (str): error string if return>0

      * uid (str): CM UID
    """

    console = i.get('out') == 'con'

    r = gen_uid()

    if console:
        print(r['uid'])

    return r

##########################################################################


def system(i):
    """
    Run system command and redirect output to string.

    Args:
      (CM input dict):

      * cmd (str): command line
      * (path) (str): go to this directory and return back to current
      * (stdout) (str): stdout file
      * (stderr) (str): stderr file

    Returns:
      (CM return dict):

      * return (int): return code == 0 if no error and >0 if error
      * (error) (str): error string if return>0

      * ret (int): return code
      * std (str): stdout + stderr
      * stdout (str): stdout
      * stderr (str): stderr
    """

    cmd = i['cmd']

    if cmd == '':
        return {'return': 1, 'error': 'cmd is empty'}

    path = i.get('path', '')
    if path != '' and os.path.isdir(path):
        cur_dir = os.getcwd()
        os.chdir(path)

    if i.get('stdout', '') != '':
        fn1 = i['stdout']
        fn1_delete = False
    else:
        r = gen_tmp_file({})
        if r['return'] > 0:
            return r
        fn1 = r['file_name']
        fn1_delete = True

    if i.get('stderr', '') != '':
        fn2 = i['stderr']
        fn2_delete = False
    else:
        r = gen_tmp_file({})
        if r['return'] > 0:
            return r
        fn2 = r['file_name']
        fn2_delete = True

    cmd += ' > ' + fn1 + ' 2> ' + fn2
    rx = os.system(cmd)

    std = ''
    stdout = ''
    stderr = ''

    if os.path.isfile(fn1):
        r = load_txt(file_name=fn1, remove_after_read=fn1_delete)
        if r['return'] == 0:
            stdout = r['string'].strip()

    if os.path.isfile(fn2):
        r = load_txt(file_name=fn2, remove_after_read=fn2_delete)
        if r['return'] == 0:
            stderr = r['string'].strip()

    std = stdout
    if stderr != '':
        if std != '':
            std += '\n'
        std += stderr

    if path != '' and os.path.isdir(path):
        os.chdir(cur_dir)

    return {'return': 0, 'ret': rx, 'stdout': stdout,
            'stderr': stderr, 'std': std}

############################################################


def load_cfg(i):
    """
    Load configuration artifacts and files

    Args:
      (CM input dict):


    Returns:
      (CM return dict):

      * return (int): return code == 0 if no error and >0 if error
      * (error) (str): error string if return>0

    """

    return call_internal_module(
        self, __file__, 'module_cfg', 'load_cfg', i)

############################################################


def select_cfg(i):
    """
    Select cfg interactively

    Args:
      (CM input dict):
        tags (str): list of tags to find cfg
        alias (str): alias of a cfg file

    Returns:
      (CM return dict):

      * return (int): return code == 0 if no error and >0 if error
      * (error) (str): error string if return>0

    """

    i['self_module'] = self

    return call_internal_module(
        self, __file__, 'module_cfg', 'select_cfg', i)

############################################################


def print_yaml(i):
    """
    Print YAML file

    Args:
      (CM input dict):
        file (str): input file

    Returns:
      (CM return dict):

      * return (int): return code == 0 if no error and >0 if error
      * (error) (str): error string if return>0

    """

    filename = i.get('file', '')
    if filename == '':
        return {'return': 1, 'error': 'please specify --file={YAML file}'}

    r = load_yaml(filename, check_if_exists=True)
    if r['return'] > 0:
        return r

    meta = r['meta']

    import json
    print(json.dumps(meta, indent=2))

    return {'return': 0}

############################################################


def print_json(i):
    """
    Print YAML file

    Args:
      (CM input dict):
        file (str): input file

    Returns:
      (CM return dict):

      * return (int): return code == 0 if no error and >0 if error
      * (error) (str): error string if return>0

    """

    filename = i.get('file', '')
    if filename == '':
        return {'return': 1, 'error': 'please specify --file={JSON file}'}

    r = load_json(filename, check_if_exists=True)
    if r['return'] > 0:
        return r

    meta = r['meta']

    import json
    print(json.dumps(meta, indent=2))

    return {'return': 0}

def parse_expiration(user_input: str) -> float:
    """
    Parse user input like '10m', '2h', '3d' into a UNIX timestamp.
    """
    units = {
        'm': 60,             # minutes
        'h': 3600,           # hours
        'd': 86400,          # days
    }

    if not user_input:
        raise ValueError("Expiration time cannot be empty")

    unit = user_input[-1].lower()
    if unit not in units:
        raise ValueError(f"Unknown unit '{unit}', use m/h/d")

    try:
        value = int(user_input[:-1])
    except ValueError:
        raise ValueError(f"Invalid number in '{user_input}'")

    seconds = value * units[unit]
    return time.time() + seconds
