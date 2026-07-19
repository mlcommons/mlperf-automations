import os


def postprocess(i):

    env = i['env']

    env['MLC_SQLITE_PATH'] = os.getcwd()

    return {'return': 0}
