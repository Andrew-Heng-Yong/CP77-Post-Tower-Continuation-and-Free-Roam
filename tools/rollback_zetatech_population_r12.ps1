param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),[string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',[switch]$ValidateOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\');$game=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
$r=Get-Content (Join-Path $workspace 'research\misty_viktor_world\population_r12_install_receipt.json') -Raw|ConvertFrom-Json
function Closed {if(@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Close Cyberpunk before rollback'}}
function Within([string]$p,[string]$root){$f=[IO.Path]::GetFullPath($p);if(-not $f.StartsWith($root+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Path escaped intended root'};return $f}
function Match([string]$p,[string]$h){if((Get-FileHash -LiteralPath $p).Hash -ne $h){throw ('Unexpected file: '+$p)}}
if($r.status -ne 'INSTALLED_R12_POPULATION_IDLE_LIVE_PENDING' -or $r.files.Count -ne 4){throw 'Unexpected R12 receipt'}
Closed;$backup=Within $r.rollback_directory $workspace
foreach($p in $r.files){Match (Within (Join-Path $game $p.relative) $game) $p.sha256;if($null -ne $p.previous_sha256){Match (Within (Join-Path $backup $p.relative) $backup) $p.previous_sha256}}
if($ValidateOnly){[pscustomobject]@{status='ROLLBACK_VALIDATED_ONLY';targets=4;restore=1;recoverable_moves=3;game_running=$false}|ConvertTo-Json;return}
$retired=Within (Join-Path $backup ('retired_r12_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))) $backup
foreach($p in $r.files){
 Closed;$target=Within (Join-Path $game $p.relative) $game;Match $target $p.sha256
 $dest=Within (Join-Path $retired $p.relative) $retired;New-Item -ItemType Directory -Force (Split-Path -Parent $dest)|Out-Null
 if($null -eq $p.previous_sha256){Move-Item -LiteralPath $target -Destination $dest;Match $dest $p.sha256}
 else{Copy-Item -LiteralPath $target -Destination $dest;Match $dest $p.sha256;Copy-Item -LiteralPath (Within (Join-Path $backup $p.relative) $backup) -Destination $target -Force;Match $target $p.previous_sha256}
}
[pscustomobject]@{status='R12_RETIRED_R11_PRESERVED';retired=$retired;save_files_modified=$false}|ConvertTo-Json
