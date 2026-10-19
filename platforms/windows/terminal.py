"""Jarvis -- send voice commands to the installed Codex desktop app."""

import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv

from core.commands import normalize_selection

load_dotenv(Path(__file__).parents[2] / ".env")

CODEX_PACKAGE_MARKER = "\\OpenAI.Codex_"


def beep():
    """Short confirmation beep when wake word is heard."""
    import winsound
    winsound.Beep(1000, 150)


def send_to_codex(text):
    """
    Send text or a selection keypress to the active Codex desktop window.
    Short selection phrases (yes/no/one/two/up/down etc.) are mapped to
    direct keypresses. Everything else is pasted via clipboard.
    """
    keys, use_clipboard = normalize_selection(text)

    activate_block = f"""
$shell = New-Object -ComObject WScript.Shell
$activated = $false
try {{
    $appProcs = Get-CimInstance Win32_Process -Filter "Name = 'ChatGPT.exe'"
    foreach ($cp in $appProcs) {{
        if ($cp.ExecutablePath -like '*{CODEX_PACKAGE_MARKER}*') {{
            $proc = Get-Process -Id $cp.ProcessId -ErrorAction SilentlyContinue
            if ($proc -and $proc.MainWindowHandle -ne 0) {{
                $activated = $shell.AppActivate($cp.ProcessId)
                if ($activated) {{ break }}
            }}
        }}
    }}
}} catch {{}}
if (-not $activated) {{
    $proc = Get-Process -Name 'ChatGPT' -ErrorAction SilentlyContinue |
        Where-Object {{ $_.MainWindowHandle -ne 0 }} | Select-Object -First 1
    if ($proc) {{ $activated = $shell.AppActivate($proc.Id) }}
}}
"""

    if not use_clipboard:
        ps_script = activate_block + f"""
if ($activated) {{
    Start-Sleep -Milliseconds 400
    $shell.SendKeys('{keys}')
    Write-Host '[voice] Sent selection: {keys}'
}} else {{
    Write-Host '[voice] Could not find the Codex desktop window.'
}}
"""
    else:
        safe_text = text.replace("'", "''")
        ps_script = f"""
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.Clipboard]::SetText('{safe_text}')
""" + activate_block + """
if ($activated) {
    Start-Sleep -Milliseconds 600
    $shell.SendKeys('^v')
    Start-Sleep -Milliseconds 200
    $shell.SendKeys('{ENTER}')
    Write-Host '[voice] Sent to Codex.'
} else {
    Write-Host '[voice] Could not find the Codex desktop window.'
}
"""
    subprocess.run(["powershell", "-Command", ps_script], capture_output=True)


# Compatibility for callers outside this repository.
send_to_claude_code = send_to_codex
