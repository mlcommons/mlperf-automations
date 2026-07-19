#!/bin/bash
if [[ ${MLC_TERRAFORM_CONFIG_DIR} == "aws" ]]; then
  source ${MLC_TERRAFORM_CONFIG_DIR}/credentials.sh
  source ${MLC_TERRAFORM_CONFIG_DIR}/apply_credentials.sh
fi


if [[ -z $MLC_DESTROY_TERRAFORM ]]; then
  terraform init -input=false
  terraform plan -out=tfplan -input=false
  terraform apply  -input=false tfplan
  test $? -eq 0 || exit $?
  sleep 20
fi
