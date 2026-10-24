#!/bin/bash
# ============================================================
#  Shared configuration for the Fire TV scripts.
#  Sourced by every script in scripts/ and by tools/theme.sh
# ------------------------------------------------------------
#  Copy local.env.example to local.env and put your TV's
#  address in it. local.env is gitignored, so your network
#  details never leave this machine.
#
#    cp local.env.example local.env
#    $EDITOR local.env
#
#  One-off override without a file:
#
#    FIRE_TV_IP=192.168.1.50 bash scripts/connect_adb.sh
# ============================================================

_ENV_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_ROOT="$_ENV_ROOT"

if [ -f "$PROJECT_ROOT/local.env" ]; then
  # shellcheck disable=SC1091
  . "$PROJECT_ROOT/local.env"
fi

if [ -z "${FIRE_TV_IP:-}" ]; then
  if [ "${_ENV_SOFT:-0}" = "1" ]; then
    FIRE_TV_IP="<your-tv-ip>"
  else
    cat >&2 <<'MSG'
ERROR: FIRE_TV_IP is not set.

  cp local.env.example local.env    # then set FIRE_TV_IP to your TV's address
  FIRE_TV_IP=192.168.1.50 bash scripts/connect_adb.sh   # or pass it once

The address is on the TV under  Settings > My Fire TV > About > Network.
MSG
    exit 1
  fi
fi

FIRE_TV_PORT="${FIRE_TV_PORT:-5555}"
SERIAL="${FIRE_TV_IP}:${FIRE_TV_PORT}"

export PROJECT_ROOT FIRE_TV_IP FIRE_TV_PORT SERIAL
