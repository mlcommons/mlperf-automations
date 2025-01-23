from mlc import utils
import os
import json


def preprocess(i):

    env = i['env']

    mlc_cache_dataset_path = env.get(
        'MLC_CUSTOM_CACHE_ENTRY_DATASET_MLCOMMONS_COGNATA_PATH', '').strip()

    res = utils.load_json(
        os.path.join(
            mlc_cache_dataset_path,
            'cfg.json'))
    cfg = res.get('meta', {})
    if cfg.get('imported', False):
        env['MLC_DATASET_MLCOMMONS_COGNATA_IMPORTED'] = 'yes'

    if env.get('MLC_ABTF_SCRATCH_PATH_DATASETS', '') != '':
        env['MLC_ABTF_SCRATCH_PATH_DATASET_COGNATA'] = os.path.join(
            env['MLC_ABTF_SCRATCH_PATH_DATASETS'], "cognata")
        env['MLC_ABTF_SCRATCH_PATH_DATASET_COGNATA_TMP'] = os.path.join(
            env['MLC_ABTF_SCRATCH_PATH_DATASETS'], "cognata_tmp")

    env['MLC_DATASET_COGNATA_POC_TEXT_MD5_FILE_PATH'] = os.path.join(
        i['run_script_input']['path'], 'checksums', 'cognata_poc.txt')

    # Check if user requests path not in CM cache
    #
    # --path (env MLC_TMP_PATH) shows where to store Cognata data set instead of CM cahe
    # --import tells CM to import existing Cognata from a given path and skip further download/processing
    #
    import_path = env.get(
        'MLC_DATASET_MLCOMMONS_COGNATA_IMPORT_PATH',
        '').strip()
    if import_path != '':
        if not os.path.isdir(import_path):
            return {'return': 1, 'error': 'directory to import this dataset doesn\'t exist: {}'.format(
                import_path)}

        env['MLC_DATASET_MLCOMMONS_COGNATA_IMPORTED'] = 'yes'
        env['MLC_DATASET_MLCOMMONS_COGNATA_PATH'] = import_path

    else:
        path = env.get('MLC_TMP_PATH', '')
        if path != '':
            env['MLC_DATASET_MLCOMMONS_COGNATA_IMPORTED'] = 'no'

            if not os.path.isdir(path):
                os.makedirs(path)

            env['MLC_DATASET_MLCOMMONS_COGNATA_PATH'] = path

    return {'return': 0}


