from mlc import utils
from automation.utils import is_true, is_false
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    automation = i['automation']
    cm = automation.action_object

    if env.get('MLC_HOST_OS_FLAVOR', '') == 'amzn':
        env['MLC_PACKAGE_TOOL'] = "yum"
        i['run_script_input']['script_name'] = "run-rhel"

    # Test (not needed - will be removed)
    if is_true(str(env.get('MLC_SKIP_SYS_UTILS', ''))):
        return {'return': 0, 'skip': True}


# Windows has moved to get-sys-utils-min and will be always run with
# "detect,os"!

    if os_info['platform'] == 'windows':
        print('')
        print('This script is not used on Windows')
        print('')

   # If windows, download here otherwise use run.sh

#
#        path = os.getcwd()
#
#        clean_dirs = env.get('MLC_CLEAN_DIRS','').strip()
#        if clean_dirs!='':
#            import shutil
#            for cd in clean_dirs.split(','):
#                if cd != '':
#                    if os.path.isdir(cd):
#                        print ('Clearning directory {}'.format(cd))
#                        shutil.rmtree(cd)
#
#        url = env['MLC_PACKAGE_WIN_URL']
#
#        urls = [url] if ';' not in url else url.split(';')
#
#        print ('')
#        print ('Current directory: {}'.format(os.getcwd()))
#
#        for url in urls:
#
#            url = url.strip()
#
#            print ('')
#            print ('Downloading from {}'.format(url))
#
#            r = cm.access({'action':'download_file',
#                           'automation':'utils,dc2743f8450541e3',
#                           'url':url})
#            if r['return']>0: return r
#
#            filename = r['filename']
#
#            print ('Unzipping file {}'.format(filename))
#
#            r = cm.access({'action':'unzip_file',
#                           'automation':'utils,dc2743f8450541e3',
#                           'filename':filename})
#            if r['return']>0: return r
#
#            if os.path.isfile(filename):
#                print ('Removing file {}'.format(filename))
#                os.remove(filename)
#
#        print ('')
#
#        # Add to path
#        env['+PATH']=[os.path.join(path, 'bin')]
#
    else:
        print('')
        print('***********************************************************************')
        print('This script will attempt to install minimal system dependencies for CM.')
        print('Note that you may be asked for your SUDO password ...')
        print('***********************************************************************')

    return {'return': 0}
