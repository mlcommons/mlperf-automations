#!/bin/bash
set -e
${MLC_SUDO} apt-get update
${MLC_SUDO} apt-get install -y software-properties-common
${MLC_SUDO} add-apt-repository -y ppa:apptainer/ppa
${MLC_SUDO} apt-get update
${MLC_SUDO} apt-get install -y apptainer
test $? -eq 0 || exit $?

# Ubuntu 24.04+ blocks unprivileged userns; the packaged profile (abi 3.0, no userns rule) is not enough on newer kernels.
if [ "$(cat /proc/sys/kernel/apparmor_restrict_unprivileged_userns 2>/dev/null)" = "1" ] && ! grep -qE '^\s*userns,' /etc/apparmor.d/apptainer 2>/dev/null; then
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
echo "apparmor_restrict_unprivileged_userns=$(cat /proc/sys/kernel/apparmor_restrict_unprivileged_userns 2>/dev/null || echo n/a)"
grep -H userns /etc/apparmor.d/apptainer 2>/dev/null || echo "apptainer AppArmor profile has no userns rule"

# Print version
apptainer --version

