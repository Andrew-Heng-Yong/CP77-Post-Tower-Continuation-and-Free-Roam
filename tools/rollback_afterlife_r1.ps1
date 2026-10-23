param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),[switch]$ValidateOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\');$audit=Join-Path $workspace 'research\afterlife_world'
$receipt=Get-Content (Join-Path $audit 'install_receipt.json') -Raw|ConvertFrom-Json
$game=[IO.Path]::GetFullPath($receipt.game_root).TrimEnd('\');$backup=[IO.Path]::GetFullPath($receipt.rollback_directory).TrimEnd('\')
function Closed {if(@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Close Cyberpunk before rollback'}}
function Within([string]$p,[string]$root){$full=[IO.Path]::GetFullPath($p);if(-not $full.StartsWith($root+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Path escaped intended root'};return $full}
function Match([string]$p,[string]$hash){if((Get-FileHash -LiteralPath $p).Hash -ne $hash){throw ('Unexpected hash: '+$p)}}
[void](Within $backup $workspace)
if($receipt.status -ne 'INSTALLED_AFTERLIFE_R1_LIVE_PENDING' -or $receipt.files.Count -ne 6){throw 'Unexpected receipt'}
$allowed=@('archive\pc\mod\TowerContinued_AfterlifeR1.archive','archive\pc\mod\TowerContinued_AfterlifeR1.archive.xl','r6\scripts\PTFR_Afterlife_R1\AfterlifeDriver.reds','bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_Afterlife_Audit\init.lua','archive\pc\mod\TowerContinued_B0_StoryEight.archive','r6\scripts\PTFR_B0_StoryEight\StoryEightDriver.reds')
if(@(Compare-Object @($receipt.files.relative|Sort-Object) @($allowed|Sort-Object)).Count){throw 'Rollback target drift'}
Closed
foreach($p in $receipt.files){$target=Within (Join-Path $game $p.relative) $game;Match $target $p.sha256;if($null -ne $p.previous_sha256){Match (Within (Join-Path $backup $p.relative) $backup) $p.previous_sha256}}
if($ValidateOnly){[pscustomobject]@{status='ROLLBACK_PREFLIGHT_PASS';files=6;restore=2;recoverable_moves=4}|ConvertTo-Json;return}
$retired=Within (Join-Path $backup ('removed_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))) $backup
foreach($p in $receipt.files){Closed;$target=Within (Join-Path $game $p.relative) $game;Match $target $p.sha256;$saved=Within (Join-Path $retired $p.relative) $retired;New-Item -ItemType Directory -Force (Split-Path $saved)|Out-Null;Copy-Item -LiteralPath $target -Destination $saved;Match $saved $p.sha256}
foreach($p in $receipt.files){Closed;$target=Within (Join-Path $game $p.relative) $game;Match $target $p.sha256;if($null -ne $p.previous_sha256){Copy-Item -LiteralPath (Within (Join-Path $backup $p.relative) $backup) -Destination $target -Force;Match $target $p.previous_sha256}else{Remove-Item -LiteralPath $target}}
$report=@{status='ROLLED_BACK_AFTERLIFE_R1';utc=[DateTime]::UtcNow.ToString('o');restored=2;removed_recoverably=4;retired_directory=$retired;saves_modified=$false;existing_logs_retained=$true}
[IO.File]::WriteAllText((Join-Path $audit 'rollback_receipt.json'),($report|ConvertTo-Json -Depth 5),[Text.UTF8Encoding]::new($false));$report|ConvertTo-Json -Depth 5
