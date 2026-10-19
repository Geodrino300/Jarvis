# Jarvis - Launch Session (Windows)
# Triggered by double snap. Opens VS Code and the installed Codex desktop app.

param(
    [string]$WorkspacePath = "",
    [switch]$SkipCodex
)

if ($WorkspacePath -eq "") {
    $WorkspacePath = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}

# Open VS Code in the workspace.
if (Get-Command code -ErrorAction SilentlyContinue) {
    Start-Process "code" -ArgumentList $WorkspacePath
}

# Use the installed Codex desktop package. This is local and never opens a web page
# or an interactive terminal with unsupported TUI settings.
if (-not $SkipCodex) {
    $package = Get-AppxPackage -Name "OpenAI.Codex" -ErrorAction Stop
    $appId = "$($package.PackageFamilyName)!App"
    Start-Process "explorer.exe" -ArgumentList "shell:AppsFolder\$appId"
}
