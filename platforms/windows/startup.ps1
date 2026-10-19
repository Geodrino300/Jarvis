# Jarvis - Startup Script (Windows)
# Starts one snap listener either hidden in the background or in a visible console.

param(
    [ValidateSet("daemon", "autostart")]
    [string]$Mode = "daemon",
    [string]$WorkspacePath = "",
    [switch]$OpenCodex,
    [switch]$Background
)

$JARVIS_PATH = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$PYTHON = (Get-Command python -ErrorAction Stop).Source
$JARVIS_SCRIPT = Join-Path $JARVIS_PATH "jarvis.py"

if ($WorkspacePath -ne "") {
    $env:WORKSPACE_PATH = $WorkspacePath
}

$resolved = if ($WorkspacePath -ne "") { $WorkspacePath } else {
    $envFile = Join-Path $JARVIS_PATH ".env"
    $ws = ""
    if (Test-Path -LiteralPath $envFile) {
        Get-Content -LiteralPath $envFile | ForEach-Object {
            if ($_ -match "^WORKSPACE_PATH=(.+)$") {
                $ws = $matches[1].Trim().Trim('"')
            }
        }
    }
    if ($ws -eq "") { $JARVIS_PATH } else { $ws }
}

if (-not (Test-Path -LiteralPath $resolved -PathType Container)) {
    throw "WORKSPACE_PATH does not name an existing folder: $resolved"
}

$existing = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like "*$JARVIS_SCRIPT*" } |
    Select-Object -First 1
if ($existing) {
    Write-Host "Jarvis is already running (PID $($existing.ProcessId))."
    exit 0
}

if ($OpenCodex) {
    $package = Get-AppxPackage -Name "OpenAI.Codex" -ErrorAction Stop
    $appId = "$($package.PackageFamilyName)!App"
    Start-Process "explorer.exe" -ArgumentList "shell:AppsFolder\$appId"
}

if ($Background) {
    $logDir = Join-Path $JARVIS_PATH "logs"
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    $process = Start-Process -FilePath $PYTHON `
        -ArgumentList @($JARVIS_SCRIPT, "--mode", $Mode) `
        -WorkingDirectory $JARVIS_PATH `
        -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $logDir "jarvis.stdout.log") `
        -RedirectStandardError (Join-Path $logDir "jarvis.stderr.log") `
        -PassThru
} else {
    $command = "`$Host.UI.RawUI.WindowTitle = 'Jarvis'; & '$PYTHON' '$JARVIS_SCRIPT' '--mode' '$Mode'"
    $process = Start-Process "powershell" `
        -ArgumentList "-NoExit", "-Command", $command `
        -WorkingDirectory $JARVIS_PATH `
        -WindowStyle Normal `
        -PassThru
}

Write-Host "Jarvis started in '$Mode' mode (PID $($process.Id)). Workspace: $resolved"
