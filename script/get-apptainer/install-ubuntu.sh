#!/bin/bash
set -e
${MLC_SUDO} apt-get update
${MLC_SUDO} apt-get install -y software-properties-common
${MLC_SUDO} add-apt-repository -y ppa:apptainer/ppa
${MLC_SUDO} apt-get update
${MLC_SUDO} apt-get install -y apptainer
test $? -eq 0 || exit $?

# Ubuntu 24.04+ blocks unprivileged user namespaces via AppArmor; allow them for apptainer only.
if [ "$(cat /proc/sys/kernel/apparmor_restrict_unprivileged_userns 2>/dev/null)" = "1" ] && [ ! -f /etc/apparmor.d/apptainer ]; then
  ${MLC_SUDO} tee /etc/apparmor.d/apptainer > /dev/null <<'EOF'
abi <abi/4.0>,
include <tunables/global>
profile apptainer /usr/libexec/apptainer/bin/starter{,-suid} flags=(unconfined) {
  userns,
  include if exists <local/apptainer>
}
EOF
  ${MLC_SUDO} apparmor_parser -r /etc/apparmor.d/apptainer
  test $? -eq 0 || exit $?
fi

# Print version
apptainer --version

