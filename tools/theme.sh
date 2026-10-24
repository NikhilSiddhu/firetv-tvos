#!/bin/bash

# Fire TV Theme Automation Script
# Push dynamic config.json updates and wallpapers over Wi-Fi
# Modifies dock apps, grid density, and stats display in real-time

source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../scripts" && pwd)/_env.sh"

THEME_DIR="${PROJECT_ROOT}/themes"
LAUNCHER_DATA="/sdcard/Android/data/com.gathin.tvhome"

echo "=========================================="
echo "  Fire TV Theme Automation Script"
echo "=========================================="

# Function to push a theme
push_theme() {
    local theme_name="$1"
    local theme_path="${THEME_DIR}/${theme_name}"
    
    if [ ! -d "$theme_path" ]; then
        echo "Theme not found: $theme_name"
        echo "Available themes:"
        ls "$THEME_DIR" 2>/dev/null
        return 1
    fi
    
    echo "Pushing theme: $theme_name"
    
    # Push config.json
    if [ -f "${theme_path}/config.json" ]; then
        echo "  - Pushing config.json..."
        adb -s ${FIRE_TV_IP}:${FIRE_TV_PORT} push "${theme_path}/config.json" "${LAUNCHER_DATA}/config.json" 2>&1
    fi
    
    # Push wallpaper if exists
    if [ -f "${theme_path}/wallpaper.jpg" ]; then
        echo "  - Pushing wallpaper.jpg..."
        adb -s ${FIRE_TV_IP}:${FIRE_TV_PORT} push "${theme_path}/wallpaper.jpg" "${LAUNCHER_DATA}/wallpaper.jpg" 2>&1
    fi
    
    # Push background if exists
    if [ -f "${theme_path}/background.jpg" ]; then
        echo "  - Pushing background.jpg..."
        adb -s ${FIRE_TV_IP}:${FIRE_TV_PORT} push "${theme_path}/background.jpg" "${LAUNCHER_DATA}/background.jpg" 2>&1
    fi
    
    # Restart launcher to apply changes
    echo "  - Restarting launcher..."
    adb -s ${FIRE_TV_IP}:${FIRE_TV_PORT} shell am force-stop com.gathin.tvhome 2>&1
    sleep 1
    adb -s ${FIRE_TV_IP}:${FIRE_TV_PORT} shell am start -n com.gathin.tvhome/.MainActivity 2>&1
    
    echo "Theme applied: $theme_name"
}

# Function to push dynamic config
push_dynamic_config() {
    local config_json="$1"
    
    echo "Pushing dynamic config..."
    
    # Write config.json to temp file
    echo "$config_json" > /tmp/firetv_config.json
    
    # Push to TV
    adb -s ${FIRE_TV_IP}:${FIRE_TV_PORT} push /tmp/firetv_config.json "${LAUNCHER_DATA}/config.json" 2>&1
    
    # Restart launcher
    adb -s ${FIRE_TV_IP}:${FIRE_TV_PORT} shell am force-stop com.gathin.tvhome 2>&1
    sleep 1
    adb -s ${FIRE_TV_IP}:${FIRE_TV_PORT} shell am start -n com.gathin.tvhome/.MainActivity 2>&1
    
    echo "Dynamic config applied."
}

# Function to reset to default theme
reset_theme() {
    echo "Resetting to default theme..."
    push_theme "default"
}

# Function to update dock apps
update_dock_apps() {
    local dock_apps="$1"
    
    echo "Updating dock apps..."
    push_dynamic_config "{\"dock_apps\": ${dock_apps}}"
}

# Function to update grid density
update_grid_density() {
    local columns="$1"
    local rows="$2"
    
    echo "Updating grid density: ${columns}x${rows}"
    push_dynamic_config "{\"grid_columns\": ${columns}, \"grid_rows\": ${rows}}"
}

# Function to toggle stats display
toggle_stats() {
    local show_stats="$1"
    
    echo "Toggling stats display: ${show_stats}"
    push_dynamic_config "{\"show_stats\": ${show_stats}}"
}

# Function to push wallpaper
push_wallpaper() {
    local wallpaper_path="$1"
    
    if [ ! -f "$wallpaper_path" ]; then
        echo "Wallpaper file not found: $wallpaper_path"
        return 1
    fi
    
    echo "Pushing wallpaper: $wallpaper_path"
    adb -s ${FIRE_TV_IP}:${FIRE_TV_PORT} push "$wallpaper_path" "${LAUNCHER_DATA}/wallpaper.jpg" 2>&1
    
    # Restart launcher
    adb -s ${FIRE_TV_IP}:${FIRE_TV_PORT} shell am force-stop com.gathin.tvhome 2>&1
    sleep 1
    adb -s ${FIRE_TV_IP}:${FIRE_TV_PORT} shell am start -n com.gathin.tvhome/.MainActivity 2>&1
    
    echo "Wallpaper applied."
}

# Main command dispatcher
case "${1:-}" in
    push)
        push_theme "${2:-default}"
        ;;
    dynamic)
        push_dynamic_config "${2}"
        ;;
    reset)
        reset_theme
        ;;
    dock)
        update_dock_apps "${2}"
        ;;
    grid)
        update_grid_density "${2}" "${3}"
        ;;
    stats)
        toggle_stats "${2}"
        ;;
    wallpaper)
        push_wallpaper "${2}"
        ;;
    list)
        echo "Available themes:"
        ls "$THEME_DIR" 2>/dev/null
        ;;
    help)
        echo "Usage: $0 <command> [args...]"
        echo ""
        echo "Commands:"
        echo "  push <theme_name>        Push a theme"
        echo "  dynamic <json>           Push dynamic config"
        echo "  reset                    Reset to default theme"
        echo "  dock <apps_json>         Update dock apps"
        echo "  grid <cols> <rows>       Update grid density"
        echo "  stats <true|false>       Toggle stats display"
        echo "  wallpaper <path>         Push wallpaper"
        echo "  list                     List available themes"
        ;;
    *)
        echo "Fire TV Theme Automation"
        echo "Usage: $0 <command> [args...]"
        echo "Run '$0 help' for usage"
        ;;
esac
