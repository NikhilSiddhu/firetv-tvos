#!/bin/bash
# ============================================================
#  Fire TV Stick 3rd Gen - Safe Debloat Script
#  Fire OS 7.7.1.7 (ps7717/5741)
#  Port: 5555 (set FIRE_TV_IP in local.env)
# ============================================================
#  SAFETY MODEL
#  - Only disables packages that are BOTH in debloat_fireos.txt
#    AND actually installed on the device.
#  - Never touches the Home/launcher, setup wizard, or core
#    system packages unless explicitly allowed.
#  - Writes a recovery record so restore_debloat.sh can undo it.
#  - Supports --dry-run to preview with zero changes.
# ============================================================

set -uo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_env.sh"

DEBLOAT_LIST="${PROJECT_ROOT}/scripts/debloat_fireos.txt"
BACKUP_DIR="${HOME}/.cleanyourtv"
RUN_ID="$(date +%Y%m%d_%H%M%S)"
RECORD_FILE="${BACKUP_DIR}/disabled_fireos_${RUN_ID}.txt"

DRY_RUN=0
[ "${1:-}" = "--dry-run" ] && DRY_RUN=1

# Packages we must NEVER disable (Home, setup, core system)
PROTECTED_PKGS=(
  "com.amazon.tv.launcher"
  "com.amazon.tv.launcherx"
  "com.amazon.firetv.launcher"
  "com.amazon.tv.launcherwrapper"
  "com.amazon.firetv.launcherwrapper"
  "com.android.systemui"
  "android"
  "com.android.settings"
  "com.amazon.tv.settings"
  "com.amazon.device.settings"
  "com.amazon.tv.setupwizard"
)

is_protected() {
  local p="$1"
  for prot in "${PROTECTED_PKGS[@]}"; do
    [ "$p" = "$prot" ] && return 0
  done
  return 1
}

echo "=========================================="
echo "  Fire TV Stick 3rd Gen - Safe Debloat"
echo "  Fire OS 7.7.1.7 (ps7717/5741)"
if [ "$DRY_RUN" -eq 1 ]; then
  echo "  MODE: DRY RUN (no changes will be made)"
fi
echo "=========================================="

# ---------- [1/5] Connection ----------
echo ""
echo "[1/5] Checking ADB connection..."
if ! command -v adb >/dev/null 2>&1; then
  echo "ERROR: adb not found. Run scripts/install_adb.sh first."
  exit 1
fi
adb connect "${SERIAL}" >/dev/null 2>&1 || true
if ! adb -s "${SERIAL}" get-state >/dev/null 2>&1; then
  echo "ERROR: Fire TV not reachable at ${SERIAL}"
  echo "  - Is the TV on and on the same Wi-Fi?"
  echo "  - Is ADB Debugging enabled?"
  adb devices
  exit 1
fi
echo "Connected: ${SERIAL}"

# ---------- [2/5] Verify it's a Fire TV ----------
echo ""
echo "[2/5] Verifying device identity..."
MODEL="$(adb -s "${SERIAL}" shell getprop ro.product.model 2>/dev/null | tr -d '\r')"
ANDROID_VER="$(adb -s "${SERIAL}" shell getprop ro.build.version.release 2>/dev/null | tr -d '\r')"
SDK_VER="$(adb -s "${SERIAL}" shell getprop ro.build.version.sdk 2>/dev/null | tr -d '\r')"
FIREOS_VER="$(adb -s "${SERIAL}" shell getprop ro.build.version.name 2>/dev/null | tr -d '\r')"
echo "  Model:       ${MODEL:-unknown}"
echo "  Fire OS:     ${FIREOS_VER:-unknown}"
echo "  Android:     ${ANDROID_VER:-unknown} (SDK ${SDK_VER:-unknown})"

