param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),[string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',[switch]$ValidateOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\');$game=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
$audit=Join-Path $workspace 'research\misty_viktor_world'
$receipt=Get-Content (Join-Path $audit 'access_r11_install_receipt.json') -Raw|ConvertFrom-Json
function Closed {if(@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Close Cyberpunk before rollback'}}
function Within([string]$p,[string]$r){$full=[IO.Path]::GetFullPath($p);if(-not $full.StartsWith($r+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Rollback path escaped expected root'};return $full}
function MatchHash([string]$p,[string]$h){if((Get-FileHash -LiteralPath $p).Hash -ne $h){throw ('Unexpected file; rollback stopped: '+$p)}}
if($receipt.status -ne 'INSTALLED_R11_DOORS_STREET_TERRY_COUNTERSTAFF_LIVE_PENDING' -or $receipt.files.Count -ne 5){throw 'Unexpected R11 receipt'}
Closed
$backup=Within $receipt.rollback_directory $workspace
foreach($p in $receipt.files){
 $target=Within (Join-Path $game $p.relative) $game;MatchHash $target $p.sha256
 if($null -ne $p.previous_sha256){MatchHash (Within (Join-Path $backup $p.relative) $backup) $p.previous_sha256}
}
if($ValidateOnly){[pscustomobject]@{status='ROLLBACK_VALIDATED_ONLY';targets=5;restore=2;recoverable_moves=3;game_running=$false}|ConvertTo-Json;return}
$removed=Within (Join-Path $backup ('retired_r11_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))) $backup
foreach($p in $receipt.files){
 Closed;$target=Within (Join-Path $game $p.relative) $game;MatchHash $target $p.sha256
 $saved=Within (Join-Path $removed $p.relative) $removed;New-Item -ItemType Directory -Force (Split-Path -Parent $saved)|Out-Null
 if($null -eq $p.previous_sha256){Move-Item -LiteralPath $target -Destination $saved;MatchHash $saved $p.sha256}
 else{Copy-Item -LiteralPath $target -Destination $saved;MatchHash $saved $p.sha256;Copy-Item -LiteralPath (Within (Join-Path $backup $p.relative) $backup) -Destination $target -Force;MatchHash $target $p.previous_sha256}
}
[pscustomobject]@{status='R11_RETIRED_R10_RESTORED';retired_r11=$removed;save_files_modified=$false}|ConvertTo-Json
