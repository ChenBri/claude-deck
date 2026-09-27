# Push this checkout's firmware and deploy scripts to the deck over the USB
# link, then restart the firmware. Run from the repo root on the PC:
#
#   .\deploy\deploy.ps1                  code only
#   .\deploy\deploy.ps1 -Deps            also reinstall Python requirements
#   .\deploy\deploy.ps1 -User myname     SSH login other than the image's default
#
# The app lives on the deck's writable /var/deck partition, so an update never
# touches the read-only root. Your ROMs and the local var/ folder stay on the PC.
param(
    [string]$User = "radxa",
    [string]$DeckHost = "10.55.0.1",
    [switch]$Deps
)
$ErrorActionPreference = "Stop"

$repo = Split-Path -Parent $PSScriptRoot
$archive = Join-Path $env:TEMP "claude-deck-push.tgz"
$target = "$User@$DeckHost"

tar -czf $archive -C $repo `
    --exclude "__pycache__" --exclude "firmware/var" --exclude "firmware/roms/*.gb*" `
    firmware deploy
if ($LASTEXITCODE -ne 0) { throw "tar failed" }

scp -q $archive "${target}:/tmp/claude-deck-push.tgz"
if ($LASTEXITCODE -ne 0) { throw "scp failed: is the deck plugged in and on $DeckHost?" }

$remote = "set -e; sudo tar -xzf /tmp/claude-deck-push.tgz -C /var/deck/app; rm /tmp/claude-deck-push.tgz"
if ($Deps) { $remote += "; sudo /var/deck/venv/bin/pip install -r /var/deck/app/firmware/requirements-deck.txt" }
$remote += "; sudo chown -R deck:deck /var/deck/app; sudo systemctl restart deck; systemctl is-active deck"

ssh $target $remote
if ($LASTEXITCODE -ne 0) { throw "remote update failed" }
Remove-Item $archive
Write-Host "deployed to $DeckHost"
