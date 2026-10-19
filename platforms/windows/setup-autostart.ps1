# Jarvis - current-user background startup (no administrator rights required).

param([switch]$Remove)

$JARVIS_PATH = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$SCRIPT_PATH = Join-Path $JARVIS_PATH "platforms\windows\startup.ps1"
$RUN_KEY = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
$RUN_NAME = "Jarvis"

if ($Remove) {
    Remove-ItemProperty -Path $RUN_KEY -Name $RUN_NAME -ErrorAction SilentlyContinue
    Write-Host "Jarvis background startup is disabled."
    exit 0
}

$command = "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$SCRIPT_PATH`" -Mode daemon -Background"
New-Item -Path $RUN_KEY -Force | Out-Null
Set-ItemProperty -Path $RUN_KEY -Name $RUN_NAME -Value $command -Type String

Write-Host "Jarvis background startup is enabled for the current user."
Write-Host "Disable it with: .\platforms\windows\setup-autostart.ps1 -Remove"
