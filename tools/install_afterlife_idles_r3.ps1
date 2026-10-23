param(
 [string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),
 [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
 [switch]$Install,
 [switch]$ValidateOnly
)
# Additive only. The default performs checks, never installs.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if($Install -and $ValidateOnly){throw 'Choose installation OR validation'}
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\');$game=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
$audit=Join-Path $workspace 'research\afterlife_world\idles_r3'
function Hash([string]$p){return (Get-FileHash -LiteralPath $p).Hash}
function Match([string]$p,[string]$h){if((Hash $p) -ne $h){throw "Hash mismatch: $p"}}
function Within([string]$p,[string]$root){$v=[IO.Path]::GetFullPath($p);if(-not $v.StartsWith($root+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Path escaped intended root'};return $v}
function Closed {if(@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Close Cyberpunk before installing or validating deployment'}}
$m=Get-Content (Join-Path $audit 'manifest.json') -Raw|ConvertFrom-Json -Depth 40
$t=Get-Content (Join-Path $audit 'tests.json') -Raw|ConvertFrom-Json
if($t.status -ne 'PASS_R3_OFFLINE_NOT_INSTALLED_NOT_LIVE' -or $t.archive_sha256 -ne $m.sha256 -or $t.xl_sha256 -ne $m.xl_sha256){throw 'Missing/stale R3 tests'}
Match (Join-Path $audit 'manifest.json') $t.manifest_sha256
Match (Join-Path $workspace 'tools\build_afterlife_idles_r3.ps1') $t.builder_sha256
Match (Join-Path $workspace 'tools\test_afterlife_idles_r3.py') $t.validator_sha256
if(-not (Test-Path -LiteralPath (Join-Path $game 'r6\cache\final.redscripts') -PathType Leaf)){throw 'Unexpected game root'}
$payloads=@(
 @{relative='archive\pc\mod\TowerContinued_AfterlifeIdlesR3.archive';source=$m.archive;sha256=$m.sha256},
 @{relative='archive\pc\mod\TowerContinued_AfterlifeIdlesR3.archive.xl';source=($m.archive+'.xl');sha256=$m.xl_sha256},
 @{relative='r6\scripts\PTFR_Afterlife_Idles_R3\AfterlifeIdlesR3.reds';source=(Join-Path $workspace 'redscript\PTFR_Afterlife_Idles_R3\AfterlifeIdlesR3.reds');sha256=$t.driver_sha256},
 @{relative='bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_Afterlife_Behavior_Audit\init.lua';source=(Join-Path $workspace 'diagnostics\PTFR_Afterlife_Behavior_Audit\init.lua');sha256=$t.diagnostic_sha256}
)
Closed
$expected=[ordered]@{}
foreach($receipt in @('research\afterlife_world\install_receipt.json','research\afterlife_world\population_r2\install_receipt.json')){
 $r=Get-Content (Join-Path $workspace $receipt) -Raw|ConvertFrom-Json
 foreach($p in $r.files){$expected[$p.relative]=$p.sha256}
}
foreach($p in $expected.Keys){Match (Within (Join-Path $game $p) $game) $expected[$p]}
foreach($p in $payloads){$p.source=Within $p.source $workspace;$p.target=Within (Join-Path $game $p.relative) $game;Match $p.source $p.sha256;if(Test-Path -LiteralPath $p.target){throw "Additive destination exists: $($p.target)"}}
$protected=[ordered]@{}
foreach($f in Get-ChildItem -LiteralPath (Join-Path $game 'archive\pc\mod') -File -Filter 'TowerContinued*'){$protected[$f.FullName]=Hash $f.FullName}
foreach($root in @((Join-Path $game 'r6\scripts'),(Join-Path $game 'bin\x64\plugins\cyber_engine_tweaks\mods'))){foreach($dir in Get-ChildItem -LiteralPath $root -Directory -Filter 'PTFR_*'){foreach($f in Get-ChildItem -LiteralPath $dir.FullName -File -Recurse){$protected[$f.FullName]=Hash $f.FullName}}}
foreach($f in Get-ChildItem -LiteralPath (Join-Path $game 'r6\tweaks') -File -Recurse){$protected[$f.FullName]=Hash $f.FullName}
function Protected {foreach($p in $protected.Keys){Match $p $protected[$p]}}
Closed;Protected
if(-not $Install){
 $result=@{status='R3_PREFLIGHT_ONLY_GAME_UNCHANGED';additions=4;replacements=0;protected_files=$protected.Count;game_running=$false;archive_sha256=$m.sha256}
 [IO.File]::WriteAllText((Join-Path $audit 'preflight.json'),($result|ConvertTo-Json),[Text.UTF8Encoding]::new($false));$result|ConvertTo-Json;return
}
if(Test-Path -LiteralPath (Join-Path $audit 'install_receipt.json')){throw 'Receipt exists; reconcile before another install'}
$written=[Collections.Generic.List[object]]::new()
try{
 foreach($p in $payloads){Closed;Match $p.source $p.sha256;if(Test-Path -LiteralPath $p.target){throw 'Destination appeared during install'};New-Item -ItemType Directory -Force (Split-Path $p.target)|Out-Null;[IO.File]::Copy($p.source,$p.target,$false);$written.Add($p);Match $p.target $p.sha256}
 Closed;Protected
 $receipt=[ordered]@{status='INSTALLED_AFTERLIFE_IDLES_R3_LIVE_PENDING';utc=[DateTime]::UtcNow.ToString('o');game_root=$game;additions=4;replacements=0;protected_files=$protected.Count;protected_hashes=$protected;files=@($payloads|ForEach-Object {@{relative=$_.relative;sha256=$_.sha256}});save_writes=0;story_writes=0;live_tested=$false}
 [IO.File]::WriteAllText((Join-Path $audit 'install_receipt.json'),($receipt|ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false))
 [pscustomobject]$receipt|Select-Object status,utc,additions,replacements,protected_files|ConvertTo-Json
}catch{
 # Recover only files actually written by this invocation, into the workspace.
 $failure=$_.Exception.Message;$errors=[Collections.Generic.List[string]]::new()
 $recovery=Within (Join-Path $audit ('failed_install_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))) $workspace
 if(@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count){$errors.Add('Game started; recovery deferred')}
 else{foreach($p in $written){try{if(Test-Path -LiteralPath $p.target){Match $p.target $p.sha256;$dest=Within (Join-Path $recovery $p.relative) $recovery;New-Item -ItemType Directory -Force (Split-Path $dest)|Out-Null;Move-Item -LiteralPath $p.target -Destination $dest}}catch{$errors.Add($_.Exception.Message)}}}
 [IO.File]::WriteAllText((Join-Path $audit 'install_failure.json'),(@{failure=$failure;recovery=$recovery;errors=@($errors)}|ConvertTo-Json -Depth 4),[Text.UTF8Encoding]::new($false));throw ($failure+'; recovery errors: '+($errors -join '; '))
}
