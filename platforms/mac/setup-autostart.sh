#!/usr/bin/env bash
# Jarvis -- Autostart Setup (macOS)
# Registers a launchd agent so Jarvis launches automatically at login.
#
# The workspace that opens is controlled by WORKSPACE_PATH in your .env file.
# Update .env when you switch projects.
#
# Usage (run once):
#   ./setup-autostart.sh
#   ./setup-autostart.sh --workspace /path/to/myapp
#   ./setup-autostart.sh --remove

JARVIS_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PLIST_LABEL="com.jarvis.autostart"
PLIST_PATH="$HOME/Library/LaunchAgents/$PLIST_LABEL.plist"
STARTUP_SCRIPT="$JARVIS_ROOT/platforms/mac/startup.sh"
WORKSPACE_OVERRIDE=""
REMOVE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --workspace) WORKSPACE_OVERRIDE="$2"; shift 2 ;;
        --remove)    REMOVE=true; shift ;;
        *)           shift ;;
    esac
done

if $REMOVE; then
    launchctl unload "$PLIST_PATH" 2>/dev/null
    rm -f "$PLIST_PATH"
    echo ""
    echo "Jarvis autostart removed."
    echo "  Deleted: $PLIST_PATH"
    echo ""
    exit 0
fi

# Resolve workspace: flag > .env > empty
if [ -z "$WORKSPACE_OVERRIDE" ] && [ -f "$JARVIS_ROOT/.env" ]; then
    WORKSPACE_OVERRIDE=$(grep -E '^WORKSPACE_PATH=' "$JARVIS_ROOT/.env" | cut -d= -f2- | tr -d '"'"'" | xargs)
fi

ARGS="--mode autostart"
if [ -n "$WORKSPACE_OVERRIDE" ]; then
    ARGS="$ARGS --workspace $WORKSPACE_OVERRIDE"
fi

mkdir -p "$HOME/Library/LaunchAgents"

cat > "$PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$PLIST_LABEL</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>$STARTUP_SCRIPT</string>
        <string>--mode</string>
        <string>autostart</string>$([ -n "$WORKSPACE_OVERRIDE" ] && printf '\n        <string>--workspace</string>\n        <string>%s</string>' "$WORKSPACE_OVERRIDE")
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardOutPath</key>
    <string>$HOME/Library/Logs/jarvis-autostart.log</string>
    <key>StandardErrorPath</key>
    <string>$HOME/Library/Logs/jarvis-autostart.log</string>
</dict>
</plist>
EOF

# Load it immediately so it takes effect without a reboot
launchctl unload "$PLIST_PATH" 2>/dev/null
launchctl load "$PLIST_PATH"

echo ""
echo "Autostart registered: $PLIST_LABEL"
echo "  Triggers:  At login (this user only)"
echo "  Workspace: ${WORKSPACE_OVERRIDE:-"read from .env at runtime"}"
echo "  Log:       ~/Library/Logs/jarvis-autostart.log"
echo ""
echo "Jarvis will launch automatically next time you log in."
echo ""
echo "To remove: bash $STARTUP_SCRIPT --remove"
echo "           or: launchctl unload $PLIST_PATH && rm $PLIST_PATH"
echo ""
