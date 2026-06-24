#!/bin/bash

# Install galaxy roles/collections if specified
if [[ -n "${MLC_ANSIBLE_GALAXY_INSTALL_CMD}" ]]; then
  echo "Installing Ansible Galaxy requirements..."
  ${MLC_ANSIBLE_GALAXY_INSTALL_CMD}
  test $? -eq 0 || exit $?
fi

# Run ansible-playbook
echo "Running: ansible-playbook ${MLC_ANSIBLE_PLAYBOOK_PATH} ${MLC_ANSIBLE_ARGS}"
ansible-playbook ${MLC_ANSIBLE_PLAYBOOK_PATH} ${MLC_ANSIBLE_ARGS}
test $? -eq 0 || exit $?
