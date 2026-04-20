import unittest
from types import SimpleNamespace
from unittest.mock import patch
import os
import sys
import types

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
AUTOMATION_ROOT = os.path.join(REPO_ROOT, 'automation')
if AUTOMATION_ROOT not in sys.path:
    sys.path.insert(0, AUTOMATION_ROOT)

if 'mlc' not in sys.modules:
    mlc_pkg = types.ModuleType('mlc')
    mlc_main = types.ModuleType('mlc.main')
    mlc_utils = types.ModuleType('mlc.utils')

    class _Automation:
        pass

    class _CacheAction:
        def __init__(self, *_args, **_kwargs):
            pass

    mlc_main.Automation = _Automation
    mlc_main.CacheAction = _CacheAction

    def _merge_dicts(_):
        return {'return': 0}

    def _compare_versions(_a, _b):
        return 0

    mlc_utils.merge_dicts = _merge_dicts
    mlc_utils.compare_versions = _compare_versions

    sys.modules['mlc'] = mlc_pkg
    sys.modules['mlc.main'] = mlc_main
    sys.modules['mlc.utils'] = mlc_utils

from script import module


class DummyLogger:
    def __init__(self):
        self.messages = []

    def warning(self, msg):
        self.messages.append(('warning', msg))

    def debug(self, msg):
        self.messages.append(('debug', msg))


def _cp(returncode=0, stdout='', stderr=''):
    return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)


class RepoUpdateHandlingTests(unittest.TestCase):
    def test_get_repo_update_status_detects_updates_and_script_change(self):
        # _run_git_command call sequence:
        # 1) rev-parse --is-inside-work-tree
        # 2) rev-parse --abbrev-ref --symbolic-full-name @{u}
        # 3) fetch --quiet
        # 4) rev-list --count HEAD..@{u}
        # 5) diff --name-only HEAD..@{u}
        # 6) diff --name-only HEAD..@{u} -- <script path>
        with patch.object(module, '_run_git_command', side_effect=[
            _cp(stdout='true\n'),
            _cp(stdout='origin/main\n'),
            _cp(),
            _cp(stdout='2\n'),
            _cp(stdout='automation/script/module.py\nREADME.md\n'),
            _cp(stdout='automation/script/module.py\n'),
        ]):
            status = module._get_repo_update_status('/tmp/repo', 'automation/script/module.py')

        self.assertTrue(status['update_available'])
        self.assertEqual(status['commits_behind'], 2)
        self.assertTrue(status['script_changed'])
        self.assertEqual(status['changed_files'], ['automation/script/module.py', 'README.md'])

    def test_get_repo_update_status_without_upstream(self):
        with patch.object(module, '_run_git_command', side_effect=[
            _cp(stdout='true\n'),
            _cp(returncode=1, stderr='fatal: no upstream configured\n'),
        ]):
            status = module._get_repo_update_status('/tmp/repo', '')

        self.assertFalse(status['update_available'])
        self.assertIn('No upstream branch configured', status.get('warning', ''))

    def test_auto_pull_repo_updates_quiet_mode_local_changes(self):
        logger = DummyLogger()
        with patch.object(module, '_run_git_command', side_effect=[
            _cp(stdout=' M file.txt\n')
        ]):
            result = module._auto_pull_repo_updates('/tmp/repo', True, logger, '')

        self.assertEqual(result['return'], 0)
        self.assertFalse(result['updated'])

    def test_check_and_handle_repo_updates_warns_and_continues_without_auto_pull(self):
        logger = DummyLogger()
        with patch.object(module, '_get_repo_update_status', return_value={
            'return': 0,
            'update_available': True,
            'commits_behind': 1,
            'changed_files': ['a.py'],
            'script_changed': False
        }):
            result = module.check_and_handle_repo_updates(
                repo_path='/tmp/repo',
                repo_alias='mlcommons@mlperf-automations',
                script_relative_path='automation/script/module.py',
                auto_pull_repo=False,
                quiet=False,
                recursion_spaces='',
                logger=logger)

        self.assertEqual(result['return'], 0)
        self.assertTrue(any('WARNING: Updates are available' in m[1] for m in logger.messages))


if __name__ == '__main__':
    unittest.main()
