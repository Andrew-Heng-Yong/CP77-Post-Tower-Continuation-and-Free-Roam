param(
 [string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),
 [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
 [switch]$ValidateOnly,
 [switch]$Install
)
# Default is read-only preflight. Use -Install only after installation approval.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if($Install -and $ValidateOnly){throw 'Choose installation OR validation'}
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\');$game=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
$audit=Join-Path $workspace 'research\afterlife_world\population_r2'
$m=Get-Content (Join-Path $audit 'manifest.json') -Raw|ConvertFrom-Json -Depth 50
$t=Get-Content (Join-Path $audit 'tests.json') -Raw|ConvertFrom-Json
$old=Get-Content (Join-Path $workspace 'research\afterlife_world\install_receipt.json') -Raw|ConvertFrom-Json
function Hash([string]$p){return (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash}
function Match([string]$p,[string]$h){if((Hash $p) -ne $h){throw "Unexpected hash: $p"}}
function Closed {if(@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Close Cyberpunk before preflight/install'}}
function Within([string]$p,[string]$root){$full=[IO.Path]::GetFullPath($p);if(-not $full.StartsWith($root+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Path escaped intended root'};return $full}
if($old.status -ne 'INSTALLED_AFTERLIFE_R1_LIVE_PENDING' -or $old.files.Count -ne 6){throw 'Unexpected R1 baseline receipt'}
if($t.status -ne 'PASS_R2_OFFLINE_NOT_INSTALLED_NOT_LIVE' -or $t.archive_sha256 -ne $m.sha256 -or $t.xl_sha256 -ne $m.xl_sha256){throw 'Missing/stale R2 tests'}
Match (Join-Path $audit 'manifest.json') $t.manifest_sha256
Match (Join-Path $workspace 'tools\build_afterlife_population_r2.ps1') $t.builder_sha256
Match (Join-Path $workspace 'tools\test_afterlife_population_r2.py') $t.validator_sha256
if(-not (Test-Path -LiteralPath (Join-Path $game 'r6\cache\final.redscripts') -PathType Leaf)){throw 'Unexpected game root'}
$payloads=@(
 @{relative='archive\pc\mod\TowerContinued_AfterlifeR1.archive';source=$m.archive;sha256=$m.sha256},
 @{relative='archive\pc\mod\TowerContinued_AfterlifeR1.archive.xl';source=($m.archive+'.xl');sha256=$m.xl_sha256}
)
$targets=@{}
Closed
foreach($p in $old.files){Match (Within (Join-Path $game $p.relative) $game) $p.sha256}
foreach($p in $payloads){$p.source=Within $p.source $workspace;$p.target=Within (Join-Path $game $p.relative) $game;$p.old=@($old.files|Where-Object {$_.relative -eq $p.relative})[0].sha256;Match $p.source $p.sha256;Match $p.target $p.old;$targets[$p.target]=$true}
$protected=[ordered]@{}
foreach($f in Get-ChildItem -LiteralPath (Join-Path $game 'archive\pc\mod') -File -Filter 'TowerContinued*'){if(-not $targets.ContainsKey($f.FullName)){$protected[$f.FullName]=Hash $f.FullName}}
foreach($root in @((Join-Path $game 'r6\scripts'),(Join-Path $game 'bin\x64\plugins\cyber_engine_tweaks\mods'))){foreach($dir in Get-ChildItem -LiteralPath $root -Directory -Filter 'PTFR_*'){foreach($f in Get-ChildItem -LiteralPath $dir.FullName -File -Recurse){if(-not $targets.ContainsKey($f.FullName)){$protected[$f.FullName]=Hash $f.FullName}}}}
foreach($f in Get-ChildItem -LiteralPath (Join-Path $game 'r6\tweaks') -File -Recurse){$protected[$f.FullName]=Hash $f.FullName}
function Protected {foreach($p in $protected.Keys){Match $p $protected[$p]}}
Closed;Protected
if(-not $Install){
 $result=@{status='R2_PREFLIGHT_ONLY_GAME_UNCHANGED';replacements=2;additions=0;protected_files=$protected.Count;archive_sha256=$m.sha256;xl_sha256=$m.xl_sha256;baseline_sha256=@($payloads.old);rollback_baseline_hash_verified=$true;game_running=$false}
 [IO.File]::WriteAllText((Join-Path $audit 'preflight.json'),($result|ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false));$result|ConvertTo-Json -Depth 6;return
}
if(Test-Path -LiteralPath (Join-Path $audit 'install_receipt.json')){throw 'R2 receipt exists; reconcile before another install'}
$backup=Within (Join-Path $audit ('rollback_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))) $workspace
New-Item -ItemType Directory -Path $backup|Out-Null
foreach($p in $payloads){$dest=Within (Join-Path $backup $p.relative) $backup;New-Item -ItemType Directory -Force (Split-Path $dest)|Out-Null;Copy-Item -LiteralPath $p.target -Destination $dest;Match $dest $p.old}
$written=[Collections.Generic.List[object]]::new()
try{
 foreach($p in $payloads){Closed;Match $p.source $p.sha256;Match $p.target $p.old;$written.Add($p);Copy-Item -LiteralPath $p.source -Destination $p.target -Force;Match $p.target $p.sha256}
 Closed;Protected
 $receipt=[ordered]@{status='INSTALLED_AFTERLIFE_POPULATION_R2_LIVE_PENDING';utc=[DateTime]::UtcNow.ToString('o');game_root=$game;rollback_directory=$backup;files=@($payloads|ForEach-Object {@{relative=$_.relative;sha256=$_.sha256;previous_sha256=$_.old}});protected_files=$protected.Count;replacements=2;additions=0;unchanged_r1_payloads=7;save_writes=0;forced_story_writes=0;live_tested=$false}
 [IO.File]::WriteAllText((Join-Path $audit 'install_receipt.json'),($receipt|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false));$receipt|ConvertTo-Json -Depth 8
}catch{
 $failure=$_.Exception.Message;$errors=[Collections.Generic.List[string]]::new()
 if(@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count){$errors.Add('Game started; recovery deferred')}
 else{foreach($p in $written){try{$saved=Within (Join-Path $backup $p.relative) $backup;Match $saved $p.old;Copy-Item -LiteralPath $saved -Destination $p.target -Force;Match $p.target $p.old}catch{$errors.Add($_.Exception.Message)}}}
 [IO.File]::WriteAllText((Join-Path $audit 'install_failure.json'),(@{status='FAILED';failure=$failure;rollback_errors=@($errors);backup=$backup}|ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false));throw ($failure+'; recovery errors: '+($errors -join '; '))
}
