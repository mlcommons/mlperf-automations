import os
import sys
import types
import unittest


REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", ".."))
AUTOMATION_ROOT = os.path.join(REPO_ROOT, "automation")

if AUTOMATION_ROOT not in sys.path:
    sys.path.insert(0, AUTOMATION_ROOT)


def _install_test_stubs():
    mlc_mod = types.ModuleType("mlc")
    mlc_utils_mod = types.ModuleType("mlc.utils")
    mlc_mod.utils = mlc_utils_mod
    sys.modules["mlc"] = mlc_mod
    sys.modules["mlc.utils"] = mlc_utils_mod

    utils_mod = types.ModuleType("utils")

    def is_true(v):
        return str(v).lower() in {"yes", "true", "1", "on"} or v is True

    def is_false(v):
        return str(v).lower() in {"no", "false", "0", "off"} or v is False

    utils_mod.is_true = is_true
    utils_mod.is_false = is_false
    sys.modules["utils"] = utils_mod


_install_test_stubs()

from script.apptainer import _get_apptainer_option, prepare_apptainer_inputs
from script.meta_schema import validate_meta


class DummyScript:
    meta = {"uid": "abcdef1234567890", "alias": "dummy-script"}


class DummyMlc:
    repos_path = "/tmp"

    def access(self, _):
        return {"list": []}


class TestApptainerOptionFallback(unittest.TestCase):

    def test_apptainer_overrides_docker(self):
        params = {
            "docker_run_cmd_prefix": "docker-prefix",
            "apptainer_run_cmd_prefix": "apptainer-prefix",
        }
        self.assertEqual(
            _get_apptainer_option(params, "run_cmd_prefix"),
            "apptainer-prefix",
        )

    def test_docker_option_used_when_apptainer_missing(self):
        params = {"docker_rebuild": True}
        self.assertTrue(_get_apptainer_option(params, "rebuild", False))

    def test_docker_mounts_aliases_to_bind(self):
        params = {
            "docker_mounts": ["/host:/cont"],
            "docker_os": "ubuntu",
            "docker_os_version": "24.04",
        }
        apptainer_inputs, _ = prepare_apptainer_inputs(
            params, {}, DummyScript(), True, DummyMlc())
        self.assertEqual(apptainer_inputs["bind"], ["/host:/cont"])
        self.assertEqual(apptainer_inputs["os"], "ubuntu")
        self.assertEqual(apptainer_inputs["os_version"], "24.04")

    def test_apptainer_options_override_docker_options(self):
        params = {
            "docker_os": "ubuntu",
            "docker_os_version": "24.04",
            "apptainer_os": "rocky",
            "apptainer_os_version": "9",
        }
        apptainer_inputs, _ = prepare_apptainer_inputs(
            params, {}, DummyScript(), True, DummyMlc())
        self.assertEqual(apptainer_inputs["os"], "rocky")
        self.assertEqual(apptainer_inputs["os_version"], "9")

    def test_apptainer_meta_schema_key_is_supported(self):
        meta = {
            "alias": "x",
            "uid": "1234567890abcdef",
            "automation_alias": "script",
            "automation_uid": "5b4e0237da074764",
            "tags": ["x"],
            "apptainer": {
                "run": True,
                "os": "ubuntu",
                "os_version": "24.04",
                "bind": ["/a:/b"],
            },
        }
        errors, warnings = validate_meta(meta)
        self.assertEqual(errors, [])
        self.assertEqual(
            [w for w in warnings if "apptainer" in w.lower()],
            [],
        )


if __name__ == "__main__":
    unittest.main()
