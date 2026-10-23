param(
 [string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),
 [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
 [switch]$ValidateOnly
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\')
$game=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
$audit=Join-Path $workspace 'research\misty_viktor_world'
$prior=Get-Content (Join-Path $audit 'access_r10_install_receipt.json') -Raw|ConvertFrom-Json
$manifest=Get-Content (Join-Path $audit 'access_r11_manifest.json') -Raw|ConvertFrom-Json
$tests=Get-Content (Join-Path $audit 'access_r11_tests.json') -Raw|ConvertFrom-Json
$terry=Get-Content (Join-Path $audit 'terry_r11_manifest.json') -Raw|ConvertFrom-Json
function Closed {if(@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Cyberpunk running; install deferred'}}
function Hash([string]$path){return (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash}
function MatchHash([string]$path,[string]$expected){if((Hash $path) -ne $expected){throw ('Hash changed: '+$path)}}
function Within([string]$path,[string]$root){$p=[IO.Path]::GetFullPath($path);if(-not $p.StartsWith($root+'\',[StringComparison]::OrdinalIgnoreCase)){throw ('Path escaped intended root: '+$p)};return $p}
if($manifest.status -ne 'BUILT_R11_DOORS_STREET_COUNTERSTAFF_LIVE_PENDING' -or $tests.status -ne 'PASS_R11_OFFLINE_NOT_LIVE' -or $tests.archive_sha256 -ne $manifest.sha256 -or $tests.xl_sha256 -ne $manifest.xl_sha256){throw 'R11 tests missing or stale'}
if($prior.status -ne 'INSTALLED_R10_STREAMED_DOORS_STREET_NPC_LIVE_PENDING' -or $prior.files.Count -ne 1){throw 'R10 receipt changed'}
if(-not $terry.tests_pass -or $terry.payloads.Count -ne 2){throw 'Terry source checks missing'}
$payloads=[Collections.Generic.List[object]]::new()
$relative='archive\pc\mod\TowerContinued_MistyViktorShellOptIn.archive'
$payloads.Add(@{relative=$relative;source=$manifest.archive;sha256=$manifest.sha256;old=$prior.files[0].sha256})
$payloads.Add(@{relative=($relative+'.xl');source=($manifest.archive+'.xl');sha256=$manifest.xl_sha256;old=$prior.unchanged_xl_sha256})
$diagnostic=Join-Path $workspace 'diagnostics\PTFR_Zetatech_Access_Audit\init.lua'
$payloads.Add(@{relative='bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_Zetatech_Access_Audit\init.lua';source=$diagnostic;sha256=(Hash $diagnostic);old=$null})
foreach($p in $terry.payloads){
 $src=if([IO.Path]::IsPathRooted($p.source)){$p.source}else{Join-Path $workspace $p.source}
 $payloads.Add(@{relative=$p.relative;source=$src;sha256=$p.sha256;old=$null})
}
Closed
$targets=@{}
foreach($p in $payloads){
 $p.source=Within $p.source $workspace;$p.target=Within (Join-Path $game $p.relative) $game
 if($targets.ContainsKey($p.target)){throw 'Duplicate install target'};$targets[$p.target]=$true
 MatchHash $p.source $p.sha256
 if($null -eq $p.old){if(Test-Path -LiteralPath $p.target){throw ('Additive target already exists: '+$p.target)}}else{MatchHash $p.target $p.old}
}
$protected=[ordered]@{}
foreach($f in Get-ChildItem -LiteralPath (Join-Path $game 'archive\pc\mod') -File -Filter 'TowerContinued*'){
 if(-not $targets.ContainsKey($f.FullName)){$protected[$f.FullName]=Hash $f.FullName}
}
foreach($root in @((Join-Path $game 'r6\scripts'),(Join-Path $game 'bin\x64\plugins\cyber_engine_tweaks\mods'))){
 foreach($dir in Get-ChildItem -LiteralPath $root -Directory -Filter 'PTFR_*'){
  foreach($f in Get-ChildItem -LiteralPath $dir.FullName -File -Recurse){if(-not $targets.ContainsKey($f.FullName)){$protected[$f.FullName]=Hash $f.FullName}}
 }
}
foreach($f in Get-ChildItem -LiteralPath (Join-Path $game 'r6\tweaks') -File -Recurse){if(-not $targets.ContainsKey($f.FullName)){$protected[$f.FullName]=Hash $f.FullName}}
function Protected {foreach($p in $protected.Keys){MatchHash $p $protected[$p]}}
Closed;Protected
if($ValidateOnly){[pscustomobject]@{status='VALIDATED_ONLY_NOT_INSTALLED';replacements=2;additions=3;protected_files=$protected.Count;game_running=$false;archive_sha256=$manifest.sha256}|ConvertTo-Json;return}
$backup=Within (Join-Path $audit ('rollback_r10_to_r11_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))) $workspace
New-Item -ItemType Directory -Path $backup|Out-Null
foreach($p in $payloads){if($null -ne $p.old){
 $saved=Within (Join-Path $backup $p.relative) $backup
 New-Item -ItemType Directory -Force (Split-Path -Parent $saved)|Out-Null
 Copy-Item -LiteralPath $p.target -Destination $saved;MatchHash $saved $p.old
}}
$written=[Collections.Generic.List[object]]::new()
try{
 foreach($p in $payloads){
  Closed;MatchHash $p.source $p.sha256
  if($null -ne $p.old){MatchHash $p.target $p.old}elseif(Test-Path -LiteralPath $p.target){throw 'New target appeared during install'}
  New-Item -ItemType Directory -Force (Split-Path -Parent $p.target)|Out-Null
  $written.Add($p);Copy-Item -LiteralPath $p.source -Destination $p.target -Force;MatchHash $p.target $p.sha256
 }
 Closed;Protected
 $receipt=[ordered]@{status='INSTALLED_R11_DOORS_STREET_TERRY_COUNTERSTAFF_LIVE_PENDING';utc=[DateTime]::UtcNow.ToString('o');files=@($payloads|ForEach-Object {@{relative=$_.relative;sha256=$_.sha256;previous_sha256=$_.old}});rollback_directory=$backup;predecessor_receipt='access_r10_install_receipt.json';protected_files=$protected.Count;replacements=2;additions=3;save_writes=0;story_writes=0;scene_starts=0;live_tested=$false}
 [IO.File]::WriteAllText((Join-Path $audit 'access_r11_install_receipt.json'),($receipt|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
 $receipt|ConvertTo-Json -Depth 6
}catch{
 $failure=$_.Exception.Message;$errors=[Collections.Generic.List[string]]::new()
 if(@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count){$errors.Add('Game started; rollback deferred until game closed')}
 else{foreach($p in $written){try{
  $saved=Within (Join-Path $backup $p.relative) $backup
  if($null -ne $p.old){MatchHash $saved $p.old;Copy-Item -LiteralPath $saved -Destination $p.target -Force;MatchHash $p.target $p.old}
  elseif(Test-Path -LiteralPath $p.target){$quarantine=Within (Join-Path $backup ('failed_additions\'+$p.relative)) $backup;New-Item -ItemType Directory -Force (Split-Path -Parent $quarantine)|Out-Null;Move-Item -LiteralPath $p.target -Destination $quarantine}
 }catch{$errors.Add($_.Exception.Message)}}}
 $failed=[ordered]@{status='R11_INSTALL_FAILED';failure=$failure;rollback_directory=$backup;rollback_errors=@($errors)}
 [IO.File]::WriteAllText((Join-Path $audit 'access_r11_failed_install_receipt.json'),($failed|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
 throw ($failure+'; rollback errors: '+($errors -join '; '))
}
