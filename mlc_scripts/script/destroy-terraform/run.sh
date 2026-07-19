#!/bin/bash
source ${MLC_TERRAFORM_CONFIG_DIR}/credentials.sh
source ${MLC_TERRAFORM_CONFIG_DIR}/apply_credentials.sh
cd ${MLC_TERRAFORM_RUN_DIR}
terraform destroy --auto-approve
test $? -eq 0 || exit 1
