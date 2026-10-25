#!/usr/bin/env bash
# Put the Liquid Glass look on the TV: newer launcher + the theme + its wallpapers.
#
#   ./scripts/apply_liquidglass.sh 192.168.1.41:5555
#
# Safe to re-run. The launcher is installed with -r, so the home layout, the App library's
# choices and the reorder you did on the TV survive. The previous APK stays in dist/ if you
# ever want to go back.
set -u

HOST="${1:-192.168.1.41:5555}"
ADB="adb -s $HOST"
PKG=com.gathin.tvhome
DIR=/sdcard/Android/data/$PKG/files

HERE="$(cd "$(dirname "$0")/.." && pwd)"
APK="$HERE/dist/tvhome-launcher-2.7-liquid.apk"
THEME="$HERE/themes/liquidglass"

say() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

if ! $ADB get-state >/dev/null 2>&1; then
  echo "TV not reachable at $HOST." >&2
  echo "On the TV: Settings -> My TV -> Developer Options -> ADB debugging ON" >&2
  exit 1
fi
[ -f "$APK" ] || { echo "missing $APK — build it first:" >&2
  echo "  cd cleanyourtv-latest/launcher && ./gradlew assembleRelease" >&2; exit 1; }

say "1. Installing the newer launcher (383 commits ahead, keeps app data)"
$ADB install -r "$APK" 2>&1 | tail -1

say "2. Pushing the Liquid Glass theme"
$ADB shell mkdir -p "$DIR/wallpapers"
$ADB push "$THEME/config.json" "$DIR/config.json" 2>&1 | tail -1
$ADB shell "rm -f $DIR/wallpapers/*.jpg"
for f in "$THEME"/wallpapers/*.jpg; do
  $ADB push "$f" "$DIR/wallpapers/$(basename "$f")" 2>&1 | tail -1
done

say "3. Restarting Home"
$ADB shell am force-stop $PKG
sleep 2
$ADB shell am start -n $PKG/.MainActivity >/dev/null 2>&1
sleep 9

say "4. What is on screen"
echo "  $($ADB shell dumpsys window 2>/dev/null | grep -i mCurrentFocus | sed 's/.*u0 //' | tr -d '}')"

say "5. Screenshot"
$ADB shell screencap -p /sdcard/liquidglass.png 2>/dev/null
$ADB pull /sdcard/liquidglass.png "$HERE/shots/32_liquidglass.png" 2>&1 | tail -1
$ADB shell rm -f /sdcard/liquidglass.png
