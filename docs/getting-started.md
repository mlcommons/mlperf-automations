# Getting Started with MLC Script Automation

## Running MLC Scripts

To execute a simple script in MLC that captures OS details, use the following command:

```bash
mlcr detect,os -j
```
* Here, `mlcr` is a shortform for `mlc run script --tags=`

This command gathers details about the system on which it's run, such as:

```json
$ mlcr detect,os -j
[2025-02-03 04:57:23,449 main.py:694 INFO] - Repos path for Index: /home/arjun/MLC/repos
[2025-02-03 04:57:24,167 main.py:837 INFO] - Shared index for script saved to /home/arjun/MLC/repos/index_script.json.
[2025-02-03 04:57:24,167 main.py:837 INFO] - Shared index for cache saved to /home/arjun/MLC/repos/index_cache.json.
[2025-02-03 04:57:24,167 main.py:837 INFO] - Shared index for experiment saved to /home/arjun/MLC/repos/index_experiment.json.
[2025-02-03 04:57:24,210 module.py:574 INFO] - * mlcr detect,os
[2025-02-03 04:57:24,213 module.py:5354 INFO] -        ! cd /mnt/arjun/MLC/repos/gateoverflow@mlperf-automations
[2025-02-03 04:57:24,213 module.py:5355 INFO] -        ! call /home/arjun/MLC/repos/gateoverflow@mlperf-automations/script/detect-os/run.sh from tmp-run.sh
[2025-02-03 04:57:24,245 module.py:5501 INFO] -        ! call "postprocess" from /home/arjun/MLC/repos/gateoverflow@mlperf-automations/script/detect-os/customize.py
[2025-02-03 04:57:24,254 module.py:2195 INFO] - {
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

