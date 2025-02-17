from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    if os_info['platform'] == "windows":
        return {'return': 1, 'error': 'Script not supported in windows yet!'}

    if env.get('MLC_DATASET_WAYMO_PATH', '') != '':
        if not os.path.exists(env['MLC_DATASET_WAYMO_PATH']):
            return {
                'return': 1, 'error': f"Path {env['MLC_DATASET_WAYMO_PATH']} does not exists!"}
    else:
        env['MLC_TMP_REQUIRE_DOWNLOAD'] = "yes"
        if env['MLC_DOWNLOAD_SRC'] == "mlcommons":
            i['run_script_input']['script_name'] = 'run-rclone'
            if env.get('MLC_OUTDIRNAME', '') != '':
                env['MLC_DATASET_WAYMO_PATH'] = env['MLC_OUTDIRNAME']
            else:
                env['MLC_DATASET_WAYMO_PATH'] = os.path.join(
                    os.getcwd(), "kitti_format")

    return {'return': 0}


def postprocess(i):

    env = i['env']

    return {'return': 0}
