#!/usr/bin/env bash
# Jarvis -- Desktop App Shortcut Creator (macOS)
# Creates a double-clickable .app on the Desktop that opens Claude Code
# in a project folder and starts the Jarvis snap listener.
#
# Usage:
#   ./create-shortcut.sh --project /path/to/myapp
#   ./create-shortcut.sh --project /path/to/myapp --name "My App - Jarvis"

JARVIS_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PROJECT_PATH=""
SHORTCUT_NAME=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --project) PROJECT_PATH="$2"; shift 2 ;;
        --name)    SHORTCUT_NAME="$2"; shift 2 ;;
        *)         shift ;;
    esac
done

if [ -z "$PROJECT_PATH" ]; then
    echo "Error: --project <path> is required"
    echo "Usage: $0 --project /path/to/myapp [--name \"My App - Jarvis\"]"
    exit 1
fi

if [ ! -d "$PROJECT_PATH" ]; then
    echo "Error: project path does not exist: $PROJECT_PATH"
    exit 1
fi

if [ -z "$SHORTCUT_NAME" ]; then
    SHORTCUT_NAME="$(basename "$PROJECT_PATH") - Jarvis"
fi

DESKTOP_PATH="$HOME/Desktop"
APP_PATH="$DESKTOP_PATH/$SHORTCUT_NAME.app"
STARTUP_SCRIPT="$JARVIS_ROOT/platforms/mac/startup.sh"

# Build the AppleScript that the .app will run
APPLESCRIPT=$(cat <<APPLEEOF
on run
    do shell script "bash '$STARTUP_SCRIPT' --workspace '$PROJECT_PATH' --mode autostart"
    tell application "Terminal"
        activate
    end tell
end run
APPLEEOF
)

# Compile into a .app bundle
osacompile -o "$APP_PATH" -e "$APPLESCRIPT"

echo ""
echo "Shortcut created: $APP_PATH"
echo "  Project: $PROJECT_PATH"
echo "  Opens:   Claude Code terminal + Jarvis snap listener"
echo ""
echo "To add it to your Dock: drag it from the Desktop into the Dock."
