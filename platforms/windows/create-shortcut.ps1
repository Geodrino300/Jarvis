# Jarvis - Desktop Shortcut Creator
# Creates a desktop shortcut that opens local Codex in a project folder
# and starts the Jarvis snap listener in one click.
#
# Usage:
#   .\create-shortcut.ps1 -ProjectPath "C:\projects\myapp"
#   .\create-shortcut.ps1 -ProjectPath "C:\projects\myapp" -ShortcutName "My App - Jarvis"

param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectPath,

    [string]$ShortcutName = ""   # defaults to folder name + " - Jarvis"
)

$JARVIS_PATH = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path

# Resolve shortcut name from folder name if not provided
if ($ShortcutName -eq "") {
    $folderName   = Split-Path $ProjectPath -Leaf
    $ShortcutName = "$folderName - Jarvis"
}

$desktopPath   = [System.Environment]::GetFolderPath("Desktop")
$shortcutPath  = Join-Path $desktopPath "$ShortcutName.lnk"
$startupScript = Join-Path $JARVIS_PATH "platforms\windows\startup.ps1"

$args = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$startupScript`" -WorkspacePath `"$ProjectPath`" -Mode autostart -Background"

$shell    = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath       = "powershell.exe"
$shortcut.Arguments        = $args
$shortcut.WorkingDirectory = $ProjectPath
$shortcut.WindowStyle      = 7   # minimised - no flash
$shortcut.Description      = "Open Codex + Jarvis for $ProjectPath"
$shortcut.Save()

Write-Host ""
Write-Host "Shortcut created: $shortcutPath"
Write-Host "  Project: $ProjectPath"
Write-Host "  Opens:   Codex terminal + Jarvis voice listener"
Write-Host ""
Write-Host "To pin it to your taskbar: right-click the shortcut > Pin to taskbar"
