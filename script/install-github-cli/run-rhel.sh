#!/bin/bash

if [ "${MLC_GH_INSTALL_WITHOUT_SUDO}" == "yes" ]; then
    bash ${MLC_SOURCE}/run-nosudo.sh
    exit $?
fi

sudo dnf install -y 'dnf-command(config-manager)'
sudo dnf config-manager --add-repo https://cli.github.com/packages/rpm/gh-cli.repo
sudo dnf install -y gh
