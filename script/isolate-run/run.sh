#!/bin/bash

MLC_TMP_CURRENT_SCRIPT_PATH=${MLC_TMP_CURRENT_SCRIPT_PATH}

function exit_if_error() {
  test $? -eq 0 || exit $?
}

function run() {
  echo "Running: "
  echo "$1"
  echo ""
  if [[ ${MLC_FAKE_RUN} != 'yes' ]]; then
    eval "$1"
    exit_if_error
  fi
}

SUDO=${MLC_SUDO}
CURRENT_USER=$(whoami)

# --- No new logins ---
if [[ "${MLC_ISOLATE_NO_NEW_LOGINS}" == "yes" ]]; then
  if [[ "${MLC_ISOLATE_NO_UNDO}" == "yes" ]]; then
    run "${SUDO} touch /var/run/nologin"
    echo "Created /var/run/nologin - new non-root logins blocked"
  else
    run "${SUDO} rm -f /var/run/nologin"
    echo "Removed /var/run/nologin - new logins allowed"
  fi
fi

# --- Force logout other users ---
if [[ "${MLC_ISOLATE_FORCE_LOGOUT}" == "yes" ]]; then
  if [[ "${MLC_ISOLATE_NO_UNDO}" == "yes" ]]; then
    echo "Forcing logout of all sessions except current user (${CURRENT_USER})..."
    # Get all logged-in users except the current one and kill their sessions
    OTHER_USERS=$(who | awk -v me="${CURRENT_USER}" '$1 != me {print $1}' | sort -u)
    if [[ -n "${OTHER_USERS}" ]]; then
      for u in ${OTHER_USERS}; do
        echo "Terminating sessions for user: ${u}"
        run "${SUDO} pkill -KILL -u ${u}"
      done
    else
      echo "No other user sessions found"
    fi
  else
    echo "Undo (default): no action needed for force-logout"
  fi
fi

# --- Network isolation ---
if [[ "${MLC_ISOLATE_NETWORK}" == "yes" ]]; then
  if [[ "${MLC_ISOLATE_NO_UNDO}" == "yes" ]]; then
    echo "Disabling all non-loopback network interfaces..."
    for iface in $(ip -o link show up | awk -F': ' '{print $2}' | grep -v '^lo$'); do
      echo "Bringing down interface: ${iface}"
      run "${SUDO} ip link set ${iface} down"
    done
    echo "Network interfaces disabled"
  else
    echo "Re-enabling all non-loopback network interfaces..."
    for iface in $(ip -o link show | awk -F': ' '{print $2}' | grep -v '^lo$'); do
      run "${SUDO} ip link set ${iface} up"
    done
    echo "Network interfaces re-enabled"
  fi
fi
