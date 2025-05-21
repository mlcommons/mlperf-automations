#!/usr/bin/env bash
set -euo pipefail

TARGET_FREQ="${MLC_TARGET_FREQ:-}"
DRIVER_FILE="/sys/devices/system/cpu/cpu0/cpufreq/scaling_driver"

if [[ ! -r $DRIVER_FILE ]]; then
  echo "Error: cannot read $DRIVER_FILE. Is cpufreq enabled?" >&2
  exit 2
fi
DRIVER=$(<"$DRIVER_FILE")
echo "Detected cpufreq driver: $DRIVER"

# Normalize AMD pstate variants
if [[ $DRIVER == amd-pstate* ]]; then
  DRIVER_KEY="amd-pstate"
else
  DRIVER_KEY="$DRIVER"
fi


case "$DRIVER_KEY" in
  intel_pstate)
    echo "→ intel_pstate: disabling turbo, setting performance governor"
    echo 0 | ${MLC_SUDO} tee /sys/devices/system/cpu/intel_pstate/no_turbo >/dev/null
    ${MLC_SUDO} cpupower frequency-set -g performance
    ;;

  amd-pstate)
    echo "→ amd_pstate: enabling boost, setting performance governor"
    # boost file is global under cpufreq
    if [[ -w /sys/devices/system/cpu/cpufreq/boost ]]; then
      echo 1 | ${MLC_SUDO} tee /sys/devices/system/cpu/cpufreq/boost >/dev/null
    fi
    ${MLC_SUDO} cpupower frequency-set -g performance
    echo ""
    echo "Note: amd-pstate does _not_ support a userspace/fixed frequency mode."
    echo "If you need a precise kHz, switch back to acpi-cpufreq in your kernel cmdline."
    ;;

  acpi-cpufreq)
    echo "→ acpi-cpufreq: switching to userspace governor + fixed freq"
    if [[ -z "$TARGET_FREQ" ]]; then
      TARGET_FREQ=$(< /sys/devices/system/cpu/cpu0/cpufreq/scaling_min_freq)
      echo "   No target given; defaulting to min freq = ${TARGET_FREQ} kHz"
    fi
    ${MLC_SUDO} cpupower frequency-set -g userspace
    ${MLC_SUDO} cpupower frequency-set -f "${TARGET_FREQ}"
    ;;

  *)
    echo "Unsupported driver: $DRIVER" >&2
    exit 3
    ;;
esac

echo ""
echo "Resulting settings for CPU0:"
cpupower frequency-info | sed -n '1,5p'

