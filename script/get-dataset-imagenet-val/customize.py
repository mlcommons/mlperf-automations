from mlc import utils
from utils import is_true
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']
    automation = i['automation']
    meta = i['meta']
    os_info = i['os_info']

    env['MLC_DATASET_IMAGENET_VAL_REQUIRE_DAE'] = 'no'

    full = is_true(env.get('MLC_IMAGENET_FULL', '').strip())

    path = env.get(
        'MLC_INPUT',
        env.get(
            'IMAGENET_PATH',
            env.get(
                'MLC_DATASET_IMAGENET_PATH',
                ''))).strip()

    if path == '':
        if full:

            if env.get('MLC_DATASET_IMAGENET_VAL_TORRENT_PATH'):
                path = env['MLC_DATASET_IMAGENET_VAL_TORRENT_PATH']
                env['MLC_DAE_EXTRA_TAGS'] = "_torrent"
                env['MLC_DAE_TORRENT_PATH'] = path
                env['MLC_DATASET_IMAGENET_VAL_REQUIRE_DAE'] = 'yes'
                return {'return': 0}

            else:
                env['MLC_DAE_URL'] = 'https://image-net.org/data/ILSVRC/2012/ILSVRC2012_img_val.tar'
                env['MLC_DAE_FILENAME'] = 'ILSVRC2012_img_val.tar'
                env['MLC_DATASET_IMAGENET_VAL_REQUIRE_DAE'] = 'yes'

                return {'return': 0}
                # return {'return':1, 'error':'Please rerun the last MLC command
                # with --env.IMAGENET_PATH={path the folder containing full
                # ImageNet images} or envoke mlcr "get val dataset
                # imagenet" --input={path to the folder containing ImageNet
                # images}'}

        else:
            env['MLC_DATASET_IMAGENET_VAL_REQUIRE_DAE'] = 'yes'

    elif not os.path.isdir(path):
        if path.endswith(".tar"):
            env['MLC_EXTRACT_FILEPATH'] = path
            env['MLC_DAE_ONLY_EXTRACT'] = 'yes'
            return {'return': 0}
        else:
            return {'return': 1,
                    'error': 'Path {} doesn\'t exist'.format(path)}
    else:
        env['MLC_EXTRACT_EXTRACTED_PATH'] = path

    return {'return': 0}


def postprocess(i):

    os_info = i['os_info']

    env = i['env']
    path = env['MLC_EXTRACT_EXTRACTED_PATH']
    path1 = os.path.join(path, 'imagenet-2012-val')
    if os.path.isdir(path1):
        path = path1

    path_image = os.path.join(path, 'ILSVRC2012_val_00000001.JPEG')

    if not os.path.isfile(path_image):
        return {'return': 1,
                'error': 'ImageNet file {} not found'.format(path_image)}

    files = os.listdir(path)
    if len(files) < int(env.get('MLC_DATASET_SIZE', 0)):
        return {'return': 1, 'error': 'Only {} files found in {}. {} expected'.format(
            len(files), path, env.get('MLC_DATASET_SIZE'))}

    env['MLC_DATASET_PATH'] = path
    env['MLC_DATASET_IMAGENET_PATH'] = path
    env['MLC_DATASET_IMAGENET_VAL_PATH'] = path

    env['MLC_GET_DEPENDENT_CACHED_PATH'] = path

    return {'return': 0}
