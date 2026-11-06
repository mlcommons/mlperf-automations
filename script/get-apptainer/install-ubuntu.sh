#!/bin/bash
set -e
${MLC_SUDO} apt-get update
${MLC_SUDO} apt-get install -y software-properties-common
${MLC_SUDO} add-apt-repository -y ppa:apptainer/ppa
${MLC_SUDO} apt-get update
# squashfuse/fuse2fs let unprivileged apptainer mount SIF images instead of extracting them.
${MLC_SUDO} apt-get install -y apptainer squashfuse fuse2fs
test $? -eq 0 || exit $?

# Ubuntu 24.04+ blocks unprivileged userns unless apptainer's AppArmor profile grants `userns`.
AA_PROFILE=/etc/apparmor.d/apptainer
AA_LOCAL=/etc/apparmor.d/local/apptainer
aa_has_userns() {
  ${MLC_SUDO} apparmor_parser -p "${AA_PROFILE}" 2>/dev/null | grep -qE '^\s*userns\s*,'
}
if [ "$(cat /proc/sys/kernel/apparmor_restrict_unprivileged_userns 2>/dev/null)" = "1" ] && ! aa_has_userns; then
  if [ ! -f "${AA_PROFILE}" ] || [[ "${MLC_APPTAINER_REPLACE_APPARMOR_PROFILE,,}" =~ ^(1|yes|true|on)$ ]]; then
    if [ -f "${AA_PROFILE}" ]; then
      ${MLC_SUDO} cp -p "${AA_PROFILE}" /var/backups/apparmor-apptainer.mlc-bak
      echo "Backed up ${AA_PROFILE} to /var/backups/apparmor-apptainer.mlc-bak"
    fi
    ${MLC_SUDO} tee "${AA_PROFILE}" > /dev/null <<'EOF'
abi <abi/4.0>,
include <tunables/global>
profile apptainer /usr/libexec/apptainer/bin/starter{,-suid} flags=(unconfined) {
  userns,
  include if exists <local/apptainer>
}
EOF
  elif grep -qE 'flags=\(\s*unconfined\s*\)' "${AA_PROFILE}" && grep -qE 'include if exists <local/apptainer>' "${AA_PROFILE}"; then
    # Unconfined profile: raising its ABI to 4.0 (needed for the userns rule) cannot add restrictions.
    ${MLC_SUDO} sed -i -E 's|^(\s*abi\s*<abi/)3\.0(>\s*,)|\14.0\2|' "${AA_PROFILE}"
    ${MLC_SUDO} mkdir -p "$(dirname "${AA_LOCAL}")"
    echo 'userns,' | ${MLC_SUDO} tee -a "${AA_LOCAL}" > /dev/null
  else
    echo "WARNING: ${AA_PROFILE} is a confined or customised profile; leaving it unchanged." >&2
    echo "         Grant 'userns,' to it manually, or set MLC_APPTAINER_REPLACE_APPARMOR_PROFILE=yes to replace it." >&2
  fi
  if aa_has_userns; then
    ${MLC_SUDO} apparmor_parser -r "${AA_PROFILE}"
  fi
fi
echo "apparmor_restrict_unprivileged_userns=$(cat /proc/sys/kernel/apparmor_restrict_unprivileged_userns 2>/dev/null || echo n/a)"
if aa_has_userns; then
  echo "apptainer AppArmor profile grants userns"
else
  echo "apptainer AppArmor profile does not grant userns"
fi

# Print version
apptainer --version

