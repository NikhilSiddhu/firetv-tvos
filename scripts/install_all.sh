#!/bin/bash
# ============================================================
#  Fire TV Stick -> Apple TV-style home : one-command installer
# ------------------------------------------------------------
#  Target: Amazon Fire TV Stick 3rd gen (AFTSSS), Fire OS 7.7.1.7
#  Run from the project root:  bash scripts/install_all.sh
#
#  Everything here is reversible:
#    scripts/restore_debloat.sh   undoes the package changes
#    adb uninstall <pkg>          removes an app we installed
#    settings put secure enabled_accessibility_services ""   turns off the redirect
# ============================================================
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TV_IP="${TV_IP:-192.168.1.41}"
SERIAL="${TV_IP}:5555"
DIST="$ROOT/dist"
THEME="$ROOT/themes/appletv"
LAUNCHER_DIR="$ROOT/../cleanyourtv/launcher"
LAUNCHER_DATA="/sdcard/Android/data/com.gathin.tvhome/files"

say() { printf '\n=== %s ===\n' "$1"; }

say "1/9  Checking adb and the TV"
command -v adb >/dev/null 2>&1 || { echo "adb not found. Install Android platform-tools first."; exit 1; }
adb connect "$SERIAL" >/dev/null 2>&1 || true
if ! adb -s "$SERIAL" get-state >/dev/null 2>&1; then
  echo "TV not reachable at $SERIAL."
  echo "  - TV on, same Wi-Fi, ADB debugging enabled?"
  adb devices
  exit 1
fi
MODEL="$(adb -s "$SERIAL" shell getprop ro.product.model | tr -d '\r')"
FIREOS="$(adb -s "$SERIAL" shell getprop ro.build.version.name | tr -d '\r')"
echo "  $MODEL / $FIREOS"

say "2/9  Installing the Apple TV-style launcher"
if [ -f "$DIST/tvhome-launcher.apk" ]; then
  adb -s "$SERIAL" install -r "$DIST/tvhome-launcher.apk" | tail -1
elif [ -d "$LAUNCHER_DIR" ]; then
  echo "  no prebuilt APK; building from cleanyourtv source"
  ( cd "$LAUNCHER_DIR" && ./gradlew --no-daemon assembleRelease ) || { echo "build failed"; exit 1; }
  adb -s "$SERIAL" install -r "$LAUNCHER_DIR/app/build/outputs/apk/release/app-release.apk" | tail -1
else
  echo "  missing $DIST/tvhome-launcher.apk and the cleanyourtv source"; exit 1
fi

say "3/9  Installing the HOME redirect watcher"
adb -s "$SERIAL" install -r "$DIST/home-watcher.apk" | tail -1

say "4/9  Installing Web Tiles (your own web shortcuts as tiles)"
adb -s "$SERIAL" install -r "$DIST/web-tiles.apk" | tail -1

say "5/9  Installing the free apps, stores and the Settings tile"
for apk in "$DIST"/SmartTube-*.apk "$DIST"/kodi-*.apk "$DIST"/jellyfin-*.apk \
           "$DIST"/VLC-*.apk "$DIST"/AuroraStore.apk "$DIST"/F-Droid.apk "$DIST"/settings-tile.apk; do
  [ -f "$apk" ] || continue
  echo "  $(basename "$apk")"
  adb -s "$SERIAL" install -r "$apk" | tail -1
done

say "6/9  Debloating (reversible; recovery record in ~/.cleanyourtv)"
bash "$ROOT/scripts/debloat_fireos.sh"

say "7/9  Wiring the HOME redirect"
# The watcher needs: the accessibility service on, the overlay grant, and the
# alarm setting that removes AlarmManager's own minimum delay.
adb -s "$SERIAL" shell settings put secure enabled_accessibility_services \
    com.firetv.tvos/com.firetv.tvos.HomeWatcherService
adb -s "$SERIAL" shell settings put secure accessibility_enabled 1
adb -s "$SERIAL" shell appops set com.firetv.tvos SYSTEM_ALERT_WINDOW allow
adb -s "$SERIAL" shell settings put global alarm_manager_constants min_futurity=0
# Make the launcher the resolved HOME as far as the system will allow.
adb -s "$SERIAL" shell cmd package set-home-activity com.gathin.tvhome/.MainActivity >/dev/null 2>&1 || true
echo "  redirect configured"

say "8/9  Pushing the Apple TV theme"
adb -s "$SERIAL" shell mkdir -p "$LAUNCHER_DATA" 2>/dev/null
adb -s "$SERIAL" push "$THEME/config.json" "$LAUNCHER_DATA/config.json" | tail -1

say "9/9  Starting the new home"
adb -s "$SERIAL" shell am force-stop com.gathin.tvhome 2>/dev/null
sleep 2
adb -s "$SERIAL" shell am start -n com.gathin.tvhome/.MainActivity >/dev/null 2>&1
sleep 6
adb -s "$SERIAL" shell screencap -p /sdcard/installed.png 2>/dev/null
adb -s "$SERIAL" pull /sdcard/installed.png "$ROOT/shots/installed.png" >/dev/null 2>&1
adb -s "$SERIAL" shell rm -f /sdcard/installed.png

cat <<'DONE'

============================================================
 Done. Press HOME on the remote - you should land on the
 Apple TV-style home (about 0.2-0.9 s of black, then it).

 On-TV controls:
   Hold OK on a tile      Move / Remove from Home / App info
   Top-bar Reorder button  rearrange tiles
   Top-bar grid button     App library (add/remove apps)
   Top-bar home button     launcher settings
   Hold OK on Settings     launcher settings too

 To undo everything:
   bash scripts/restore_debloat.sh
   adb shell settings put secure enabled_accessibility_services ""
============================================================
DONE
