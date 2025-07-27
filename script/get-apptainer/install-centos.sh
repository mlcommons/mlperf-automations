#!/bin/bash
set -e
${MLC_SUDO} yum install -y epel-release
${MLC_SUDO} yum install -y apptainer
test $? -eq 0 || exit $?

# Print version
apptainer --version
