# Getting Started with MLC Script Automation

## Install MLC Scripts
```
pip install mlc-scripts
```

`mlc-scripts` bundles the script content; it depends on `mlcflow` (the CLI and
execution engine) automatically, so this single command is all you need — no
`mlc pull repo` step required. See
[this repo is now content-only](migration.md) for what changed and why.

For more customized installation you can see [here](https://docs.mlcommons.org/mlcflow/install/)

## Running MLC Scripts

To execute a simple script in MLC that captures OS details, use the following command:

```bash
mlcr detect,os -j
```
* Here, `mlcr` is a shortform for `mlc run script --tags=`

This command gathers details about the system on which it's run, such as:

```json
[.... index.py:335 WARN] - Missing index files: script, cache, experiment. Forcing full index rebuild...
[.... script_utils.py:88 INFO] - * mlcr detect,os
[.... module.py:1881 INFO] -   - cache UID: c31147a2fc454878
[.... module.py:1912 INFO] - {
  "return": 0,
  "env": {
    "MLC_HOST_OS_TYPE": "linux",
    "MLC_HOST_OS_BITS": "64",
    "MLC_HOST_OS_FLAVOR": "ubuntu",
    "MLC_HOST_OS_FLAVOR_LIKE": "debian",
    "MLC_HOST_OS_VERSION": "24.04",
    "MLC_HOST_OS_KERNEL_VERSION": "6.8.0-52-generic",
    "MLC_HOST_OS_GLIBC_VERSION": "2.39",
    "MLC_HOST_OS_MACHINE": "x86_64",
    "MLC_HOST_OS_PACKAGE_MANAGER": "apt",
    "MLC_HOST_OS_PACKAGE_MANAGER_INSTALL_CMD": "DEBIAN_FRONTEND=noninteractive apt-get install -y",
    "MLC_HOST_OS_PACKAGE_MANAGER_UPDATE_CMD": "apt-get update -y",
    "+MLC_HOST_OS_DEFAULT_LIBRARY_PATH": [
      "/usr/local/lib/x86_64-linux-gnu",
      "/lib/x86_64-linux-gnu",
      "/usr/lib/x86_64-linux-gnu",
      "/usr/lib/x86_64-linux-gnu64",
      "/usr/local/lib64",
      "/lib64",
      "/usr/lib64",
      "/usr/local/lib",
      "/lib",
      "/usr/lib",
      "/usr/x86_64-linux-gnu/lib64",
      "/usr/x86_64-linux-gnu/lib"
    ],
    "MLC_HOST_PLATFORM_FLAVOR": "x86_64",
    "MLC_HOST_PYTHON_BITS": "64",
    "MLC_HOST_SYSTEM_NAME": "arjun-spr"
  },
  "new_env": {
    "MLC_HOST_OS_TYPE": "linux",
    "MLC_HOST_OS_BITS": "64",
    "MLC_HOST_OS_FLAVOR": "ubuntu",
    "MLC_HOST_OS_FLAVOR_LIKE": "debian",
    "MLC_HOST_OS_VERSION": "24.04",
    "MLC_HOST_OS_KERNEL_VERSION": "6.8.0-52-generic",
    "MLC_HOST_OS_GLIBC_VERSION": "2.39",
    "MLC_HOST_OS_MACHINE": "x86_64",
    "MLC_HOST_OS_PACKAGE_MANAGER": "apt",
    "MLC_HOST_OS_PACKAGE_MANAGER_INSTALL_CMD": "DEBIAN_FRONTEND=noninteractive apt-get install -y",
    "MLC_HOST_OS_PACKAGE_MANAGER_UPDATE_CMD": "apt-get update -y",
    "+MLC_HOST_OS_DEFAULT_LIBRARY_PATH": [
      "/usr/local/lib/x86_64-linux-gnu",
      "/lib/x86_64-linux-gnu",
      "/usr/lib/x86_64-linux-gnu",
      "/usr/lib/x86_64-linux-gnu64",
      "/usr/local/lib64",
      "/lib64",
      "/usr/lib64",
      "/usr/local/lib",
      "/lib",
      "/usr/lib",
      "/usr/x86_64-linux-gnu/lib64",
      "/usr/x86_64-linux-gnu/lib"
    ],
    "MLC_HOST_PLATFORM_FLAVOR": "x86_64",
    "MLC_HOST_PYTHON_BITS": "64",
    "MLC_HOST_SYSTEM_NAME": "arjun-spr"
  },
  "state": {
    "os_uname_machine": "x86_64",
    "os_uname_all": "Linux arjun-spr 6.8.0-52-generic #53-Ubuntu SMP PREEMPT_DYNAMIC Sat Jan 11 00:06:25 UTC 2025 x86_64 x86_64 x86_64 GNU/Linux"
  },
  "new_state": {
    "os_uname_machine": "x86_64",
    "os_uname_all": "Linux arjun-spr 6.8.0-52-generic #53-Ubuntu SMP PREEMPT_DYNAMIC Sat Jan 11 00:06:25 UTC 2025 x86_64 x86_64 x86_64 GNU/Linux"
  },
  "deps": []
}
```

For more details on MLC scripts, see the [MLC documentation](index.md).


You can also execute the script from Python as follows:

