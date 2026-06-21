#!/bin/bash

echo "Installing Ansible via pip..."
${MLC_PYTHON_BIN_WITH_PATH} -m pip install ${MLC_ANSIBLE_PIP_INSTALL_STRING}
test $? -eq 0 || exit 1

echo ""
echo "Ansible installed successfully."
ansible --version
