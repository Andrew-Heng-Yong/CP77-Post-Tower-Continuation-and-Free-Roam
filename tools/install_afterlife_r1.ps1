param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),[string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',[switch]$ValidateOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\');$game=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
$audit=Join-Path $workspace 'research\afterlife_world'
$m=Get-Content (Join-Path $audit 'manifest.json') -Raw|ConvertFrom-Json
$nix=Get-Content (Join-Path $audit 'nix_manifest.json') -Raw|ConvertFrom-Json
$t=Get-Content (Join-Path $audit 'tests.json') -Raw|ConvertFrom-Json
$runtime=Get-Content (Join-Path $audit 'runtime_tests.json') -Raw|ConvertFrom-Json
function Closed {if(@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Close Cyberpunk before installation'}}
function Hash([string]$p){return (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash}
function Match([string]$p,[string]$h){if((Hash $p) -ne $h){throw ('Unexpected hash: '+$p)}}
function Within([string]$p,[string]$root){$full=[IO.Path]::GetFullPath($p);if(-not $full.StartsWith($root+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Path escaped intended root'};return $full}
if($t.status -ne 'PASS_AFTERLIFE_R1_OFFLINE_NOT_LIVE' -or $t.archive_sha256 -ne $m.sha256 -or $t.xl_sha256 -ne $m.xl_sha256 -or $t.nix_archive_sha256 -ne $nix.sha256 -or $runtime.status -ne 'PASS_RUNTIME_OFFLINE_NOT_LIVE'){throw 'Missing/stale offline validation'}
if(-not (Test-Path -LiteralPath (Join-Path $game 'r6\cache\final.redscripts') -PathType Leaf)){throw 'Unexpected game directory'}
$payloads=@(
 @{relative='archive\pc\mod\TowerContinued_AfterlifeR1.archive';source=$m.archive;sha256=$m.sha256;old=$null},
 @{relative='archive\pc\mod\TowerContinued_AfterlifeR1.archive.xl';source=($m.archive+'.xl');sha256=$m.xl_sha256;old=$null},
 @{relative='r6\scripts\PTFR_Afterlife_R1\AfterlifeDriver.reds';source=(Join-Path $workspace 'redscript\PTFR_Afterlife_R1\AfterlifeDriver.reds');sha256=$runtime.driver_sha256;old=$null},
 @{relative='bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_Afterlife_Audit\init.lua';source=(Join-Path $workspace 'diagnostics\PTFR_Afterlife_Audit\init.lua');sha256=$runtime.diagnostic_sha256;old=$null},
 @{relative='archive\pc\mod\TowerContinued_B0_StoryEight.archive';source=$nix.archive;sha256=$nix.sha256;old=$nix.previous_sha256},
 @{relative='r6\scripts\PTFR_B0_StoryEight\StoryEightDriver.reds';source=$nix.script;sha256=$runtime.nix_driver_sha256;old=$nix.previous_script_sha256}
)
$targets=@{}
Closed
foreach($p in $payloads){$p.source=Within $p.source $workspace;$p.target=Within (Join-Path $game $p.relative) $game;if($targets.ContainsKey($p.target)){throw 'Duplicate target'};$targets[$p.target]=$true;Match $p.source $p.sha256;if($null -eq $p.old){if(Test-Path -LiteralPath $p.target){throw ('Additive target already exists: '+$p.target)}}else{Match $p.target $p.old}}
$protected=[ordered]@{}
foreach($f in Get-ChildItem -LiteralPath (Join-Path $game 'archive\pc\mod') -File -Filter 'TowerContinued*'){if(-not $targets.ContainsKey($f.FullName)){$protected[$f.FullName]=Hash $f.FullName}}
foreach($root in @((Join-Path $game 'r6\scripts'),(Join-Path $game 'bin\x64\plugins\cyber_engine_tweaks\mods'))){foreach($dir in Get-ChildItem -LiteralPath $root -Directory -Filter 'PTFR_*'){foreach($f in Get-ChildItem -LiteralPath $dir.FullName -File -Recurse){if(-not $targets.ContainsKey($f.FullName)){$protected[$f.FullName]=Hash $f.FullName}}}}
foreach($f in Get-ChildItem -LiteralPath (Join-Path $game 'r6\tweaks') -File -Recurse){if(-not $targets.ContainsKey($f.FullName)){$protected[$f.FullName]=Hash $f.FullName}}
function Protected {foreach($p in $protected.Keys){Match $p $protected[$p]}}
Closed;Protected
if($ValidateOnly){[pscustomobject]@{status='VALIDATED_ONLY';additions=4;replacements=2;protected_files=$protected.Count;game_running=$false}|ConvertTo-Json;return}
$backup=Within (Join-Path $audit ('rollback_R1_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))) $workspace
New-Item -ItemType Directory -Path $backup|Out-Null
foreach($p in $payloads){if($null -ne $p.old){$dest=Within (Join-Path $backup $p.relative) $backup;New-Item -ItemType Directory -Force (Split-Path $dest)|Out-Null;Copy-Item -LiteralPath $p.target -Destination $dest;Match $dest $p.old}}
$written=[Collections.Generic.List[object]]::new()
try{
 foreach($p in $payloads){Closed;Match $p.source $p.sha256;if($null -eq $p.old){if(Test-Path -LiteralPath $p.target){throw 'New destination appeared'}}else{Match $p.target $p.old};New-Item -ItemType Directory -Force (Split-Path $p.target)|Out-Null;$written.Add($p);Copy-Item -LiteralPath $p.source -Destination $p.target -Force;Match $p.target $p.sha256}
 Closed;Protected
 $receipt=[ordered]@{status='INSTALLED_AFTERLIFE_R1_LIVE_PENDING';utc=[DateTime]::UtcNow.ToString('o');game_root=$game;files=@($payloads|ForEach-Object {@{relative=$_.relative;sha256=$_.sha256;previous_sha256=$_.old}});rollback_directory=$backup;protected_files=$protected.Count;additions=4;replacements=2;nix_unchanged_payloads=15;save_writes=0;forced_story_writes=0;live_tested=$false}
 [IO.File]::WriteAllText((Join-Path $audit 'install_receipt.json'),($receipt|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false));$receipt|ConvertTo-Json -Depth 8
}catch{
 $failure=$_.Exception.Message;$errors=[Collections.Generic.List[string]]::new()
 if(@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count){$errors.Add('Game started; rollback deferred')}
 else{foreach($p in $written){try{if($null -ne $p.old){$saved=Within (Join-Path $backup $p.relative) $backup;Match $saved $p.old;Copy-Item -LiteralPath $saved -Destination $p.target -Force;Match $p.target $p.old}elseif(Test-Path -LiteralPath $p.target){$dest=Within (Join-Path $backup ('failed_additions\'+$p.relative)) $backup;New-Item -ItemType Directory -Force (Split-Path $dest)|Out-Null;Move-Item -LiteralPath $p.target -Destination $dest}}catch{$errors.Add($_.Exception.Message)}}}
 [IO.File]::WriteAllText((Join-Path $audit 'install_failure.json'),(@{status='FAILED';failure=$failure;rollback_errors=@($errors);backup=$backup}|ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false));throw ($failure+'; rollback errors: '+($errors -join '; '))
}
