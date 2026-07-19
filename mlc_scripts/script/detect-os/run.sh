#!/bin/bash

uname -m > tmp-run.out
uname -a >> tmp-run.out
if test -f "/etc/os-release"; then
   echo "MLC_HOST_OS_FLAVOR=`cat /etc/os-release | grep '^ID=' | cut -d'=' -f2 | cut -d'"' -f2 | tr '[:upper:]' '[:lower:]'`" >> tmp-run-env.out
   echo "MLC_HOST_OS_FLAVOR_LIKE=`cat /etc/os-release | grep '^ID_LIKE=' | cut -d'=' -f2 | cut -d'"' -f2 | tr '[:upper:]' '[:lower:]'`" >> tmp-run-env.out
   echo "MLC_HOST_OS_VERSION=`cat /etc/os-release | grep '^VERSION_ID=' | cut -d'=' -f2 | cut -d'"' -f2 | cut -d'"' -f2 | tr '[:upper:]' '[:lower:]'`" >> tmp-run-env.out
   echo "MLC_HOST_OS_KERNEL_VERSION=`uname -r`" >> tmp-run-env.out
   echo "MLC_HOST_PLATFORM_FLAVOR=`uname -m`" >> tmp-run-env.out
   echo "MLC_HOST_OS_GLIBC_VERSION=`ldd --version | tail -n +1 | head -1 | cut -d')' -f2 | cut -d' ' -f2`" >> tmp-run-env.out
else
   MLC_HOST_OS_FLAVOR=`sw_vers | grep '^ProductName:' | cut -f2 | tr '[:upper:]' '[:lower:]'`
   if [ -z ${MLC_HOST_OS_FLAVOR} ]; then
     MLC_HOST_OS_FLAVOR=`sw_vers | grep '^ProductName:' | cut -f3 | tr '[:upper:]' '[:lower:]' `
   fi
   echo "MLC_HOST_OS_FLAVOR=${MLC_HOST_OS_FLAVOR}" >> tmp-run-env.out
   echo "MLC_HOST_OS_VERSION=`sw_vers | grep '^ProductVersion:' | cut -f2 | tr '[:upper:]' '[:lower:]' `" >> tmp-run-env.out
   echo "MLC_HOST_OS_KERNEL_VERSION=`uname -r`" >> tmp-run-env.out
   echo "MLC_HOST_PLATFORM_FLAVOR=`uname -m `" >> tmp-run-env.out
fi
filesystems=$(
      awk '
        $3 !~ /^(autofs|bpf|cgroup|cgroup2|configfs|devpts|devtmpfs|efivarfs|fusectl|hugetlbfs|debugfs|binfmt_misc|mqueue|nsfs|pstore|proc|rpc_pipefs|securityfs|sysfs|tmpfs|tracefs)$/ &&
        $3 !~ /^(overlay|aufs|squashfs|fuse\..*|cgroup.*)$/ {
          print $3
        }
      ' /proc/mounts \
      | sort -u \
      | tr '\n' ' ' \
      | sed 's/ $//'
    )
echo "MLC_HOST_FILESYSTEMS=$filesystems">>tmp-run-env.out

