#!/usr/bin/env bash
# Probe the TV for anything that could feed an Apple-TV-style "Up Next" / Continue Watching row.
#
# tvOS builds that row from data every streaming app hands the system. Android has two possible
# sources and Fire OS may expose neither, so measure before building anything:
#
#   1. AOSP's TV provider: content://android.media.tv/watch_next_program  (what Google TV uses)
#   2. Amazon's own home/recommendation provider, which the stock Fire TV launcher reads for its
#      "Recent" row. Third-party reads may be signature-gated.
#
# Run with the TV reachable (ADB debugging on):
#   ./tools/probe_upnext.sh 192.168.1.41:5555
set -u

HOST="${1:-192.168.1.41:5555}"
ADB="adb -s $HOST"

say() { printf '\n\033[1m== %s\033[0m\n' "$*"; }
row() { printf '  %-28s %s\n' "$1" "$2"; }

if ! $ADB get-state >/dev/null 2>&1; then
  echo "TV not reachable at $HOST — turn ADB debugging on first." >&2
  exit 1
fi

say "1. AOSP TV provider (Google TV's watch-next source)"
printf '  package: %s\n' "$($ADB shell pm list packages 2>/dev/null | tr -d '\r' | grep -c 'providers.tv')"
$ADB shell pm list packages 2>/dev/null | tr -d '\r' | grep -E 'providers\.tv|media\.tv' | sed 's/^/  /'

say "2. does watch_next_program answer?"
$ADB shell content query --uri content://android.media.tv/watch_next_program 2>&1 | head -8 | sed 's/^/  /'

say "3. Amazon home / recommendation providers"
$ADB shell dumpsys activity providers 2>/dev/null \
  | grep -iE 'provider\{|authority' | tr -d '\r' \
  | grep -iE 'amazon|home|recommend|watch|recent' | head -20 | sed 's/^/  /'

say "4. any provider whose authority mentions home/tv/watch (full list)"
$ADB shell dumpsys activity providers 2>/dev/null \
  | grep -oE 'authority=[^ ;}]+' | tr -d '\r' | sort -u \
  | grep -iE 'home|watch|tv\.|media|recommend|amazon' | head -30 | sed 's/^/  /'

say "5. Fire OS launcher packages still enabled (the stock Recent row lives in one of these)"
for p in com.amazon.tv.launcher com.amazon.device.home com.amazon.firehomestarter com.amazon.tv.recommendations; do
  st=$($ADB shell pm list packages -e 2>/dev/null | tr -d '\r' | grep -c "^package:$p$")
  row "$p" "$([ "$st" = 1 ] && echo enabled || echo 'missing or disabled')"
done

say "6. can a third-party app see the launcher's providers? (permission check)"
$ADB shell dumpsys package com.amazon.tv.launcher 2>/dev/null \
  | grep -iE 'provider|readPermission|writePermission|grantUriPermission' | head -20 | sed 's/^/  /'

say "7. Android version / TvProvider availability"
row "sdk" "$($ADB shell getprop ro.build.version.sdk | tr -d '\r')"
row "has tv feature" "$($ADB shell pm list features 2>/dev/null | tr -d '\r' | grep -c 'android.software.leanback')"
row "live tv" "$($ADB shell pm list features 2>/dev/null | tr -d '\r' | grep -c 'android.hardware.type.television')"

cat <<'EOF'

How to read this:
  * Step 2 prints rows  -> a real Up Next row is possible from app-published data.
  * Step 2 prints nothing, but step 3/4 find an Amazon provider -> try reading it; it may need a
    permission a sideloaded app cannot get.
  * Both empty -> no streaming app on Fire TV publishes watch history to Android, so a true
    Continue Watching shelf cannot be built. The fallback is a "Recently opened" row, which the
    launcher already tracks itself.
EOF
