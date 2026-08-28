import platform


def preprocess(i):
    env = i['env']
    env['MLC_DEMO_ARCH'] = platform.machine()
    return {'return': 0}


def postprocess(i):
    return {'return': 0}
