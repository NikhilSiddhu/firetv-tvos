#!/usr/bin/env bash
# Install the tvOS layer: canvasOS as the home screen + the HOME redirect that
# makes the Home button land on it (Amazon's launcher is a protected package and
# cannot be disabled, so it is routed around instead).
#
#   scripts/install_tvos_layer.sh <TV_IP[:5555]> <canvasOS.apk> [home-watcher.apk]
#
# Nothing is uninstalled from the TV, and scripts/uninstall_tvos_layer.sh undoes
# all of it.
set -euo pipefail

TV=${1:?usage: install_tvos_layer.sh <TV_IP[:5555]> <canvasOS.apk> [home-watcher.apk]}
CANVAS=${2:?path to the canvasOS APK}
WATCHER=${3:-dist/home-watcher-canvasos.apk}
SER=${TV%:5555}:5555
P=com.getisolated.canvasos
W=com.firetv.tvos

say() { printf '\n\033[1m%s\033[0m\n' "$*"; }
command -v adb >/dev/null || { echo "adb is required (brew install --cask android-platform-tools)"; exit 1; }
[ -f "$CANVAS" ] || { echo "no such APK: $CANVAS"; exit 1; }
[ -f "$WATCHER" ] || { echo "no such APK: $WATCHER"; exit 1; }

say "Connecting to $SER (accept the prompt on the TV)"
adb connect "$SER" >/dev/null 2>&1 || true
adb -s "$SER" wait-for-device
SDK=$(adb -s "$SER" shell getprop ro.build.version.sdk | tr -d '\r')
[ "$SDK" -ge 28 ] || { echo "canvasOS needs Android 9 (SDK 28) or newer; this TV reports $SDK"; exit 1; }

say "Installing canvasOS"
adb -s "$SER" install -r "$CANVAS"

say "Making it the home screen"
adb -s "$SER" shell cmd package set-home-activity "$P/.HomeActivity" || true

say "Granting the permissions only ADB can grant"
adb -s "$SER" shell pm grant "$P" android.permission.WRITE_SECURE_SETTINGS || true
adb -s "$SER" shell pm grant "$P" android.permission.READ_TV_LISTINGS || true
adb -s "$SER" shell cmd notification allow_listener "$P/$P.RevivalListener" >/dev/null 2>&1 || true
adb -s "$SER" shell appops set "$P" SYSTEM_ALERT_WINDOW allow || true

say "Switching on the tvOS look"
adb -s "$SER" shell am broadcast -a "$P.CONFIG" -n "$P/.ConfigReceiver" \
  --es focus_style tvos --es cc_style glass --es brand tvos \
  --ez intro true --es intro boot --ez intro_sound true >/dev/null 2>&1 || true

say "Installing the HOME redirect"
adb -s "$SER" install -r "$WATCHER"
adb -s "$SER" shell appops set "$W" SYSTEM_ALERT_WINDOW allow
adb -s "$SER" shell settings put global alarm_manager_constants min_futurity=0
adb -s "$SER" shell settings put secure enabled_accessibility_services \
  "$P/$P.HomeGuardService:$W/$W.HomeWatcherService"
adb -s "$SER" shell settings put secure accessibility_enabled 1

say "Opening the home screen"
adb -s "$SER" shell input keyevent KEYCODE_HOME
sleep 4
NOW=$(adb -s "$SER" shell dumpsys activity activities | grep -m1 ResumedActivity || true)
case "$NOW" in
  *"$P"*) echo "OK: $P is in front." ;;
  *)      echo "Amazon's launcher is still in front. Run scripts/healthcheck.sh $SER"; echo "$NOW" ;;
esac

cat <<EOF

Done. Press Back on the remote for the Control Center.

Next, optionally:
  scripts/healthcheck.sh $SER      # verify everything
  tools/make_tvos_faces.py         # Apple-style tile art for the rest of the apps
EOF
