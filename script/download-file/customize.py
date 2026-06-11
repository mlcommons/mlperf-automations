from mlc import utils
import os
import subprocess
from utils import *


def escape_special_chars(text, tool=None):
    special_chars = [
        '&', '|', '(', ')'
    ]

    for char in special_chars:
        text = text.replace(char, f'^{char}')

    # handle URL special cases
    if tool != "rclone":
        text = text.replace('%', "%%")

    return text


def get_filename_from_content_disposition(url, verify_ssl, logger=None):
    """Browser-like filename resolution.

    Performs a lightweight HTTP request and inspects the server's
    ``Content-Disposition`` header (honouring the RFC 5987 ``filename*`` form)
    to determine the name a browser would save the file as. Falls back to the
    basename of the final (post-redirect) URL path. Returns the resolved
    filename or ``None`` when it cannot be determined. Best-effort: any error
    results in ``None`` so the caller can fall back to URL-based naming.
    """
    try:
        import re
        import ssl
        import urllib.request
        from urllib.parse import unquote, urlsplit

        ctx = None
        if not verify_ssl:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

        # Use GET (many servers reject HEAD); urllib only reads the body
        # lazily, so closing the response avoids downloading the payload.
        req = urllib.request.Request(
            url, headers={'User-Agent': 'Mozilla/5.0'}, method='GET')
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            cd = resp.headers.get('Content-Disposition', '') or ''
            final_url = resp.geturl()

        if cd:
            # Prefer RFC 5987: filename*=UTF-8''<percent-encoded>
            m = re.search(
                r"filename\*\s*=\s*[^']*''([^;\r\n]+)", cd, re.IGNORECASE)
            if m:
                name = os.path.basename(
                    unquote(m.group(1).strip().strip('"')))
                if name:
                    return name
            # Then the plain filename= form (quoted or bare).
            m = re.search(r'filename\s*=\s*"([^"]+)"', cd, re.IGNORECASE)
            if not m:
                m = re.search(
                    r'filename\s*=\s*([^;\r\n]+)', cd, re.IGNORECASE)
            if m:
                name = os.path.basename(m.group(1).strip().strip('"'))
                if name:
                    return name

        # Fall back to the basename of the final (possibly redirected) URL.
        if final_url:
            tail = os.path.basename(urlsplit(final_url).path)
            if "." in tail:
                return tail
    except Exception as e:
        if logger is not None:
            logger.warning(
                f"Could not resolve filename from headers for {url}: {e}")
    return None


