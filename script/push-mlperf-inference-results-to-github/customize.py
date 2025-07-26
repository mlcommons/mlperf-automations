from mlc import utils
import os
from giturlparse import parse


def preprocess(i):

    os_info = i['os_info']
    env = i['env']
    meta = i['meta']
    automation = i['automation']

    repo = env.get('MLC_MLPERF_RESULTS_GIT_REPO_URL', '')
    if repo.strip() == '':
        return {'return': 1, 'error': 'Invalid GIT_REPO_URL for MLPERF results'}

    branch = env.get('MLC_GIT_BRANCH', '')
    if branch:
        extra_tags_string = f",_branch.{branch}"
    else:
        extra_tags_string = ""

    r = automation.update_deps({'deps': meta['prehook_deps'],
                                'update_deps': {
        'get-git-repo': {
            'tags': "_repo." + repo + extra_tags_string
        }
    }
    })
    if r['return'] > 0:
        return r
    env['MLC_MLPERF_RESULTS_REPO_COMMIT_MESSAGE'] = env.get(
        'MLC_MLPERF_RESULTS_REPO_COMMIT_MESSAGE', 'Added new results')

    if env.get('MLC_GITHUB_PAT', '') != '':
        p = parse(repo)
        token = env['MLC_GITHUB_PAT']
        if token == 'pat':
            token = "$PAT"
        env['MLC_GIT_PUSH_CMD'] = f"""git push https://x-access-token:{token}@{p.host}/{p.owner}/{p.repo}"""
    else:
        env['MLC_GIT_PUSH_CMD'] = "git push"

    return {'return': 0}


def postprocess(i):

    os_info = i['os_info']
    env = i['env']
    meta = i['meta']
    automation = i['automation']

    env['MLC_MLPERF_RESULTS_SYNC_DIR'] = env['MLC_GIT_REPO_CHECKOUT_PATH']

    logger = automation.logger

    logger.log(
        f"\n\nPath to the locally synced submission directory: {env['MLC_MLPERF_RESULTS_SYNC_DIR']}\n\n")

    return {'return': 0}
