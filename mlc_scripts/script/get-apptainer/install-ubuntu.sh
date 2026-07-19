#!/bin/bash
set -e
${MLC_SUDO} apt-get update
${MLC_SUDO} apt-get install -y software-properties-common
${MLC_SUDO} add-apt-repository -y ppa:apptainer/ppa
${MLC_SUDO} apt-get update
${MLC_SUDO} apt-get install -y apptainer
test $? -eq 0 || exit $?

# Print version
apptainer --version

