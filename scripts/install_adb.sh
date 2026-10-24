#!/bin/bash

# Fire TV Stick ADB Installation & Setup Script
# Installation for Mac M5 Air

PROJECT_ROOT="/Users/nikhilsiddhu/OpenCode/firetv-tvos"
FIRE_TV_IP="192.168.1.41"
FIRE_TV_PORT="5555"

echo "=== Fire TV Stick ADB Setup for tvOS Customization ==="
echo "Device IP: $FIRE_TV_IP"
echo "Target Port: $FIRE_TV_PORT"

echo "\n=== Installing ADB (Android Debug Bridge) ==="

if command -v adb >/dev/null 2>&1; then
    echo "ADB is already installed: $(adb version)"
else
    echo "ADB not found. Installing..."
    
    # Check if Homebrew is available
    if command -v brew >/dev/null 2>&1; then
        echo "Using Homebrew to install Android Platform Tools..."
        brew install --cask android-platform-tools
    else
        echo "Homebrew not found. Please install Homebrew first:"
        echo "  /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        echo "Then re-run this script."
        exit 1
    fi
fi

echo "\n=== Verifying ADB Installation ==="
if command -v adb >/dev/null 2>&1; then
    echo "✓ ADB installed successfully: $(adb version)"
else
    echo "✗ ADB installation failed! Please install manually:"
    echo "  Download from: https://developer.android.com/studio/releases/platform-tools"
    exit 1
fi

echo "\n=== Checking Device Connection ==="

# Check if device is already connected locally
echo "Checking for connected Android devices..."
adb devices 2>/dev/null

echo "\n=== Fire TV Stick Connection Steps ==="
echo "1. On your Fire TV Stick ($FIRE_TV_IP):"
echo "   - Settings → Device Preferences → About → Build (press OK x7 times)"
echo "   - Back → Developer options → ADB Debugging (TURN ON)"
echo "   - If available, turn on Network/ADB debugging too"
echo "   - Keep TV ON"
echo ""
echo "2. On your Mac M5 Air:"
echo "   - Connect both computer and TV to same Wi-Fi network"
echo "   - Run: adb connect $FIRE_TV_IP:$FIRE_TV_PORT"
echo "   - Approve authorization on TV screen when prompted"
echo ""
echo "3. Verify connection:"
echo "   adb devices"
echo "   Should show: $FIRE_TV_IP device"

echo "\n=== Next Steps ==="
echo "After successful connection, run:"
echo "  bash $PROJECT_ROOT/scripts/debloat_fireos.sh"
echo ""
echo "This will create backup, debloat the device, and prepare for tvOS customization."
