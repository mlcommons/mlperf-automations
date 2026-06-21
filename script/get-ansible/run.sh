#!/bin/bash
ansible-playbook --version > tmp-ver.out
test $? -eq 0 || exit 1