case "${MODEL}" in
  *AFT*|*Fire*|*fire*) : ;;
  *)
    echo "WARNING: Model '${MODEL}' does not look like a Fire TV."
    echo "         This script targets Amazon Fire TV devices only."
    read -r -p "Continue anyway? [y/N] " ans
    [ "${ans:-N}" = "y" ] || [ "${ans:-N}" = "Y" ] || { echo "Aborted."; exit 1; }
    ;;
esac

# ---------- [3/5] Load + validate list ----------
echo ""
echo "[3/5] Loading debloat list..."
if [ ! -f "${DEBLOAT_LIST}" ]; then
  echo "ERROR: list not found: ${DEBLOAT_LIST}"
  exit 1
fi

# Read installed packages once
INSTALLED="$(adb -s "${SERIAL}" shell pm list packages 2>/dev/null | tr -d '\r' | sed 's/^package://')"
if [ -z "${INSTALLED}" ]; then
  echo "ERROR: could not read installed packages."
  exit 1
fi

TOTAL_LIST=0
PRESENT=0
SKIPPED_PROTECTED=0
SKIPPED_ABSENT=0

# Build candidate list (only present + not protected)
CANDIDATES=()
while IFS= read -r line; do
  # strip comments / blanks / whitespace
  line="${line%%#*}"
  pkg="$(echo "${line}" | tr -d '[:space:]')"
  [ -z "${pkg}" ] && continue
  TOTAL_LIST=$((TOTAL_LIST + 1))

  if is_protected "${pkg}"; then
    echo "  PROTECTED (skipped): ${pkg}"
    SKIPPED_PROTECTED=$((SKIPPED_PROTECTED + 1))
    continue
  fi

  if echo "${INSTALLED}" | grep -qx "${pkg}"; then
    CANDIDATES+=("${pkg}")
    PRESENT=$((PRESENT + 1))
  else
    SKIPPED_ABSENT=$((SKIPPED_ABSENT + 1))
  fi
done < "${DEBLOAT_LIST}"

echo ""
echo "  In list:            ${TOTAL_LIST}"
echo "  Installed & safe:   ${PRESENT}"
echo "  Not on device:      ${SKIPPED_ABSENT}"
echo "  Protected:          ${SKIPPED_PROTECTED}"

if [ "${PRESENT}" -eq 0 ]; then
  echo ""
  echo "Nothing to disable. Exiting."
  exit 0
fi

# ---------- [4/5] Disable ----------
echo ""
echo "[4/5] Disabling ${PRESENT} packages..."
if [ "${DRY_RUN}" -eq 0 ]; then
  mkdir -p "${BACKUP_DIR}"
  {
    echo "# Fire TV debloat record - ${RUN_ID}"
    echo "# Model: ${MODEL} | Fire OS: ${FIREOS_VER} | SDK: ${SDK_VER}"
    echo "# Restore with: scripts/restore_debloat.sh"
  } > "${RECORD_FILE}"
fi

OK=0
FAIL=0
for pkg in "${CANDIDATES[@]}"; do
  if [ "${DRY_RUN}" -eq 1 ]; then
    echo "  [dry-run] would disable: ${pkg}"
    OK=$((OK + 1))
    continue
  fi

  out="$(adb -s "${SERIAL}" shell pm disable-user --user 0 "${pkg}" 2>&1 | tr -d '\r')"
  if echo "${out}" | grep -qi "new state: disabled"; then
    echo "  disabled: ${pkg}"
    echo "${pkg}" >> "${RECORD_FILE}"
    OK=$((OK + 1))
  else
    echo "  FAILED:   ${pkg}  (${out})"
    FAIL=$((FAIL + 1))
  fi
done

# ---------- [5/5] Summary ----------
echo ""
echo "[5/5] Summary"
echo "  Disabled: ${OK}"
echo "  Failed:   ${FAIL}"
if [ "${DRY_RUN}" -eq 0 ]; then
  echo "  Recovery record: ${RECORD_FILE}"
  echo ""
  echo "  To undo everything:"
  echo "    bash ${PROJECT_ROOT}/scripts/restore_debloat.sh"
fi
echo "=========================================="
