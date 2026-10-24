#!/bin/bash
# ============================================================
#  Fire TV Stick 3rd Gen - RESTORE Script
#  Undoes everything scripts/debloat_fireos.sh disabled.
# ============================================================
set -uo pipefail

FIRE_TV_IP="192.168.1.41"
FIRE_TV_PORT="5555"
SERIAL="${FIRE_TV_IP}:${FIRE_TV_PORT}"
BACKUP_DIR="${HOME}/.cleanyourtv"

echo "=========================================="
echo "  Fire TV Debloat - RESTORE"
echo "=========================================="

echo ""
echo "[1/4] Connecting..."
if ! adb -s "${SERIAL}" get-state >/dev/null 2>&1; then
  adb connect "${SERIAL}" >/dev/null 2>&1 || true
fi
if ! adb -s "${SERIAL}" get-state >/dev/null 2>&1; then
  echo "ERROR: Fire TV not reachable at ${SERIAL}"
  adb devices
  exit 1
fi
echo "Connected: ${SERIAL}"

echo ""
echo "[2/4] Finding the most recent recovery record..."
RECORD="$(ls -t "${BACKUP_DIR}"/disabled_fireos_*.txt 2>/dev/null | head -1)"
if [ -z "${RECORD}" ]; then
  echo "No recovery record found in ${BACKUP_DIR}"
  echo ""
  echo "Falling back to the debloat list itself (re-enables every listed package):"
  RECORD="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/debloat_fireos.txt"
  echo "  ${RECORD}"
fi
echo "Using: ${RECORD}"

echo ""
echo "[3/4] Re-enabling packages..."
OK=0
FAIL=0
while IFS= read -r line; do
  line="${line%%#*}"
  pkg="$(echo "${line}" | tr -d '[:space:]')"
  [ -z "${pkg}" ] && continue

  out="$(adb -s "${SERIAL}" shell pm enable --user 0 "${pkg}" 2>&1 | tr -d '\r')"
  if echo "${out}" | grep -qiE "new state: enabled|already"; then
    echo "  enabled: ${pkg}"
    OK=$((OK + 1))
  else
    echo "  skip/failed: ${pkg}  (${out})"
    FAIL=$((FAIL + 1))
  fi
done < "${RECORD}"

echo ""
echo "[4/4] Summary"
echo "  Re-enabled: ${OK}"
echo "  Skipped:    ${FAIL}"
echo ""
echo "IMPORTANT: If the stock Amazon launcher was disabled, re-enable it now:"
echo "  adb -s ${SERIAL} shell pm enable --user 0 com.amazon.tv.launcher"
echo ""
echo "Then reboot the stick:"
echo "  adb -s ${SERIAL} reboot"
echo "=========================================="
