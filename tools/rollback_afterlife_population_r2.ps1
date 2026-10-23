param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),[switch]$Restore,[switch]$ValidateOnly)
# Default is read-only. Does not use the R1 rollback, which would undo Nix.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if($Restore -and $ValidateOnly){throw 'Choose restoration OR validation'}
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\');$audit=Join-Path $workspace 'research\afterlife_world\population_r2'
$r=Get-Content (Join-Path $audit 'install_receipt.json') -Raw|ConvertFrom-Json
$game=[IO.Path]::GetFullPath($r.game_root).TrimEnd('\');$backup=[IO.Path]::GetFullPath($r.rollback_directory).TrimEnd('\')
function Closed {if(@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Close Cyberpunk before rollback'}}
function Within([string]$p,[string]$root){$full=[IO.Path]::GetFullPath($p);if(-not $full.StartsWith($root+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Path escaped intended root'};return $full}
function Match([string]$p,[string]$hash){if((Get-FileHash -LiteralPath $p).Hash -ne $hash){throw "Unexpected hash: $p"}}
[void](Within $backup $workspace)
$allowed=@('archive\pc\mod\TowerContinued_AfterlifeR1.archive','archive\pc\mod\TowerContinued_AfterlifeR1.archive.xl')
if($r.status -ne 'INSTALLED_AFTERLIFE_POPULATION_R2_LIVE_PENDING' -or $r.files.Count -ne 2 -or @(Compare-Object @($r.files.relative|Sort-Object) ($allowed|Sort-Object)).Count){throw 'Unexpected R2 receipt/targets'}
Closed
foreach($p in $r.files){Match (Within (Join-Path $game $p.relative) $game) $p.sha256;Match (Within (Join-Path $backup $p.relative) $backup) $p.previous_sha256}
if(-not $Restore){@{status='R2_ROLLBACK_PREFLIGHT_PASS';restore=2;named_actor_and_nix_changes=0}|ConvertTo-Json;return}
$retired=Within (Join-Path $backup ('retired_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))) $backup
foreach($p in $r.files){Closed;$target=Within (Join-Path $game $p.relative) $game;Match $target $p.sha256;$dest=Within (Join-Path $retired $p.relative) $retired;New-Item -ItemType Directory -Force (Split-Path $dest)|Out-Null;Copy-Item -LiteralPath $target -Destination $dest;Match $dest $p.sha256}
foreach($p in $r.files){Closed;$target=Within (Join-Path $game $p.relative) $game;Match $target $p.sha256;Copy-Item -LiteralPath (Within (Join-Path $backup $p.relative) $backup) -Destination $target -Force;Match $target $p.previous_sha256}
$report=@{status='ROLLED_BACK_AFTERLIFE_POPULATION_R2_TO_R1';utc=[DateTime]::UtcNow.ToString('o');restored=2;retired_directory=$retired;save_changes=0;warning='Load the pre-R2 test save; removing native quest resources is not certified safe for an R2-saved session.'}
[IO.File]::WriteAllText((Join-Path $audit 'rollback_receipt.json'),($report|ConvertTo-Json -Depth 5),[Text.UTF8Encoding]::new($false));$report|ConvertTo-Json -Depth 5
