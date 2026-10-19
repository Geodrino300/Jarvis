#!/usr/bin/env bash
# Jarvis -- Startup Script (macOS)
#
# Usage:
#   ./startup.sh                           # daemon mode (wait for double snap)
#   ./startup.sh --mode autostart          # launch immediately
#   ./startup.sh --workspace /path/to/app  # override WORKSPACE_PATH for this session

JARVIS_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
MODE="daemon"
WORKSPACE_OVERRIDE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --mode)      MODE="$2";              shift 2 ;;
        --workspace) WORKSPACE_OVERRIDE="$2"; shift 2 ;;
        *)           shift ;;
    esac
done

if [ -n "$WORKSPACE_OVERRIDE" ]; then
    export WORKSPACE_PATH="$WORKSPACE_OVERRIDE"
fi

if [ -f "$JARVIS_ROOT/venv/bin/python3" ]; then
    PYTHON="$JARVIS_ROOT/venv/bin/python3"
else
    PYTHON=$(which python3)
fi
JARVIS_SCRIPT="$JARVIS_ROOT/jarvis.py"

if [ ! -f "$JARVIS_SCRIPT" ]; then
    echo "Error: jarvis.py not found at $JARVIS_SCRIPT"
    exit 1
fi

echo "[jarvis] Starting in '$MODE' mode from $JARVIS_ROOT"

# Open a new terminal window/tab and run Jarvis there
if pgrep -x "iTerm2" > /dev/null 2>&1; then
    osascript <<EOF
tell application "iTerm2"
    tell current window
        create tab with default profile
        tell current session of current tab
            set name to "Jarvis"
            write text "cd '$JARVIS_ROOT' && $PYTHON '$JARVIS_SCRIPT' --mode $MODE"
        end tell
    end tell
end tell
EOF
else
    osascript <<EOF
tell application "Terminal"
    do script "cd '$JARVIS_ROOT' && $PYTHON '$JARVIS_SCRIPT' --mode $MODE; exec bash"
    set custom title of front window to "Jarvis"
    activate
end tell
EOF
fi

echo "[jarvis] Startup script done. Jarvis is running."