def preprocess(i):

    os_info = i['os_info']
    env = i['env']

    # env to be passed to the  subprocess
    subprocess_env = os.environ.copy()
    subprocess_env['PATH'] += os.pathsep + \
        os.pathsep.join(env.get('+PATH', ''))

    meta = i['meta']

    automation = i['automation']

    logger = automation.logger

    quiet = is_true(env.get('MLC_QUIET', False))

    tool = env.get('MLC_DOWNLOAD_TOOL', '')
    pre_clean = env.get('MLC_PRE_DOWNLOAD_CLEAN', False)

    #    xsep = '^&^&' if windows else '&&'
    xsep = '&&'

    q = '"' if os_info['platform'] == 'windows' else "'"

    x = '*' if os_info['platform'] == 'windows' else ''
    x_c = '-s' if os_info['platform'] == 'darwin_off' else ''

    # command for deleting file in windows and linux is different
    if os_info['platform'] == 'windows':
        del_cmd = "del /f"
    else:
        del_cmd = "rm -f"

    if env.get('MLC_DOWNLOAD_LOCAL_FILE_PATH'):
        filepath = env['MLC_DOWNLOAD_LOCAL_FILE_PATH']

        if not os.path.exists(filepath):
            return {'return': 1,
                    'error': 'Local file {} doesn\'t exist'.format(filepath)}

        env['MLC_DOWNLOAD_CMD'] = ""

        env['MLC_DOWNLOAD_FILENAME'] = filepath

        if not quiet:
            logger.info('')
            logger.info('Using local file: {}'.format(filepath))
    else:
        url = env.get('MLC_DOWNLOAD_URL', '')

        if url == '':
            return {
                'return': 1, 'error': 'please specify URL using --url={URL} or --env.MLC_DOWNLOAD_URL={URL}'}

        logger.info('')
        logger.info('Downloading from {}'.format(url))

        if '&' in url and tool != "mlcutil":
            if os_info['platform'] == 'windows':
                url = '"' + url + '"'
            else:
                url = url.replace('&', '\\&')

        extra_download_options = env.get('MLC_DOWNLOAD_EXTRA_OPTIONS', '')

        verify_ssl = is_true(env.get('MLC_VERIFY_SSL', "True"))
        if not verify_ssl or os_info['platform'] == 'windows':
            verify_ssl = False
        else:
            verify_ssl = True

        # Support custom CA file via MLC_SSL_CA_FILE
        ca_file = env.get('MLC_SSL_CA_FILE', '')
        if ca_file and os.path.isfile(ca_file):
            ssl_ca_file = ca_file
        else:
            ssl_ca_file = ''

        if env.get('MLC_DOWNLOAD_PATH', '') != '':
            download_path = env['MLC_DOWNLOAD_PATH']
            if os.path.isfile(download_path):
                download_path = os.path.dirname(download_path)
            if not os.path.exists(download_path):
                os.makedirs(download_path, exist_ok=True)
            os.chdir(download_path)

        if env.get('MLC_DOWNLOAD_FILENAME', '') == '':
            download_url = env['MLC_DOWNLOAD_URL']
            resolved_name = ''
            # Browser-like behaviour: ask the server what the file should be
            # named (Content-Disposition) before deriving it from the URL.
            if download_url.lower().startswith(('http://', 'https://')):
                resolved_name = get_filename_from_content_disposition(
                    download_url, verify_ssl, logger) or ''
            if resolved_name != '':
                env['MLC_DOWNLOAD_FILENAME'] = resolved_name
            else:
                # Fallback: derive the filename from the URL path (basename).
                urltail = os.path.basename(download_url)
                urlhead = os.path.dirname(download_url)
                if "." in urltail and "/" in urlhead:
                    # Check if ? after filename
                    j = urltail.find('?')
                    if j > 0:
                        urltail = urltail[:j]
                    env['MLC_DOWNLOAD_FILENAME'] = urltail
                elif env.get('MLC_DOWNLOAD_TOOL', '') == "rclone":
                    env['MLC_DOWNLOAD_FILENAME'] = urltail
                else:
                    env['MLC_DOWNLOAD_FILENAME'] = "index.html"

        if tool == "mlcutil":
            mlcutil_require_download = 0
            if env.get('MLC_DOWNLOAD_CHECKSUM_FILE', '') != '':
                if os_info['platform'] == 'windows':
                    checksum_cmd = f"cd {q}{filepath}{q} {xsep}  md5sum -c{x_c} {x}{escape_special_chars(env['MLC_DOWNLOAD_CHECKSUM_FILE'])}"
                else:
                    checksum_cmd = f"cd {q}{filepath}{q} {xsep}  md5sum -c{x_c} {x}{q}{env['MLC_DOWNLOAD_CHECKSUM_FILE']}{q}"
                checksum_result = subprocess.run(
                    checksum_cmd,
                    cwd=f'{q}{filepath}{q}',
                    capture_output=True,
                    text=True,
                    shell=True,
                    env=subprocess_env)
            elif env.get('MLC_DOWNLOAD_CHECKSUM', '') != '' and os.path.isfile(env['MLC_DOWNLOAD_FILENAME']):
                if os_info['platform'] == 'windows':
                    checksum_cmd = f"echo {env.get('MLC_DOWNLOAD_CHECKSUM')} {x}{escape_special_chars(env['MLC_DOWNLOAD_FILENAME'])} | md5sum -c{x_c} -"
                else:
                    checksum_cmd = f"echo {env.get('MLC_DOWNLOAD_CHECKSUM')} {x}{q}{env['MLC_DOWNLOAD_FILENAME']}{q} | md5sum -c{x_c} -"
                checksum_result = subprocess.run(
                    checksum_cmd,
                    capture_output=True,
                    text=True,
                    shell=True,
                    env=subprocess_env)
            if (env.get('MLC_DOWNLOAD_CHECKSUM_FILE', '') != '' or env.get(
                    'MLC_DOWNLOAD_CHECKSUM', '') != '') and os.path.exists(env['MLC_DOWNLOAD_FILENAME']):
                # print(checksum_result) #for debugging
                if "checksum did not match" in checksum_result.stderr.lower():
                    computed_checksum = subprocess.run(
                        f"md5sum {env['MLC_DOWNLOAD_FILENAME']}",
                        capture_output=True,
                        text=True,
                        shell=True).stdout.split(" ")[0]
                    print(
                        f"WARNING: File already present, mismatch between original checksum({env.get('MLC_DOWNLOAD_CHECKSUM')}) and computed checksum({computed_checksum}). Deleting the already present file and downloading new.")
                    try:
                        os.remove(env['MLC_DOWNLOAD_FILENAME'])
                        print(
                            f"File {env['MLC_DOWNLOAD_FILENAME']} deleted successfully.")
                    except PermissionError:
                        return {
                            "return": 1, "error": f"Permission denied to delete file {env['MLC_DOWNLOAD_FILENAME']}."}
                    mlcutil_require_download = 1
                elif "no such file" in checksum_result.stderr.lower():
                    # print(f"No file {env['MLC_DOWNLOAD_FILENAME']}. Downloading through mlcutil.")
                    mlcutil_require_download = 1
                elif checksum_result.returncode > 0:
                    return {
                        "return": 1, "error": f"Error while checking checksum: {checksum_result.stderr}"}
                else:
                    print(
                        f"File {env['MLC_DOWNLOAD_FILENAME']} already present, original checksum and computed checksum matches! Skipping Download..")
            else:
                mlcutil_require_download = 1

            if mlcutil_require_download == 1:
                retry_count = int(env.get('MLC_DOWNLOAD_RETRY_COUNT', '1'))
                download_success = False
                r = {'return': 1}  # Initialize with failure

                for retry_attempt in range(1, retry_count + 1):
                    if retry_attempt > 1:
                        logger.info(
                            f"Retry attempt {retry_attempt} of {retry_count}")

                    # Reset url to the original for each retry attempt
                    url = env.get('MLC_DOWNLOAD_URL', '')

                    for i in range(1, 5):
                        r = download_file({
                            'url': url,
                            'filename': env.get('MLC_DOWNLOAD_FILENAME', ''),
                            'verify': verify_ssl,
                            'ssl_ca_file': ssl_ca_file})
                        if r['return'] == 0:
                            download_success = True
                            break
                        oldurl = url
                        url = env.get('MLC_DOWNLOAD_URL' + str(i), '')
                        if url == '':
                            break
                        logger.error(
                            f"Download from {oldurl} failed, trying from {url}")

                    if download_success:
                        break
                    elif retry_attempt < retry_count:
                        logger.error(f"All URLs failed. Retrying...")

                if r['return'] > 0:
                    logger.error(
                        f"Download failed after {retry_count} attempt(s)")
                    return r

                env['MLC_DOWNLOAD_CMD'] = ""
                env['MLC_DOWNLOAD_FILENAME'] = r['filename']

        elif tool == "wget":
            if env.get('MLC_DOWNLOAD_FILENAME', '') != '':
                extra_download_options += f" --tries=3 -O {q}{env['MLC_DOWNLOAD_FILENAME']}{q} "
                if ssl_ca_file:
                    extra_download_options += f" --ca-certificate={q}{ssl_ca_file}{q} "
                elif not verify_ssl:
                    extra_download_options += " --no-check-certificate "
            env['MLC_DOWNLOAD_CMD'] = f"wget -nc {extra_download_options} {url}"
            for i in range(1, 5):
                url = env.get('MLC_DOWNLOAD_URL' + str(i), '')
                if url == '':
                    break
                env['MLC_DOWNLOAD_CMD'] += f" || (({del_cmd} {env['MLC_DOWNLOAD_FILENAME']} || true) && wget -nc {extra_download_options} {url})"
            logger.info(f"{env['MLC_DOWNLOAD_CMD']}")

        elif tool == "r2-downloader":
            if is_true(env.get('MLC_AUTH_USING_SERVICE_ACCOUNT')):
                extra_download_options += " -s "
            env['MLC_DOWNLOAD_CMD'] = f"bash <(curl -s https://raw.githubusercontent.com/mlcommons/r2-downloader/refs/heads/main/mlc-r2-downloader.sh) "
            if env["MLC_HOST_OS_TYPE"] == "windows":
                # have to modify the variable from url to temp_url if it is
                # going to be used anywhere after this point
                url = url.replace("%", "%%")
                temp_download_file = env['MLC_DOWNLOAD_FILENAME'].replace(
                    "%", "%%")
            else:
                temp_download_file = env['MLC_DOWNLOAD_FILENAME']
            env['MLC_DOWNLOAD_CMD'] += f" -d {q}{os.path.join(os.getcwd(), temp_download_file)}{q} {extra_download_options} {url}"

        elif tool == "curl":
            if ssl_ca_file:
                extra_download_options += f" --cacert {q}{ssl_ca_file}{q} "
            elif not verify_ssl:
                extra_download_options += " -k "
            if env.get('MLC_DOWNLOAD_FILENAME', '') != '':
                extra_download_options += f" --output {q}{env['MLC_DOWNLOAD_FILENAME']}{q} "

            env['MLC_DOWNLOAD_CMD'] = f"curl {extra_download_options} {url}"
            for i in range(1, 5):
                url = env.get('MLC_DOWNLOAD_URL' + str(i), '')
                if url == '':
                    break
                env['MLC_DOWNLOAD_CMD'] += f" || (({del_cmd} {env['MLC_DOWNLOAD_FILENAME']} || true) && curl {extra_download_options} {url})"

        elif tool == "gdown":
            if not verify_ssl:
                extra_download_options += " --no-check-certificate "
            env['MLC_DOWNLOAD_CMD'] = f"gdown {extra_download_options} {url}"
            for i in range(1, 5):
                url = env.get('MLC_DOWNLOAD_URL' + str(i), '')
                if url == '':
                    break
                env['MLC_DOWNLOAD_CMD'] += f" || (({del_cmd} {env['MLC_DOWNLOAD_FILENAME']} || true) && gdown {extra_download_options} {url})"

        elif tool == "rclone":
            # keeping this for backward compatibility. Ideally should be done
            # via get,rclone-config script
            if env.get('MLC_RCLONE_CONFIG_CMD', '') != '':
                env['MLC_DOWNLOAD_CONFIG_CMD'] = env['MLC_RCLONE_CONFIG_CMD']
            if is_true(env.get('MLC_RCLONE_SKIP_BUCKET_CHECK')):
                extra_download_options += " --s3-no-check-bucket "
            rclone_copy_using = env.get('MLC_RCLONE_COPY_USING', 'sync')
            if rclone_copy_using == "sync":
                pre_clean = False
            if not verify_ssl:
                extra_download_options += " --no-check-certificate "
            # rlone fix : check rclone version to add --multi-thread-streams=0
            tmp_rclone_version = env.get('MLC_RCLONE_VERSION', '')
            if tmp_rclone_version == '':
                logger.warning(
                    "MLC_RCLONE_VERSION not set, was get-rclone called as dependency?"
                )
            else:
                ref_version = list(map(int, "1.60.0".split('.')))
                rclone_version = list(map(int, tmp_rclone_version.split('.')))
                if rclone_version >= ref_version:
                    extra_download_options += " --multi-thread-streams=0 "
            if env["MLC_HOST_OS_TYPE"] == "windows":
                # have to modify the variable from url to temp_url if it is
                # going to be used anywhere after this point
                url = url.replace("%", "%%")
                temp_download_file = env['MLC_DOWNLOAD_FILENAME'].replace(
                    "%", "%%")
                env['MLC_DOWNLOAD_CMD'] = f"rclone {rclone_copy_using} {q}{url}{q} {q}{os.path.join(os.getcwd(), temp_download_file)}{q} -P --error-on-no-transfer {extra_download_options}"
            else:
                env['MLC_DOWNLOAD_CMD'] = f"rclone {rclone_copy_using} {q}{url}{q} {q}{os.path.join(os.getcwd(), env['MLC_DOWNLOAD_FILENAME'])}{q} -P --error-on-no-transfer {extra_download_options}"

        filename = env['MLC_DOWNLOAD_FILENAME']
        env['MLC_DOWNLOAD_DOWNLOADED_FILENAME'] = filename

        filename = os.path.basename(env['MLC_DOWNLOAD_FILENAME'])
        filepath = os.path.join(os.getcwd(), filename)

    env['MLC_DOWNLOAD_DOWNLOADED_PATH'] = filepath

    # verify checksum if file already present
    if env.get('MLC_DOWNLOAD_CHECKSUM_FILE', '') != '':
        env['MLC_DOWNLOAD_CHECKSUM_CMD'] = f"cd {q}{filepath}{q} {xsep}  md5sum -c {x_c} {x}{q}{env['MLC_DOWNLOAD_CHECKSUM_FILE']}{q}"
    elif env.get('MLC_DOWNLOAD_CHECKSUM', '') != '':
        if os_info['platform'] == 'windows':
            env['MLC_DOWNLOAD_CHECKSUM_CMD'] = "echo {} {}{} | md5sum {} -c -".format(
                env.get('MLC_DOWNLOAD_CHECKSUM'), x, escape_special_chars(
                    env['MLC_DOWNLOAD_FILENAME']), x_c)
        else:
            env['MLC_DOWNLOAD_CHECKSUM_CMD'] = "echo {} {}{}{}{} | md5sum {} -c -".format(
                env.get('MLC_DOWNLOAD_CHECKSUM'), x, q, env['MLC_DOWNLOAD_FILENAME'], q, x_c)
        for i in range(1, 5):
            if env.get('MLC_DOWNLOAD_CHECKSUM' + str(i), '') == '':
                break
            if os_info['platform'] == 'windows':
                env['MLC_DOWNLOAD_CHECKSUM_CMD'] += " || echo {} {}{} | md5sum {} -c -".format(
                    env.get(
                        'MLC_DOWNLOAD_CHECKSUM' +
                        str(i)),
                    x,
                    escape_special_chars(
                        env['MLC_DOWNLOAD_FILENAME']),
                    x_c)
            else:
                env['MLC_DOWNLOAD_CHECKSUM_CMD'] += " || echo {} {}{}{}{} | md5sum {} -c -".format(
                    env.get(
                        'MLC_DOWNLOAD_CHECKSUM' +
                        str(i)),
                    x,
                    q,
                    env['MLC_DOWNLOAD_FILENAME'].replace(
                        "%",
                        "%%"),
                    q,
                    x_c)
        # print(env['MLC_DOWNLOAD_CHECKSUM_CMD'])
    else:
        env['MLC_DOWNLOAD_CHECKSUM_CMD'] = ""

    if not pre_clean:
        env['MLC_PRE_DOWNLOAD_CMD'] = ''

    if os_info['platform'] == 'windows' and env.get(
            'MLC_DOWNLOAD_CMD', '') != '':
        env['MLC_DOWNLOAD_CMD'] = escape_special_chars(
            env['MLC_DOWNLOAD_CMD'], tool)
        if pre_clean:
            env['MLC_PRE_DOWNLOAD_CLEAN_CMD'] = "del /Q %MLC_DOWNLOAD_FILENAME%"
        # Check that if empty CMD, should add ""
        for x in ['MLC_DOWNLOAD_CMD', 'MLC_DOWNLOAD_CHECKSUM_CMD']:
            env[x + '_USED'] = 'YES' if env.get(x, '') != '' else 'NO'
    else:
        env['MLC_PRE_DOWNLOAD_CLEAN_CMD'] = "rm -f {}".format(
            env['MLC_DOWNLOAD_FILENAME'])

    return {'return': 0}


def postprocess(i):

    automation = i['automation']

    env = i['env']

    if env.get('MLC_DOWNLOAD_MODE') == "dry":
        return {'return': 0}

    filepath = env['MLC_DOWNLOAD_DOWNLOADED_PATH']

    if not os.path.exists(filepath):
        return {
            'return': 1, 'error': 'Downloaded path {} does not exist. Probably MLC_DOWNLOAD_FILENAME is not set and MLC_DOWNLOAD_URL given is not pointing to a file'.format(filepath)}

    if env.get('MLC_DOWNLOAD_RENAME_FILE', '') != '':
        file_dir = os.path.dirname(filepath)
        new_file_name = env['MLC_DOWNLOAD_RENAME_FILE']
        new_file_path = os.path.join(file_dir, new_file_name)
        os.rename(filepath, new_file_path)
        filepath = new_file_path

    if env.get('MLC_DOWNLOAD_FINAL_ENV_NAME', '') != '':
        env[env['MLC_DOWNLOAD_FINAL_ENV_NAME']] = filepath

    env['MLC_GET_DEPENDENT_CACHED_PATH'] = filepath

    # Since may change directory, check if need to clean some temporal files
    automation.clean_some_tmp_files({'env': env})

    return {'return': 0}
