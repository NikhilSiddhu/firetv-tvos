# Fire TV Stick → Apple TV-style home

A complete, reversible rewrite of the **front end** of an Amazon Fire TV Stick: Amazon's
ad-filled launcher is bypassed, and the TV opens on an Apple TV-style home screen you can
rearrange from the remote.

Built and tested on a **Fire TV Stick 3rd gen (AFTSSS)**, **Fire OS 7.7.1.7 (PS7717/5741)**,
Android 9 / SDK 28, 1 GB RAM.

---

## What this is, and what it is not

**Is:** a new home screen, a debloated system, and a redirect that makes the HOME button land on
your launcher instead of Amazon's.

**Is not:** a new operating system. Fire TV's bootloader is locked and signed by Amazon; nothing
can be flashed over Wi-Fi. The Amazon launcher also cannot be disabled (`pm disable-user` refuses
it — it is a *protected package*), so it stays installed and we route around it.

---

## The four pieces

| Piece | Package | What it does |
|---|---|---|
| **Launcher** | `com.gathin.tvhome` | The Apple TV-style home. From [cleanyourtv](https://github.com/Gathin23/cleanyourtv), built from source (477 KB). |
| **Home watcher** | `com.firetv.tvos` | Our own app. Catches Amazon's home appearing and puts ours in front. This is the piece that makes HOME work. |
| **Web Tiles** | `com.firetv.webtiles` | Our own app. Add any web address as a tile, with the icon fetched from the site. |
| **Debloat list** | `scripts/debloat_fireos.txt` | ~71 Amazon packages disabled, based on the cleanyourtv list for this exact Fire OS build. |

---

## Quick start

```bash
# one-time: adb
brew install --cask android-platform-tools

# on the TV: Settings > My Fire TV > About > press OK on the name 7x
#            > Developer Options > ADB debugging ON

adb connect 192.168.1.41:5555      # accept the prompt on the TV

bash scripts/install_all.sh        # does everything below, in order
```

Prefer step by step?

```bash
bash scripts/connect_adb.sh        # 1. connect
bash scripts/debloat_fireos.sh     # 2. disable Amazon bloat (reversible)
bash scripts/install_all.sh        # 3. launcher + watcher + apps + theme
```

---

## The hard part: making HOME work

This is the bit every guide gets wrong, so it is worth writing down.

Fire OS 7 blocks the obvious approaches:

- `pm disable-user com.amazon.tv.launcher` → **"Cannot disable a protected package"**
- `pm disable-user com.amazon.firehomestarter` → same
- `cmd package set-home-activity com.gathin.tvhome/.MainActivity` → returns *Success*, but Amazon's
  launcher still wins HOME (its intent filter has priority 950 and firehomestarter re-asserts it)
- Filtering `KEYCODE_HOME` in an accessibility service → Fire OS handles HOME **before** any
  accessibility key filter runs

So the watcher does this:

1. An accessibility service watches for `com.amazon.tv.launcher` reaching the foreground.
2. It covers the screen with a black overlay so Amazon's home is never seen.
3. It fires an **AlarmManager alarm whose PendingIntent is the launcher activity itself**.
4. The alarm is started by `system_server`, which is **exempt** from Fire OS's
   `APP_SWITCH_DELAY_TIME` — a ~5 second hold applied to app launches that follow HOME.
5. The cover lifts once the launcher is up.

**Point 3 is the whole trick.** If you wake your own `BroadcastReceiver` and call `startActivity`
from it, the launch is attributed to *your* uid and the 5 second hold applies again — you get the
classic "Amazon home for five seconds, then my launcher". Pointing the alarm straight at the
activity makes `system_server` do the launch.

Two settings matter:

```bash
adb shell settings put global alarm_manager_constants min_futurity=0
adb shell appops set com.firetv.tvos SYSTEM_ALERT_WINDOW allow
```

**Measured on this stick:** HOME → launcher in **175–290 ms**, no Amazon frames visible.

### The second trap: Settings lives in the same package

The Amazon launcher package also hosts the TV's real Settings screen
(`com.amazon.tv.launcher.ui.MainSettingsActivity`). A watcher that redirects on *any* window from
`com.amazon.tv.launcher` therefore makes Fire TV Settings impossible to open — you press Settings
and get bounced home. The watcher checks the window's class name and only redirects when it looks
like a home screen (`HomeActivity`, `FireHomeStarter`). Everything else in that package is left
alone.

`com.amazon.tv.settings.v2` is a **stub** on this build (all its activities are `CTSDummy*`), so
`android.settings.SETTINGS` goes nowhere useful. `MainSettingsActivity` is the one that works.

---

## Where everything lives

| I want to… | How |
|---|---|
| **Fire TV Settings** (network, display, apps, account, accessibility) | `com.amazon.tv.launcher/.ui.MainSettingsActivity` — reachable from the launcher's Settings page |
| **Launcher settings** (rows, dock opacity, motion) | Top-bar **home icon** button, or hold OK on Settings |
| **Reorder tiles** | Top-bar **↑↓** button, or hold OK on a tile → Move |
| **Add/remove apps from Home** | Top-bar **grid** button (App library), or hold OK on a tile → Remove from Home |
| **Rename an app's tile** | theme `app_labels`: `["com.foo=My Name"]` |
| **See what's installed** | `adb shell pm list packages -3` |

```bash
adb shell am start -n com.amazon.tv.launcher/.ui.MainSettingsActivity   # Fire TV Settings
adb shell am start -n com.gathin.tvhome/.LauncherSettingsActivity       # launcher settings
```

---

## Prime Video with a different account

Fire TV's Prime Video (`com.amazon.firebat`) is **bound to the device's registered Amazon
account**. There is no supported way to sign it into a different account on its own:

- There is no in-app "sign in as someone else" — it uses the device registration.
- `com.amazon.avod` (the standalone Prime Video app, which *can* hold its own session) is not
  installed on this build, and on Fire TV it still defers to the device account.

The two things that actually work:

1. **Amazon Household** (recommended, no risk) — Settings → Account & Profile Settings → Amazon
   Household, and link the second Amazon account. Both accounts then get Prime benefits on this
   device, and you can switch **Prime Video profiles** with the profile switcher in the app.
2. **Deregister and re-register** — Settings → My Fire TV → Deregister, then sign in with the other
   account. This changes the account for *everything* (Appstore, Alexa, Prime Video), not just
   Prime Video. Nothing is lost, but you sign in again everywhere.

Rebooting does not change the registration, and nothing in this project touches it — the account
list still shows the original account after a reboot.


---

## On-TV controls

Everything is editable from the remote. No ADB, no recompiling.

| Action | Does |
|---|---|
| **Hold OK on a tile** | Menu: Move, Remove from Home, App info |
| **Top-bar ↑↓ button** | Reorder tiles |
| **Top-bar grid button** | App library — add or remove apps from Home |
| **Top-bar home button** | Launcher settings |
| **Hold OK on Settings** | Launcher settings |
| **Move mode** | Arrows carry the tile, Back puts it down |

---

## Web Tiles — your own shortcuts

Open **Web Tiles** on the home screen.

- **+ Add** → type a **name** and a **web address**. The icon is fetched from the site
  automatically (its `/favicon.ico`, then Google's favicon service as a fallback).
- The **icon address** field is optional — use it to force a specific picture.
- **OK** opens the site full-screen; **Back** returns.
- **Long-press** a tile to edit or delete it.

Tiles live in a plain JSON file, so a script or a home server can manage them too:

```
/sdcard/Android/data/com.firetv.webtiles/files/tiles.json
```

```json
[
  { "name": "YouTube",  "url": "https://youtube.com",  "icon": "" },
  { "name": "Wikipedia","url": "https://wikipedia.org", "icon": "" }
]
```

```bash
adb push tiles.json /sdcard/Android/data/com.firetv.webtiles/files/tiles.json
```

---

## Themes and configuration

The launcher reads `config.json` at
`/sdcard/Android/data/com.gathin.tvhome/files/config.json` as an overlay over its built-in
settings, so the look changes without rebuilding anything.

```bash
bash tools/theme.sh push appletv     # apply the Apple TV theme
bash tools/theme.sh list             # what is available
```

The shipped theme (`themes/appletv/config.json`):

| Key | Value | Why |
|---|---|---|
| `dock_apps` | Netflix, Prime Video, SmartTube, Apple TV | the four majors |
| `fill_dock` | false | no filler apps |
| `cinematic_home` | true | the Apple TV top shelf: artwork, big name, "Last opened", dock dots |
| `columns` / `rows_below_dock` | 5 / 2 | tile density |
| `dock_glass`, `dock_opacity` | true, 85 | frosted dock band |
| `icon_only_buttons` | true | round Wi-Fi / Settings pills |
| `app_library`, `library_button` | true | add/remove apps on TV |
| `tile_menu`, `reorder_button` | true | move/remove tiles on TV |
| `launcher_settings_button` | true | settings from the home bar |
| `show_stats` | false | CPU/RAM line off (turn on if you want it) |
| `ambient_glow`, `app_glow`, `glow_style` | true, true, radial | the colour glow from the focused app |
| `animations`, `advanced_effects` | true, true | fluid motion |
| `reduced_motion` | false | *true* makes it calmer but reads as "sticky" |
| `focus_overshoot` | true | the Apple TV spring on focus |
| `home_idle_clock_minutes` | 5 | drifting clock screensaver |

---

## Apps installed

| App | Package | Source |
|---|---|---|
| Netflix, Prime Video, Apple TV, JioHotstar, SonyLIV, Airtel Xstream, MX Player, Luna | preinstalled | re-enabled after the debloat |
| **SmartTube** | `org.smarttube.stable` | GitHub — ad-free YouTube |
| **Kodi** | `org.xbmc.kodi` | kodi.tv |
| **Jellyfin** | `org.jellyfin.androidtv` | GitHub |
| **VLC** | `org.videolan.vlc` | videolan.org (32-bit build) |
| **Web Tiles** | `com.firetv.webtiles` | this repo |
| **Settings** | `com.firetv.settings` | this repo — a tile that opens Fire TV Settings |

### App stores on the TV

| Store | Package | What it has |
|---|---|---|
| **Amazon Appstore** | `com.amazon.venezia` | every commercial TV app: Netflix, Disney+, ZEE5, Tubi, Pluto TV, Plex… (preinstalled) |
| **Aurora Store** | `com.aurora.store` | an open-source client for **Google Play** — the largest catalogue. Sign in anonymously. |
| **F-Droid** | `org.fdroid.fdroid` | thousands of open-source apps |

All three are on the home screen. Between them you can install essentially anything that exists for
Android TV without touching a computer.

**Not installed, deliberately:** piracy APKs (Cinejoy and similar) that unlock paid catalogues. They
are copyright infringement and a common malware vector on a device that holds your Amazon account.
Everything listed above is legitimate.

**A note on 32-bit:** this stick is `armeabi-v7a`, so 64-bit-only APKs fail with
`INSTALL_FAILED_NO_MATCHING_ABIS` (VLC's F-Droid build did). Always take the `armeabi-v7a` build.

---

## The Settings tile

Fire OS answers the standard `android.settings.SETTINGS` action with a **stub**
(`com.amazon.tv.settings.v2` is all `CTSDummy*` activities), so the real menu has to be started by
component: `com.amazon.tv.launcher/.ui.MainSettingsActivity`.

`com.firetv.settings` is a 12 KB app that does exactly that and disappears — a one-tap Settings
button sitting on the Apple TV home screen next to your apps.

### Why not a remote button

The launcher supports `settings_key_keycodes` and `app_keys` (with `HomeKeyService` /
`InputKeyService`), but the Fire TV Stick remote has **no spare key**:

- **Menu (☰)** is already consumed by the launcher's tile menu.
- **Home, Back, D-pad, Select, Play/Pause, Rewind, FF** are all in use.
- **Alexa** is the voice button.
- There is no gear button (that is a TCL Google TV remote thing).

Mapping Menu was tried: it opened the launcher's own popup instead, because the launcher claims
that key first. So the tile is the answer — it is one press from Home and it cannot break anything.
Use the top-bar **↑↓** button to move it wherever you want it.

---

## The dock caps at five

`dock_apps` can list more, but the dock row follows `columns`, so with `columns: 5` the sixth entry
is dropped. To get six in the dock, raise `columns` to 6 (tiles shrink) — otherwise keep the dock at
five and let the rest sit in the grid.



---

## Undo

```bash
bash scripts/restore_debloat.sh                                    # packages back
adb shell settings put secure enabled_accessibility_services ""    # redirect off
adb uninstall com.firetv.tvos com.firetv.webtiles com.gathin.tvhome
adb shell settings put global alarm_manager_constants ""           # alarm setting back
```

A factory reset also removes all of it.

---

## Security note

Wireless ADB on port 5555 is plaintext and unauthenticated once authorised. When you are finished,
turn it off:

```bash
adb shell settings put global adb_enabled 0
```

---

## Credits

- [cleanyourtv](https://github.com/Gathin23/cleanyourtv) — the launcher, the debloat lists, and the
  Fire TV example this list is based on.
- [dumbtv](https://github.com/humblemuzzu/dumbtv) — whose README documents the AlarmManager
  exemption from Fire OS's app-switch hold.
- [SmartTube](https://github.com/yuliskov/SmartTube) — ad-free YouTube for TV.

Fire TV, Fire OS, Alexa and Prime Video are trademarks of Amazon. This project is not affiliated
with or endorsed by Amazon or Apple. Use on hardware you own, at your own risk.
