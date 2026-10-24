#!/bin/bash
# ADB Wireless Connection Script for Fire TV Stick 3rd Gen
# Fire OS 7.7.1.7 | Port: 5555 (set FIRE_TV_IP in local.env)

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_env.sh"

echo "=========================================="
echo "  Fire TV Stick ADB Connection"
echo "=========================================="
echo "Device: Fire TV Stick 3rd Gen"
echo "IP: $FIRE_TV_IP"
echo "Port: $FIRE_TV_PORT"
echo "Fire OS: 7.7.1.7"
echo "=========================================="

echo -e "\n[1/3] Checking ADB..."
if ! command -v adb >/dev/null 2>&1; then
    echo "ADB not found! Run: bash scripts/install_adb.sh"
    exit 1
fi
echo "ADB found: $(adb version)"

echo -e "\n[2/3] Connecting to Fire TV..."
adb connect ${FIRE_TV_IP}:${FIRE_TV_PORT}

echo -e "\n[3/3] Verifying connection..."
adb devices

echo -e "\n=========================================="
echo "  CONNECTION COMPLETE"
echo "=========================================="
echo "Next: bash scripts/debloat_fireos.sh"
