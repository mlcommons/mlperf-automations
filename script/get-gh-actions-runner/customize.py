from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    meta = i['meta']

    automation = i['automation']
    mlc = automation.action_runner

    quiet = (env.get('MLC_QUIET', False) == 'yes')

    cmd = env.get('MLC_GH_ACTIONS_RUNNER_COMMAND', '')
    if cmd == "config":
        run_cmd = f"cd {env['MLC_GH_ACTIONS_RUNNER_CODE_PATH']} && ./config.sh --url {env['MLC_GH_ACTIONS_RUNNER_URL']} --token {env['MLC_GH_ACTIONS_RUNNER_TOKEN']}"
    elif cmd == "remove":
        run_cmd = f"cd {env['MLC_GH_ACTIONS_RUNNER_CODE_PATH']} && ./config.sh remove --token {env['MLC_GH_ACTIONS_RUNNER_TOKEN']}"
    elif cmd == "install":
        run_cmd = f"cd {env['MLC_GH_ACTIONS_RUNNER_CODE_PATH']} && sudo ./svc.sh install"
    elif cmd == "uninstall":
        run_cmd = f"cd {env['MLC_GH_ACTIONS_RUNNER_CODE_PATH']} && sudo ./svc.sh uninstall"
        cache_rm_tags = "gh,runner,_install"
        r = mlc.access({'action': 'rm', 'automation': 'cache',
                        'tags': cache_rm_tags, 'f': True})
        print(r)
        if r['return'] != 0 and r['return'] != 16:  # ignore missing ones
            return r
    elif cmd == "start":
        run_cmd = f"cd {env['MLC_GH_ACTIONS_RUNNER_CODE_PATH']} && sudo ./svc.sh start"

    env['MLC_RUN_CMD'] = run_cmd

    return {'return': 0}


def postprocess(i):

    env = i['env']

    return {'return': 0}
