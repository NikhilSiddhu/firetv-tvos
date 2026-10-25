# canvasOS on the Fire TV Stick — how this box is set up

Final state of the AFTSSS ("sheldonp", Fire OS 7.7.1.7 / Android 9, 1 GB RAM).

## What is installed

| Piece | Package | Notes |
|---|---|---|
| Home screen | `com.getisolated.canvasos` | **canvasOS 1.2.0, English build** (`dist/canvasOS-1.2.0-english.apk`) |
| Home watcher | `com.firetv.tvos` | Our app, rebuilt to point at canvasOS (`dist/home-watcher-canvasos.apk`) |
| SmartTube | `org.smarttube.stable` | Stock YouTube (`com.amazon.firetv.youtube`) is `disable-user` |
| Prime, Netflix, JioHotstar, Apple TV | — | in the dock, order set on the TV |

## Why the English build exists

Upstream canvasOS ships French only (all UI text is hardcoded in Kotlin, ~975
strings, `locales: '--_--'`). To get English we build from source:

- `canvasos-src/` — upstream `getisolated/canvasOS`, translated to English
  (UI strings, `strings.xml`, manifest labels, phone page HTML), with
  `Locale.FRANCE` → `Locale.US`, Bing `mkt=en-US`, Open-Meteo/ TMDB `en`.
- Signed with a **local key** (`keystore.properties` at the repo root,
  password in that file). Consequence: Settings → Update cannot install
  upstream releases — rebuild and `adb install -r` instead.

Rebuild:

```bash
cd canvasos-src
export JAVA_HOME=/opt/homebrew/opt/openjdk@17 ANDROID_HOME=$HOME/Android/sdk
./gradlew assembleStandardRelease
# -> app/build/outputs/apk/standard/release/app-standard-release.apk
```

## Why HOME works (the part that is easy to get wrong)

Fire OS protects `com.amazon.tv.launcher` and `com.amazon.firehomestarter`, so
`pm disable-user` refuses them and `cmd package set-home-activity` says
*Success* while Amazon's launcher still wins. Our watcher covers Amazon's home
with a black overlay and fires an **activity PendingIntent through
AlarmManager**, so `system_server` performs the launch and escapes the ~5 s
post-HOME `APP_SWITCH_DELAY_TIME` hold. Measured here: ~350 ms.

```bash
adb shell settings put global alarm_manager_constants min_futurity=0
adb shell appops set com.firetv.tvos SYSTEM_ALERT_WINDOW allow
adb shell settings put secure enabled_accessibility_services \
  com.getisolated.canvasos/com.getisolated.canvasos.HomeGuardService:com.firetv.tvos/com.firetv.tvos.HomeWatcherService
```

## Grants canvasOS needs over ADB

```bash
P=com.getisolated.canvasos
adb shell pm grant $P android.permission.WRITE_SECURE_SETTINGS
adb shell pm grant $P android.permission.READ_TV_LISTINGS
adb shell cmd notification allow_listener $P/$P.RevivalListener
adb shell appops set $P SYSTEM_ALERT_WINDOW allow
```

## Look

```bash
adb shell am broadcast -a com.getisolated.canvasos.CONFIG -n com.getisolated.canvasos/.ConfigReceiver \
  --es focus_style tvos --es cc_style glass --es brand tvos --es intro boot --ez intro_sound true
```

Tile art (16:9, 800×450 JPEG, one file per package):

```
/sdcard/Android/data/com.getisolated.canvasos/files/tiles/<package>.jpg
```

`tools/make_tvos_faces.py` (needs `.imgvenv`) draws dark-glass tvOS-style faces
for any set of APKs; `dist/youtube-tile-org.smarttube.stable.jpg` is the
SmartTube one.

## Undo

```bash
adb shell pm enable com.amazon.firetv.youtube          # stock YouTube back
adb shell pm uninstall com.firetv.tvos                # stop the HOME redirect
adb shell pm uninstall com.getisolated.canvasos       # back to Amazon's home
```
