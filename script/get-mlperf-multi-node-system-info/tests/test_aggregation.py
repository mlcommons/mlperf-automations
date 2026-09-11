"""Aggregation tests for get-mlperf-multi-node-system-info.

The aggregation step reads one JSON file per node out of a directory, so it
can be tested by seeding that directory - no ssh, no remote nodes, no mlcflow
run. This is the layer that was previously untested end to end: a node whose
file never arrived used to be a log line, and the run reported success with
that node quietly absent.
"""
import importlib.util
import json
import logging
import os
import sys
import tempfile
import unittest

_SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_customize():
    """Import the script's customize.py the way the engine would.

    ``customize.py`` opens with ``from utils import *``, which resolves to
    mlcflow's bundled ``automation/utils.py`` because the engine puts that
    directory on sys.path. Reproduce that here rather than skipping.
    """
    try:
        import utils  # noqa: F401
    except ImportError:
        try:
            import mlc
        except ImportError:
            raise unittest.SkipTest("mlcflow is not installed")
        automation = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(mlc.__file__))),
            "automation")
        if not os.path.isdir(automation):
            raise unittest.SkipTest(
                f"mlcflow's automation/ not found at {automation}")
        sys.path.insert(0, automation)

    spec = importlib.util.spec_from_file_location(
        "multi_node_customize", os.path.join(_SCRIPT_DIR, "customize.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _Automation:
    def __init__(self):
        self.logger = logging.getLogger("multi-node-test")
        self.logger.addHandler(logging.NullHandler())


def _node(commit="abc123", model="EPYC-9654", accel="H100", per_node="8"):
    """One node's file, cut down to the fields aggregation actually reads."""
    return {
        "host_processor_model_name": model,
        "host_processors_per_node": "2",
        "host_memory_capacity": "1.5 TB",
        "accelerator_model_name": accel,
        "accelerators_per_node": per_node,
        "number_of_nodes": 1,
        "operating_system": "Ubuntu 22.04",
        "mlc_scripts_version": {
            "source": "package", "commit": commit,
            "version": "1.2.0a4", "branch": "", "dirty": False,
        },
    }


class MultiNodeAggregationTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.customize = _load_customize()

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.dir_path = self.temp_dir.name
        self.out_file = os.path.join(self.dir_path, "system-info.json")

    def _write_node(self, node_id, payload):
        path = os.path.join(
            self.dir_path, f"mlperf-system-info-single-node-{node_id}.json")
        with open(path, "w") as f:
            json.dump(payload, f)
        return path

    def _postprocess(self, remote_count, **env_extra):
        env = {
            "MLC_MULTI_NODE_SYSTEM_INFO_DIR_PATH": self.dir_path,
            "MLC_MULTI_NODE_SYSTEM_INFO_FILE_PATH": self.out_file,
            "MLC_REMOTE_RUN_SSH_ID_COUNT": str(remote_count),
            "MLC_MLPERF_SYSTEM_NAME": "test-system",
            "MLC_MLPERF_SUBMITTER": "TestOrg",
            "MLC_TMP_CURRENT_SCRIPT_REPO_PATH": self.dir_path,
        }
        env.update(env_extra)
        return self.customize.postprocess(
            {"env": env, "automation": _Automation(), "state": {}})

    def _output(self):
        with open(self.out_file) as f:
            return json.load(f)

    # -- the happy path ---------------------------------------------------

    def test_every_node_present_aggregates_cleanly(self):
        self._write_node(0, _node())
        self._write_node(1, _node())
        r = self._postprocess(remote_count=1)
        self.assertEqual(r["return"], 0, r.get("error"))
        self.assertTrue(os.path.isfile(self.out_file))

    def test_identical_nodes_collapse_into_one_type_with_a_count(self):
        """Two localhost 'nodes' in CI land here, so this is load-bearing."""
        self._write_node(0, _node())
        self._write_node(1, _node())
        self._postprocess(remote_count=1)
        blob = json.dumps(self._output())
        self.assertIn("EPYC-9654", blob)

    # -- the gap this work closes ----------------------------------------

    def test_a_missing_node_file_fails_the_run(self):
        self._write_node(0, _node())
        # node 1 never came back
        r = self._postprocess(remote_count=1)
        self.assertEqual(
            r["return"], 1,
            "a system description missing a node reported success")
        self.assertIn("node(s) 1", r["error"])

    def test_the_error_names_the_file_it_looked_for(self):
        self._write_node(0, _node())
        r = self._postprocess(remote_count=1)
        self.assertIn("mlperf-system-info-single-node-1.json", r["error"])

    def test_every_missing_node_is_named_not_just_the_first(self):
        self._write_node(0, _node())
        r = self._postprocess(remote_count=3)
        for node_id in ("1", "2", "3"):
            self.assertIn(node_id, r["error"])

    def test_a_missing_host_node_fails_too(self):
        self._write_node(1, _node())
        r = self._postprocess(remote_count=1)
        self.assertEqual(r["return"], 1)
        self.assertIn("node(s) 0", r["error"])

    # -- version reporting, the acceptance signal -------------------------

    def test_matching_versions_report_consistent(self):
        """The one-line acceptance check for the whole provisioning feature.

        It needs get_repo_version() to understand a packaged install; before
        that fix this block was absent rather than false.
        """
        with open(os.path.join(self.dir_path, ".mlc-provenance.json"),
                  "w") as f:
            json.dump({"version": "1.2.0a4", "commit": "abc123"}, f)
        self._write_node(0, _node(commit="abc123"))
        self._write_node(1, _node(commit="abc123"))
        self.assertEqual(self._postprocess(remote_count=1)["return"], 0)
        block = self._output().get("mlc_scripts_version")
        self.assertIsNotNone(
            block, "no version block: a packaged head reported nothing")
        self.assertTrue(block["consistent"], block)

    def test_a_node_on_a_different_version_is_reported_not_hidden(self):
        with open(os.path.join(self.dir_path, ".mlc-provenance.json"),
                  "w") as f:
            json.dump({"version": "1.2.0a4", "commit": "abc123"}, f)
        self._write_node(0, _node(commit="abc123"))
        self._write_node(1, _node(commit="totally-different"))
        self._postprocess(remote_count=1)
        block = self._output().get("mlc_scripts_version")
        self.assertFalse(block["consistent"], block)
        self.assertIn("1", block["nodes"])

    def _packaged_node(self, commit, version):
        n = _node(commit=commit)
        n["mlc_scripts_version"]["version"] = version
        return n

    def test_two_different_versions_are_not_consistent_without_a_commit(self):
        """Two genuinely different wheels must not report consistent: true.

        The comparison keys on commit alone. A wheel built without git
        metadata carries no commit, so two different versions both compare
        as '' == '' and the safeguard reports agreement -- in exactly the
        packaged case the provisioning work exists to protect.
        """
        with open(os.path.join(self.dir_path, ".mlc-provenance.json"),
                  "w") as f:
            json.dump({"version": "1.1.0", "commit": ""}, f)
        self._write_node(0, self._packaged_node("", "1.1.0"))
        self._write_node(1, self._packaged_node("", "1.0.2"))
        self._postprocess(remote_count=1)
        block = self._output().get("mlc_scripts_version")
        self.assertIsNotNone(block)
        self.assertFalse(
            block["consistent"],
            f"node 1 is on 1.0.2 and the head on 1.1.0, reported as "
            f"consistent: {block}")

    def test_unknown_commits_do_not_confirm_each_other(self):
        """get_commit_hash() returns the literal 'unknown' when git metadata
        is missing, so two unrelated builds both say 'unknown' and match."""
        with open(os.path.join(self.dir_path, ".mlc-provenance.json"),
                  "w") as f:
            json.dump({"version": "1.1.0", "commit": "unknown"}, f)
        self._write_node(0, self._packaged_node("unknown", "1.1.0"))
        self._write_node(1, self._packaged_node("unknown", "1.0.2"))
        self._postprocess(remote_count=1)
        block = self._output().get("mlc_scripts_version")
        self.assertIsNotNone(block)
        self.assertFalse(block["consistent"], block)


class ProvisioningPassthroughTest(unittest.TestCase):
    """preprocess forwards the provisioning flags and fails on a lost node."""

    @classmethod
    def setUpClass(cls):
        cls.customize = _load_customize()

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.calls = []

        real_access = self.customize.mlc.access
        self.addCleanup(setattr, self.customize.mlc, "access", real_access)

    def _run(self, access, **env_extra):
        self.customize.mlc.access = access
        env = {
            "MLC_MULTINODE_SYSTEM_SSH_IDS": "bench@node1,bench@node2",
            "MLC_MULTI_NODE_SYSTEM_INFO_DIR_PATH": self.temp_dir.name,
            # preprocess now refuses without this, before contacting a node.
            "MLC_MLPERF_SYSTEM_NAME": "test-system",
        }
        env.update(env_extra)
        return self.customize.preprocess(
            {"env": env, "automation": _Automation(), "state": {}})

    def _record_ok(self, payload):
        self.calls.append(payload)
        return {"return": 0}

    def test_an_unconfigured_run_forwards_no_provisioning_keys(self):
        """The opt-in promise, from this script's side."""
        r = self._run(self._record_ok)
        self.assertEqual(r["return"], 0, r.get("error"))
        self.assertEqual(len(self.calls), 2)
        for call in self.calls:
            leaked = [k for k in call if k.startswith("remote_")
                      and k not in ("remote_host", "remote_user",
                                    "remote_port")]
            self.assertEqual(
                leaked, [], f"unexpected keys forwarded: {leaked}")

    def test_a_pinned_version_reaches_every_node(self):
        self._run(self._record_ok,
                  MLC_REMOTE_MLC_SCRIPTS="1.2.0a4",
                  MLC_REMOTE_PROVISION="package")
        self.assertEqual(len(self.calls), 2)
        for call in self.calls:
            self.assertEqual(call["remote_mlc_scripts"], "1.2.0a4")
            self.assertEqual(call["remote_provision"], "package")

    def test_blank_values_are_not_forwarded(self):
        """An unset MLC input arrives as '', which must not look like a mode."""
        self._run(self._record_ok, MLC_REMOTE_PROVISION="   ")
        self.assertNotIn("remote_provision", self.calls[0])

    def test_a_node_that_fails_fails_the_run(self):
        def access(payload):
            self.calls.append(payload)
            if payload["remote_host"] == "node2":
                return {"return": 1, "error": "ssh: connection refused"}
            return {"return": 0}

        r = self._run(access)
        self.assertEqual(r["return"], 1, "a lost node was reported as success")
        self.assertIn("node2", r["error"])
        self.assertIn("connection refused", r["error"])
        self.assertNotIn("node1", r["error"])

    def test_every_failed_node_is_named(self):
        r = self._run(lambda p: {"return": 1, "error": "boom"})
        self.assertEqual(r["return"], 1)
        self.assertIn("node1", r["error"])
        self.assertIn("node2", r["error"])
        self.assertIn("2 of 2", r["error"])

    def test_an_exception_is_a_failed_node_not_a_crash(self):
        def access(payload):
            raise OSError("host unreachable")

        r = self._run(access)
        self.assertEqual(r["return"], 1)
        self.assertIn("host unreachable", r["error"])


if __name__ == "__main__":
    unittest.main()


class SystemNameIsCheckedBeforeAnyNodeTest(unittest.TestCase):
    """The check used to live in postprocess.

    By the time it fired there, every node had been reached, provisioned,
    run and copied back. A missing string then discarded all of that and
    wrote no aggregate, and the only remedy was to run the whole thing
    again. Nothing about system_name depends on the nodes, so it is
    answerable before the first ssh.
    """

    @classmethod
    def setUpClass(cls):
        cls.customize = _load_customize()

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.calls = []
        real_access = self.customize.mlc.access
        self.addCleanup(setattr, self.customize.mlc, "access", real_access)

        def record(payload):
            self.calls.append(payload)
            return {"return": 0}

        self.customize.mlc.access = record

    def _preprocess(self, **env_extra):
        env = {
            "MLC_MULTINODE_SYSTEM_SSH_IDS": "bench@node1,bench@node2",
            "MLC_MULTI_NODE_SYSTEM_INFO_DIR_PATH": self.temp_dir.name,
        }
        env.update(env_extra)
        return self.customize.preprocess(
            {"env": env, "automation": _Automation(), "state": {}})

    def test_a_missing_system_name_fails_before_the_first_node(self):
        r = self._preprocess()
        self.assertEqual(r["return"], 1)
        self.assertIn("system_name is required", r["error"])
        self.assertEqual(
            self.calls, [],
            "no node may be contacted before system_name is validated")

    def test_the_message_names_every_way_to_supply_it(self):
        r = self._preprocess()
        for how in ("--system_name", "config file", "MLC_MLPERF_SYSTEM_NAME"):
            self.assertIn(how, r["error"])

    def test_a_supplied_system_name_proceeds(self):
        r = self._preprocess(MLC_MLPERF_SYSTEM_NAME="named")
        self.assertEqual(r["return"], 0, r.get("error"))
        self.assertEqual(len(self.calls), 2)

    def test_a_config_file_can_supply_it(self):
        """_load_config_file runs first, so the config file still counts --
        the check must not demand the command-line flag specifically."""
        cfg = os.path.join(self.temp_dir.name, "cfg.json")
        with open(cfg, "w") as fh:
            json.dump({"system_name": "from-config"}, fh)

        r = self._preprocess(MLC_MLPERF_CONFIG_FILE=cfg)

        self.assertEqual(r["return"], 0, r.get("error"))
        self.assertEqual(len(self.calls), 2)

    def test_an_empty_system_name_is_not_a_name(self):
        r = self._preprocess(MLC_MLPERF_SYSTEM_NAME="")
        self.assertEqual(r["return"], 1)
        self.assertEqual(self.calls, [])
