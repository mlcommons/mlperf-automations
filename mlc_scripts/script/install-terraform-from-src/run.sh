#!/bin/bash

CUR_DIR=${PWD}
if [ ! -d "terraform" ]; then
  echo "Cloning Terraform from ${MLC_GIT_URL} with branch ${MLC_GIT_CHECKOUT}..."
  git clone  -b "${MLC_GIT_CHECKOUT}" ${MLC_GIT_URL} terraform
fi
test $? -eq 0 || exit 1

export GOPATH=$CUR_DIR
cd terraform
go install
test $? -eq 0 || exit 1

echo "******************************************************"
echo "Terraform is built and installed to ${GOPATH}/bin/terraform ..."
