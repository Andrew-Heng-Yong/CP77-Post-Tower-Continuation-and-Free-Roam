param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),[string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',[switch]$ValidateOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\');$game=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
$audit=Join-Path $workspace 'research\misty_viktor_world'
$prior=Get-Content (Join-Path $audit 'access_r11_install_receipt.json') -Raw|ConvertFrom-Json
$m=Get-Content (Join-Path $audit 'population_r12_manifest.json') -Raw|ConvertFrom-Json
$t=Get-Content (Join-Path $audit 'population_r12_tests.json') -Raw|ConvertFrom-Json
function Closed {if(@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Cyberpunk is running; close it before install'}}
function Hash([string]$p){return (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash}
function Match([string]$p,[string]$h){if((Hash $p) -ne $h){throw ('Unexpected hash: '+$p)}}
function Within([string]$p,[string]$r){$full=[IO.Path]::GetFullPath($p);if(-not $full.StartsWith($r+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Path escaped intended root'};return $full}
if($t.status -ne 'PASS_R12_OFFLINE_NOT_LIVE' -or $t.archive_sha256 -ne $m.sha256 -or $t.xl_sha256 -ne $m.xl_sha256 -or $m.status -ne 'BUILT_R12_POPULATION_LIVE_PENDING'){throw 'Missing or stale R12 tests'}
if($prior.files.Count -ne 5){throw 'Unexpected R11 receipt'}
Closed
foreach($p in $prior.files){Match (Within (Join-Path $game $p.relative) $game) $p.sha256}
$diagRel='bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_Zetatech_Access_Audit\init.lua'
$diagOld=@($prior.files|Where-Object {$_.relative -eq $diagRel})[0].sha256
$payloads=@(
 @{relative='archive\pc\mod\TowerContinued_ZetatechPopulationR12.archive';source=$m.archive;sha256=$m.sha256;old=$null},
 @{relative='archive\pc\mod\TowerContinued_ZetatechPopulationR12.archive.xl';source=($m.archive+'.xl');sha256=$m.xl_sha256;old=$null},
 @{relative='r6\scripts\PTFR_Zetatech_Idles_R12\TerryIdleR12.reds';source=(Join-Path $workspace 'redscript\PTFR_Zetatech_Idles_R12\TerryIdleR12.reds');sha256=$t.driver_sha256;old=$null},
 @{relative=$diagRel;source=(Join-Path $workspace 'diagnostics\PTFR_Zetatech_Access_Audit\init.lua');sha256=$t.diagnostic_sha256;old=$diagOld}
)
$targets=@{}
foreach($p in $payloads){$p.source=Within $p.source $workspace;$p.target=Within (Join-Path $game $p.relative) $game;if($targets.ContainsKey($p.target)){throw 'Duplicate target'};$targets[$p.target]=$true;Match $p.source $p.sha256;if($null -eq $p.old){if(Test-Path -LiteralPath $p.target){throw 'Additive destination already exists'}}else{Match $p.target $p.old}}
$protected=[ordered]@{}
foreach($f in Get-ChildItem -LiteralPath (Join-Path $game 'archive\pc\mod') -File -Filter 'TowerContinued*'){if(-not $targets.ContainsKey($f.FullName)){$protected[$f.FullName]=Hash $f.FullName}}
foreach($root in @((Join-Path $game 'r6\scripts'),(Join-Path $game 'bin\x64\plugins\cyber_engine_tweaks\mods'))){foreach($dir in Get-ChildItem -LiteralPath $root -Directory -Filter 'PTFR_*'){foreach($f in Get-ChildItem -LiteralPath $dir.FullName -File -Recurse){if(-not $targets.ContainsKey($f.FullName)){$protected[$f.FullName]=Hash $f.FullName}}}}
foreach($f in Get-ChildItem -LiteralPath (Join-Path $game 'r6\tweaks') -File -Recurse){if(-not $targets.ContainsKey($f.FullName)){$protected[$f.FullName]=Hash $f.FullName}}
function Protected {foreach($p in $protected.Keys){Match $p $protected[$p]}}
Closed;Protected
if($ValidateOnly){[pscustomobject]@{status='VALIDATED_ONLY';additions=3;replacements=1;protected_files=$protected.Count;game_running=$false}|ConvertTo-Json;return}
$backup=Within (Join-Path $audit ('rollback_r11_to_r12_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))) $workspace
New-Item -ItemType Directory -Path $backup|Out-Null
$originalBackup=Within (Join-Path $backup $diagRel) $backup;New-Item -ItemType Directory -Force (Split-Path -Parent $originalBackup)|Out-Null
Copy-Item -LiteralPath (Join-Path $game $diagRel) -Destination $originalBackup;Match $originalBackup $diagOld
$written=[Collections.Generic.List[object]]::new()
try{
 foreach($p in $payloads){Closed;Match $p.source $p.sha256;if($null -eq $p.old){if(Test-Path -LiteralPath $p.target){throw 'New target appeared'}}else{Match $p.target $p.old};New-Item -ItemType Directory -Force (Split-Path -Parent $p.target)|Out-Null;$written.Add($p);Copy-Item -LiteralPath $p.source -Destination $p.target -Force;Match $p.target $p.sha256}
 Closed;Protected
 $receipt=[ordered]@{status='INSTALLED_R12_POPULATION_IDLE_LIVE_PENDING';utc=[DateTime]::UtcNow.ToString('o');files=@($payloads|ForEach-Object {@{relative=$_.relative;sha256=$_.sha256;previous_sha256=$_.old}});rollback_directory=$backup;protected_files=$protected.Count;additions=3;replacements=1;r11_core_unchanged=$true;additional_street_npcs=27;indoor_private_replacements=2;save_writes=0;story_writes=0;scene_starts=0;live_tested=$false}
 [IO.File]::WriteAllText((Join-Path $audit 'population_r12_install_receipt.json'),($receipt|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false));$receipt|ConvertTo-Json -Depth 8
}catch{
 $failure=$_.Exception.Message;$errors=[Collections.Generic.List[string]]::new()
 if(@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count){$errors.Add('Game started; rollback deferred')}
 else{foreach($p in $written){try{if($null -ne $p.old){Copy-Item -LiteralPath $originalBackup -Destination $p.target -Force;Match $p.target $p.old}elseif(Test-Path -LiteralPath $p.target){$dest=Within (Join-Path $backup ('failed_additions\'+$p.relative)) $backup;New-Item -ItemType Directory -Force (Split-Path -Parent $dest)|Out-Null;Move-Item -LiteralPath $p.target -Destination $dest}}catch{$errors.Add($_.Exception.Message)}}}
 $report=@{status='R12_INSTALL_FAILED';failure=$failure;rollback_errors=@($errors);backup=$backup};[IO.File]::WriteAllText((Join-Path $audit 'population_r12_install_failure.json'),($report|ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false));throw ($failure+'; rollback errors: '+($errors -join '; '))
}