def postprocess(i):

    env = i['env']

    automation = i['automation']
    mlc = automation.action_object

    cur_dir = os.getcwd()

    quiet = (env.get('MLC_QUIET', False) == 'yes')

    mlc_cache_dataset_path = env.get(
        'MLC_CUSTOM_CACHE_ENTRY_DATASET_MLCOMMONS_COGNATA_PATH', '').strip()

    if not os.path.isdir(mlc_cache_dataset_path):
        return {
            'return': 1, 'error': 'Dataset corrupted - CM cache path not found: {}'.format(mlc_cache_dataset_path)}

    if env.get('MLC_DATASET_MLCOMMONS_COGNATA_FILE_NAMES', '') == '':
        env['MLC_DATASET_MLCOMMONS_COGNATA_PATH'] = os.path.dirname(
            env['MLC_CUSTOM_CACHE_ENTRY_DATASET_MLCOMMONS_COGNATA_PATH'])
        env['MLC_GET_DEPENDENT_CACHED_PATH'] = env['MLC_DATASET_MLCOMMONS_COGNATA_PATH']
        return {'return': 0}

    mlc_cache_dataset_cfg_file = os.path.join(mlc_cache_dataset_path, 'cfg.json')
    env['MLC_DATASET_MLCOMMONS_COGNATA_CFG_FILE'] = mlc_cache_dataset_cfg_file

    res = utils.load_json(mlc_cache_dataset_cfg_file)
    cfg = res.get('meta', {})

    dataset_path = cfg.get('real_path', '')
    dataset_path_requested = env.get('MLC_DATASET_MLCOMMONS_COGNATA_PATH', '')
    if dataset_path == '':
        if dataset_path_requested != '':
            dataset_path = dataset_path_requested
        else:
            dataset_path = os.path.join(mlc_cache_dataset_path, 'cognata')
    else:
        if dataset_path_requested != '':
            dataset_path = dataset_path_requested

    cfg['real_path'] = dataset_path

    print('')
    print('Used dataset path: {}'.format(dataset_path))

    env['MLC_DATASET_MLCOMMONS_COGNATA_PATH'] = dataset_path

    # If imported, don't process further
    if env.get('MLC_DATASET_MLCOMMONS_COGNATA_IMPORTED', '') == 'yes':
        cfg['imported'] = True
    else:
        cfg['imported'] = False

    utils.save_json(mlc_cache_dataset_cfg_file, cfg)

    if cfg.get('imported', False):
        return {'return': 0}

    # If processed once, don't process unless forced
    if cfg.get('processed', False):
        if not utils.check_if_true_yes_on(
                env, 'MLC_DATASET_MLCOMMONS_COGNATA_UPDATE'):
            print('')
            print('Already processed: use --update to update this dataset')

            return {'return': 0}

    # First level dir
    dataset_path1 = dataset_path

    if not os.path.isdir(dataset_path1):
        os.makedirs(dataset_path1)

    # Check if has license and download URL
    dataset_path_secret = os.path.join(dataset_path1, 'secret.json')

    first_url = ''
    dataset_meta = {}

    if os.path.isfile(dataset_path_secret):
        r = utils.load_json(dataset_path_secret)
        if r['return'] > 0:
            return r

        dataset_meta = r['meta']

        first_url = dataset_meta.get('first_url', '').strip()

    if first_url == '':
        x = env.get('MLC_DATASET_MLCOMMONS_COGNATA_PRIVATE_URL', '').strip()
        if x != '':
            first_url = x
        else:
            print('')
            first_url = input(
                'Please register at https://mlcommons.org/datasets/cognata and enter private URL: ')

            first_url = first_url.strip()

        if first_url == '':
            return {'return': 1,
                    'error': 'Private MLCommons Cognata URL was not provided'}

        dataset_meta['first_url'] = first_url

        with open(dataset_path_secret, 'w') as f:
            f.write(json.dumps(dataset_meta, indent=2) + '\n')

    ##########################################################################
    # Check if first.xlsx exists
    file_first_xlsx = 'first.xlsx'
    first_xlsx = os.path.join(dataset_path1, file_first_xlsx)

    if not os.path.isfile(first_xlsx):
        # Attempting to download file
        first_url_export, dummy = google_url_for_export(first_url)

        if first_url_export == '':
            return {
                'return': 1, 'error': 'can\'t parse URL for export: {}'.format(first_url)}

        r = mlc.access({'action': 'run',
                       'automation': 'script',
                        'tags': 'download,file,_wget',
                        'verify': 'no',
                        'url': first_url_export,
                        'output_file': file_first_xlsx,
                        'store': dataset_path1})
        if r['return'] > 0:
            return r

    if not os.path.isfile(first_xlsx):
        return {'return': 1,
                'error': 'File {} was not downloaded'.format(first_xlsx)}

    ##########################################################################
    # Parse XLSX and check serial number
    serial_numbers = []
    for s in env.get(
            'MLC_DATASET_MLCOMMONS_COGNATA_SERIAL_NUMBERS', '').strip().split(','):
        s = s.strip()
        if s != '' and s not in serial_numbers:
            serial_numbers.append(s)

    dataset_key = env['MLC_DATASET_MLCOMMONS_COGNATA_KEY1']
    url_key = 'Link to Excel File (Download Links)'
    serial_key = 'Serial Number'

    r = process_xlsx(
        first_xlsx,
        dataset_key,
        url_key,
        serial_key,
        serial_numbers)
    if r['return'] > 0:
        return r

    headers = r['headers']
    data = r['data']
    all_data = r['all_data']

    if len(all_data) != 0:
        file_first_json = 'first.json'
        first_json = os.path.join(dataset_path1, file_first_json)

        if not os.path.isfile(first_json):
            with open(first_json, 'w') as f:
                f.write(json.dumps(all_data, indent=2) + '\n')

    if len(data) == 0:
        return {'return': 0, 'error': 'no sets found'}

    ##########################################################################
    print('')
    print('Available or selected serial numbers (use --serial_numbers=a,b,c to download specific subsets):')
    print('')
    for d in data:
        s = d[serial_key]
        print(s)

    for d in data:
        url = d[url_key]
        url_export, dummy = google_url_for_export(url)

        serial_file = d[serial_key] + '.xlsx'

        dataset_path2 = os.path.join(dataset_path1, serial_file)
        dataset_path3 = os.path.join(dataset_path1, d[serial_key])

        if not os.path.isdir(dataset_path3):
            os.makedirs(dataset_path3)

        if not os.path.isfile(dataset_path2):

            print('')
            print('Downloading {} ...'.format(url_export))

            r = mlc.access({'action': 'run',
                           'automation': 'script',
                            'tags': 'download,file,_wget',
                            'verify': 'no',
                            'url': url_export,
                            'output_file': serial_file,
                            'store': dataset_path1})
            if r['return'] > 0:
                return r

    ##########################################################################
    print('')
    print('Processing subsets ...')

    group_names = []
    for s in env.get('MLC_DATASET_MLCOMMONS_COGNATA_GROUP_NAMES',
                     '').strip().split(','):
        s = s.strip()
        if s != '' and s not in group_names:
            group_names.append(s)

    # Check if force some filenames
    x = env.get('MLC_DATASET_MLCOMMONS_COGNATA_FILE_NAMES', '').strip()
    file_names = []
    if x != '':
        file_names = x.strip(';') if ';' in x else [x]

    for d in data:
        serial_file = d[serial_key] + '.xlsx'

        dataset_path2 = os.path.join(dataset_path1, serial_file)
        dataset_path3 = os.path.join(dataset_path1, d[serial_key])

        print('')
        print('Processing {} ...'.format(serial_file))

        dataset_key = 'File_Data'
        url_key = 'File_Link'
        serial_key = 'Group_Name'

        r = process_xlsx(
            dataset_path2,
            dataset_key,
            url_key,
            serial_key,
            group_names)
        if r['return'] > 0:
            return r

        headers = r['headers']
        data = r['data']
        all_data = r['all_data']

        if len(all_data) != 0:
            file_all_json = 'all.json'
            all_json = os.path.join(dataset_path3, file_all_json)

            if not os.path.isfile(all_json):
                with open(all_json, 'w') as f:
                    f.write(json.dumps(all_data, indent=2) + '\n')

        if len(data) == 0:
            return {'return': 0, 'error': 'no sub-sets found'}

        for d in data:
            file_name = d['File_Name']

            if len(file_names) > 0 and file_name not in file_names:
                continue

            file_name_with_path = os.path.join(dataset_path3, file_name)
            file_name_with_path_done = os.path.join(
                dataset_path3, file_name) + '.done'

            url = d[url_key]

            print('')
            print('Downloading {} ...'.format(file_name))

            if os.path.isfile(file_name_with_path_done):
                print('')
                print('  Already processed - skipping ...')
                continue

            if os.name == 'nt':
                aria2_tool = env['MLC_ARIA2_BIN_WITH_PATH']
            else:
                aria2_tool = 'aria2c'

            cmd = aria2_tool + \
                ' --async-dns=false -x15 -s15 "{}" --dir "{}" -o "{}"'.format(
                    url, dataset_path3, file_name)

            print('')
            print(cmd)
            print('')

            os.system(cmd)

            # Unarchive
            print('')
            print('Extracting file {} ...'.format(file_name_with_path))
            print('')

            if file_name.endswith('.zip'):

                import zipfile
                extractor = zipfile.ZipFile(file_name_with_path, "r")

            elif file_name.endswith('.tar'):

                import tarfile
                extractor = tarfile.ZipFile(file_name_with_path, "r")

            else:
                extractor = None

            if extractor is not None:

                try:
                    extractor.extractall(dataset_path3)
                    extractor.close()

                except Exception as e:
                    return {'return': 1,
                            'error': 'extracting failed: {}'.format(e)}

            # Mark as downloaded
            with open(file_name_with_path_done, 'w') as f:
                f.write('DONE\n')

            # Remove file
            os.remove(file_name_with_path)

    print('')

    # Mark that processed this dataset once correctly
    cfg['processed'] = True
    utils.save_json(mlc_cache_dataset_cfg_file, cfg)

    env['MLC_GET_DEPENDENT_CACHED_PATH'] = env['MLC_DATASET_MLCOMMONS_COGNATA_PATH']

    return {'return': 0}


# Prepare Google URL for export
def google_url_for_export(url):
    url2 = ''

    j = url.rfind('/')

    if j > 0:
        url = url[:j + 1]
        url2 = url + 'export'

    return (url2, url)

# Download Cognata XLSX


def process_xlsx(filename, dataset_key, url_key, serial_key, serial_numbers):
    import openpyxl

    ex = openpyxl.load_workbook(filename)

    sets = ex[dataset_key]

    headers = {}

    data = []
    all_data = []

    for row in sets.iter_rows(values_only=True):
        lrow = list(row)

        if len(headers) == 0:
            for j in range(0, len(lrow)):
                headers[j] = str(lrow[j]).strip()
        else:
            xrow = {}

            for j in range(0, len(lrow)):
                xrow[headers[j]] = lrow[j]

            url = str(xrow.get(url_key, ''))
            if 'https' in url:
                all_data.append(xrow)

                if len(serial_numbers) > 0:
                    serial_number = xrow.get(serial_key, '')

                    if serial_number not in serial_numbers:
                        continue

                if url != '':
                    data.append(xrow)

    return {'return': 0, 'headers': headers,
            'data': data, 'all_data': all_data}
