#!/bin/bash

MLC_TMP_CURRENT_SCRIPT_PATH=${MLC_TMP_CURRENT_SCRIPT_PATH}

function exit_if_error() {
  test $? -eq 0 || exit $?
}

function is_true() {
  local val="${1,,}"  # lowercase
  [[ "${val}" == "yes" || "${val}" == "true" || "${val}" == "1" || "${val}" == "on" ]]
}

function run() {
  echo "Running: "
  echo "$1"
  echo ""
  if ! is_true "${MLC_FAKE_RUN}"; then
    eval "$1"
    exit_if_error
  fi
}

SUDO=${MLC_SUDO}
CURRENT_USER=$(whoami)
ACTION=${MLC_ISOLATE_ACTION}

# --- No new logins ---
if is_true "${MLC_ISOLATE_NO_NEW_LOGINS}"; then
  if [[ "${ACTION}" == "set" ]]; then
    run "${SUDO} touch /var/run/nologin"
    echo "Created /var/run/nologin - new non-root logins blocked"
  elif [[ "${ACTION}" == "unset" ]]; then
    if is_true "${MLC_ISOLATE_NOLOGIN_EXISTED}"; then
      echo "/var/run/nologin existed before set - leaving it in place"
    else
      run "${SUDO} rm -f /var/run/nologin"
      echo "Removed /var/run/nologin - new logins allowed"
    fi
  fi
fi

# --- Force logout other users ---
if is_true "${MLC_ISOLATE_FORCE_LOGOUT}"; then
  if [[ "${ACTION}" == "set" ]]; then
    echo "Forcing logout of all sessions except current user (${CURRENT_USER}).."
    OTHER_USERS=$(who | awk -v me="${CURRENT_USER}" '$1 != me {print $1}' | sort -u)
    if [[ -n "${OTHER_USERS}" ]]; then
      for u in ${OTHER_USERS}; do
        echo "Terminating sessions for user: ${u}"
        run "${SUDO} pkill -KILL -u ${u}"
      done
    else
      echo "No other user sessions found"
    fi
  elif [[ "${ACTION}" == "unset" ]]; then
    echo "Unset: no action for force-logout (cannot restore terminated sessions)"
  fi
fi

# --- Network isolation ---
if is_true "${MLC_ISOLATE_NETWORK}"; then
  if [[ "${ACTION}" == "set" ]]; then
    echo "Disabling non-loopback network interfaces..."
    IFS=',' read -ra IFACES <<< "${MLC_ISOLATE_SAVED_INTERFACES}"
    for iface in "${IFACES[@]}"; do
      if [[ -n "${iface}" ]]; then
        echo "Bringing down interface: ${iface}"
        run "${SUDO} ip link set ${iface} down"
      fi
    done
    echo "Network interfaces disabled"
  elif [[ "${ACTION}" == "unset" ]]; then
    echo "Re-enabling network interfaces from saved state..."
    IFS=',' read -ra IFACES <<< "${MLC_ISOLATE_SAVED_INTERFACES}"
    for iface in "${IFACES[@]}"; do
      if [[ -n "${iface}" ]]; then
        echo "Bringing up interface: ${iface}"
        run "${SUDO} ip link set ${iface} up"
      fi
    done
    echo "Network interfaces re-enabled"
  fi
fi
