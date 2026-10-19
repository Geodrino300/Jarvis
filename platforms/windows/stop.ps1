# Stop the Jarvis listener. Optionally disable login startup too.

param([switch]$DisableAutostart)

$JARVIS_PATH = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$JARVIS_SCRIPT = Join-Path $JARVIS_PATH "jarvis.py"
$targets = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like "*$JARVIS_SCRIPT*" }

if ($targets) {
    $targets | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
    Write-Host "Jarvis stopped."
} else {
    Write-Host "Jarvis is not running."
}

if ($DisableAutostart) {
    $runKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
    Remove-ItemProperty -Path $runKey -Name "Jarvis" -ErrorAction SilentlyContinue
    Write-Host "Jarvis background startup is disabled."
}
