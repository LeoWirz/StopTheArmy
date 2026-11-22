# Fallback for harnesses with no plugin system (Windows): link this plugin's
# skills into a skills directory the harness scans. Uses directory junctions,
# which need no admin rights or Developer Mode.
#   .\scripts\link-skills.ps1                                  # -> .\.agents\skills
#   .\scripts\link-skills.ps1 "$env:USERPROFILE\.agents\skills" # user-wide
param([string]$Dest = '.agents\skills')
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
New-Item -ItemType Directory -Force -Path $Dest | Out-Null
Get-ChildItem -Directory (Join-Path $root 'skills') | ForEach-Object {
    $link = Join-Path $Dest $_.Name
    if (Test-Path $link) {
        $item = Get-Item -Force $link
        if (-not ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            Write-Warning "skipping $link (a real directory, not a link)"; return
        }
        # Removes only the junction itself. Never Remove-Item -Recurse here:
        # on Windows PowerShell 5.1 that can delete the target's contents.
        [IO.Directory]::Delete($link, $false)
    }
    New-Item -ItemType Junction -Path $link -Target $_.FullName | Out-Null
    Write-Output "linked $link"
}
Write-Output ''
Write-Output "For always-on instructions, reference $root\INSTRUCTIONS.md from your"
Write-Output "harness's global instructions file (e.g. $env:USERPROFILE\.codex\AGENTS.md)."
