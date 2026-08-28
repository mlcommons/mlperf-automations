def preprocess(i):
    env = i['env']
    env['MLC_DEMO_HELLO_MESSAGE'] = 'Hello from the pip-installed mlc-scripts-content package!'
    env['MLC_DEMO_HOST_OS'] = env.get('MLC_HOST_OS_TYPE', 'unknown')
    return {'return': 0}


def postprocess(i):
    return {'return': 0}
