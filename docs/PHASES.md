# Fire TV Stick "tvOS" Customization - Phase Guide

## Your Device Context
- **Device**: Amazon Fire TV Stick 3rd Gen (1080p)
- **Fire OS**: 7.7.1.7 (ps7717/5741)
- **Fire TV Home**: 7320373.1
- **Serial**: GEB1TX2234250489
- **IP**: 192.168.1.41
- **MAC**: E8d87edd1b34
- **Host**: Mac M5 Air

---

## Phase 1: ADB Wireless Connection & Authorization

### Step 1: Install ADB on Mac M5 Air

```bash
# If Homebrew is installed:
brew install --cask android-platform-tools

# Or manual install:
# 1. Download from: https://developer.android.com/studio/releases/platform-tools
# 2. Unzip to /usr/local/bin
# 3. Run: adb version
```

### Step 2: Enable ADB Debugging on Fire TV

1. On Fire TV Stick: **Settings → Device Preferences → About**
2. Press **OK** on **Build** seven times
3. Go back → **Developer options**
4. Enable **ADB Debugging**
5. Enable **Network/ADB debugging** if available
6. Keep TV powered on

### Step 3: Connect via Wi-Fi ADB

```bash
adb connect 192.168.1.41:5555
```

- Approve "Allow USB debugging?" on TV screen
- Verify: `adb devices` should show `192.168.1.41:5555 device`

---

## Phase 2: Targeted Amazon Fire OS Debloat

### Step 1: Run Debloat Script

```bash
bash /Users/nikhilsiddhu/OpenCode/firetv-tvos/scripts/debloat_fireos.sh
```

### Step 2: Run Backup First (Recommended)

```bash
bash /Users/nikhilsiddhu/OpenCode/firetv-tvos/scripts/backup.sh
```

### Step 3: Restore if Needed

```bash
bash /Users/nikhilsiddhu/OpenCode/firetv-tvos/scripts/restore_debloat.sh
```

---

## Phase 3: Sideloading & Forcing Apple TV Launcher

### Step 1: Install Launcher

```bash
bash /Users/nikhilsiddhu/OpenCode/firetv-tvos/scripts/install_launcher.sh
```

### Step 2: Setup Accessibility Service

```bash
bash /Users/nikhilsiddhu/OpenCode/firetv-tvos/scripts/setup_accessibility.sh
```

### Step 3: Force Home Override

The AccessibilityService intercepts window state changes from `com.amazon.tv.launcher` and forces the Apple TV launcher.

---

## Phase 4: Cloud & Local Theme Automation

### Step 1: Push Theme

```bash
bash /Users/nikhilsiddhu/OpenCode/firetv-tvos/tools/theme.sh push default
```

### Step 2: Push Custom Config

```bash
bash /Users/nikhilsiddhu/OpenCode/firetv-tvos/tools/theme.sh dynamic '{"dock_apps": [...], "grid_columns": 5}'
```

### Step 3: Toggle Stats

```bash
bash /Users/nikhilsiddhu/OpenCode/firetv-tvos/tools/theme.sh stats true
```

---

## Important Fire OS Notes

1. **Fire OS limitation**: Fire OS will NOT hand Home to third-party launchers automatically
2. **Solution**: AccessibilityService is required to intercept Home button
3. **No root**: We use `pm disable-user --user 0` (requires ADB debugging, no root)
4. **Firmware updates**: Will undo debloat changes - use `tools/check.py` to reapply

---

*This completes the phase documentation for Fire TV Stick 3rd Gen.*
