#!/usr/bin/env bash
# Remove the tvOS layer and hand the screen back to Amazon's launcher.
#
#   scripts/uninstall_tvos_layer.sh <TV_IP[:5555]>
#
# Removes the HOME redirect first (so nothing fights you while the rest is
# undone), then canvasOS. Apps, accounts and the TV's own settings are untouched.
set -uo pipefail

TV=${1:?usage: uninstall_tvos_layer.sh <TV_IP[:5555]>}
SER=${TV%:5555}:5555
P=com.getisolated.canvasos
W=com.firetv.tvos
A() { adb -s "$SER" shell "$@" 2>/dev/null | tr -d '\r'; }

adb connect "$SER" >/dev/null 2>&1 || true
adb -s "$SER" wait-for-device || { echo "cannot reach $SER"; exit 1; }

echo "Stopping the HOME redirect"
A settings put secure enabled_accessibility_services "$P/$P.HomeGuardService"
A pm uninstall "$W"
A pm enable com.amazon.tv.launcher >/dev/null 2>&1 || true
A pm enable com.amazon.firehomestarter >/dev/null 2>&1 || true
A settings delete global alarm_manager_constants >/dev/null 2>&1 || true

echo "Restoring stock YouTube (if it was disabled)"
A pm enable com.amazon.firetv.youtube >/dev/null 2>&1 || true

echo "Removing canvasOS"
A am force-stop "$P"
A pm uninstall "$P"

echo "Back to the default launcher"
A cmd package set-home-activity com.amazon.tv.launcher/.ui.HomeActivity_vNext >/dev/null 2>&1 || true
A input keyevent KEYCODE_HOME
sleep 2

FRONT=$(A dumpsys activity activities | grep -m1 ResumedActivity)
case "$FRONT" in
  *amazon.tv.launcher*) echo "OK: Amazon's launcher is back." ;;
  *) echo "Home activity now: $FRONT"
     echo "If the screen looks wrong, press Home on the remote, or reboot the TV." ;;
esac
