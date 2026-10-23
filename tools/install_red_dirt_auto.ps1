param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),[string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if(@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Game must be closed'}
$game=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
$audit=Join-Path $WorkspaceRoot 'research\b0_red_dirt_auto'
$prior=Get-Content (Join-Path $WorkspaceRoot 'research\b0_mirror_rollout\validation_c5_red_dirt\install_receipt.json') -Raw|ConvertFrom-Json
$pairs=@(
 @('build\RedDirt_Auto\TowerContinued_RedDirt_Auto.archive','archive\pc\mod\TowerContinued_RedDirt_Auto.archive'),
 @('build\RedDirt_Auto\TowerContinued_RedDirt_Auto.archive.xl','archive\pc\mod\TowerContinued_RedDirt_Auto.archive.xl'),
 @('diagnostics\PTFR_RedDirt_Auto\init.lua','bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_RedDirt_Mirror\init.lua'))
$targets=@($pairs|ForEach-Object {Join-Path $game $_[1]})
foreach($t in $targets){if(-not [IO.Path]::GetFullPath($t).StartsWith($game+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Out-of-root target'}}
foreach($i in 0,1){if(Test-Path -LiteralPath $targets[$i]){throw 'Auto target already exists'}}
if($targets[2] -ne $prior.files[2]){throw 'Unexpected helper path'}
foreach($i in 0,1,2){if((Get-FileHash -LiteralPath $prior.files[$i]).Hash -ne $prior.sha256[$i]){throw 'Unexpected C5 foundation; no overwrite'}}
$backup=Join-Path $audit 'opt_in_helper_revision1.lua'
if(Test-Path -LiteralPath $backup){throw 'Backup exists; no overwrite'}
$python='C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
foreach($test in 'test_red_dirt_scene_delta.py','test_red_dirt_auto.py'){
 & $python (Join-Path $PSScriptRoot $test)
 if($LASTEXITCODE -ne 0){throw "Test failed: $test"}
}
$protected=[ordered]@{}
foreach($dir in 'archive\pc\mod','r6\scripts','bin\x64\plugins\cyber_engine_tweaks\mods'){
 foreach($f in Get-ChildItem (Join-Path $game $dir) -Recurse -File|Where-Object {($_.Name -like '*TowerContinued*' -or $_.FullName -match '[\\/]PTFR_') -and $_.FullName -ne $targets[2]}){
  $protected[$f.FullName]=(Get-FileHash -LiteralPath $f.FullName).Hash
 }
}
[IO.File]::Copy($targets[2],$backup,$false)
if((Get-FileHash $backup).Hash -ne $prior.sha256[2]){throw 'Backup mismatch'}
if(@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Game started; abort'}
for($i=0;$i -lt $pairs.Count;$i++){
 New-Item -ItemType Directory -Force -Path (Split-Path -Parent $targets[$i])|Out-Null
 [IO.File]::Copy((Join-Path $WorkspaceRoot $pairs[$i][0]),$targets[$i],($i -eq 2))
 if((Get-FileHash $targets[$i]).Hash -ne (Get-FileHash (Join-Path $WorkspaceRoot $pairs[$i][0])).Hash){throw 'Installed hash mismatch'}
}
foreach($p in $protected.Keys){if((Get-FileHash -LiteralPath $p).Hash -ne $protected[$p]){throw "Protected file changed: $p"}}
$receipt=@{status='INSTALLED_AUTOMATIC_CANDIDATE';utc=[DateTime]::UtcNow.ToString('o');files=$targets;sha256=@($targets|ForEach-Object {(Get-FileHash $_).Hash});preserved_files=$protected.Count;backup=$backup;c5_native_unchanged=$true;save_or_story_fact_change=$false;live_auto_tested=$false}
[IO.File]::WriteAllText((Join-Path $audit 'install_receipt.json'),($receipt|ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false))
$receipt|ConvertTo-Json -Depth 6
