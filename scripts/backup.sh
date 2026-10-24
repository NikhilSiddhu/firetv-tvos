#!/bin/bash
# Create a backup of all installed packages and settings before debloat

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_env.sh"

BACKUP_DIR="${HOME}/.cleanyourtv_backup"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="fireos_backup_$TIMESTAMP"

mkdir -p "$BACKUP_DIR"

echo "=========================================="
echo "  Creating Fire TV Backup"
echo "=========================================="

echo -e "\n[1/4] Connecting to TV..."
adb connect ${FIRE_TV_IP}:${FIRE_TV_PORT} >/dev/null 2>&1
adb devices

echo -e "\n[2/4] Backing up packages..."
adb shell pm list packages > "${BACKUP_DIR}/${BACKUP_NAME}.packages" 2>/dev/null

echo -e "\n[3/4] Backing up settings..."
adb shell settings get secure > "${BACKUP_DIR}/${BACKUP_NAME}.settings" 2>/dev/null || true

echo -e "\n[4/4] Done!"
echo "Backup saved to: ${BACKUP_DIR}"
ls -la "${BACKUP_DIR}/"
