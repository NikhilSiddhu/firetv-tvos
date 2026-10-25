#!/usr/bin/env bash
# Read-only check of a box running the tvOS layer. Changes nothing.
#
#   scripts/healthcheck.sh <TV_IP[:5555]>
set -uo pipefail

TV=${1:?usage: healthcheck.sh <TV_IP[:5555]>}
SER=${TV%:5555}:5555
P=com.getisolated.canvasos
W=com.firetv.tvos
A() { adb -s "$SER" shell "$@" 2>/dev/null | tr -d '\r'; }

adb connect "$SER" >/dev/null 2>&1 || true
adb -s "$SER" wait-for-device || { echo "cannot reach $SER"; exit 1; }

row() { printf '%-34s %s\n' "$1" "$2"; }
echo "Device: $(A getprop ro.product.model) · Android $(A getprop ro.build.version.release)"
echo

row "canvasOS installed"      "$(A pm path $P >/dev/null && echo yes || echo NO)"
row "  version"              "$(A dumpsys package $P | grep -m1 versionName | sed 's/.*=//')"
row "watcher installed"       "$(A pm path $W >/dev/null && echo yes || echo NO)"
row "watcher process"         "$(A ps -A | grep -q $W && echo running || echo NOT RUNNING)"
row "watcher boot receiver"   "$(A dumpsys package $W | grep -q BOOT_COMPLETED && echo registered || echo MISSING)"
row "accessibility services"  "$(A settings get secure enabled_accessibility_services)"
row "  accessibility enabled" "$(A settings get secure accessibility_enabled)"
row "alarm min_futurity"      "$(A settings get global alarm_manager_constants)"
row "overlay (watcher)"       "$(A appops get $W SYSTEM_ALERT_WINDOW | tail -1)"
row "overlay (canvasOS)"      "$(A appops get $P SYSTEM_ALERT_WINDOW | tail -1)"
row "WRITE_SECURE_SETTINGS"   "$(A dumpsys package $P | grep -q WRITE_SECURE_SETTINGS && echo granted || echo NOT granted)"
row "READ_TV_LISTINGS"        "$(A dumpsys package $P | grep -q READ_TV_LISTINGS && echo granted || echo NOT granted)"
row "animation scales"        "$(A settings get global window_animation_scale) $(A settings get global transition_animation_scale) $(A settings get global animator_duration_scale)"
row "tile art"                "$(A ls /sdcard/Android/data/$P/files/tiles/ 2>/dev/null | tr '\n' ' ')"
row "stock YouTube"           "$(A pm list packages -d | grep -q com.amazon.firetv.youtube && echo 'disabled' || echo 'enabled')"
echo

echo "Look / state"
A am broadcast -a "$P.CONFIG" -n "$P/.ConfigReceiver" | grep -o 'data="[^"]*"' | tr ' ' '\n' |
  grep -E '^(guard|keep_adb|focus_style|cc_style|brand|intro|low_end|listener|overlay|dock_recents|background)=' || true
echo

echo "Crashes (crash buffer)"
A logcat -d -b crash | grep -E 'FATAL|canvasos|HomeWatcher' | tail -5 || true
echo "(empty means none)"
echo

echo "HOME button"
A input keyevent KEYCODE_HOME
sleep 2
FRONT=$(A dumpsys activity activities | grep -m1 ResumedActivity)
case "$FRONT" in
  *"$P"*) echo "OK: lands on canvasOS" ;;
  *)      echo "PROBLEM: $FRONT" ;;
esac
