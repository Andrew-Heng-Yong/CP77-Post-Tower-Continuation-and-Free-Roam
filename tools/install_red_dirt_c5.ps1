param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),[string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if(@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Game must be closed'}
$game=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
$audit=Join-Path $WorkspaceRoot 'research\b0_mirror_rollout\validation_c5_red_dirt'
$pairs=@(
 @('build\OrdinaryMirrors_C5_RED_DIRT\TowerContinued_OrdinaryMirrors_C5_RED_DIRT.archive','archive\pc\mod\TowerContinued_OrdinaryMirrors_C5_RED_DIRT.archive'),
 @('build\OrdinaryMirrors_C5_RED_DIRT\TowerContinued_OrdinaryMirrors_C5_RED_DIRT.archive.xl','archive\pc\mod\TowerContinued_OrdinaryMirrors_C5_RED_DIRT.archive.xl'),
 @('diagnostics\PTFR_RedDirt_Mirror\init.lua','bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_RedDirt_Mirror\init.lua'))
$targets=@($pairs|ForEach-Object {Join-Path $game $_[1]})
foreach($t in $targets){
 if(-not [IO.Path]::GetFullPath($t).StartsWith($game+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Out-of-root target'}
 if(Test-Path -LiteralPath $t){throw "Target already exists; no overwrite: $t"}
}
$python='C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
foreach($test in 'test_red_dirt_scene_delta.py','test_red_dirt_lua.py'){
 & $python (Join-Path $PSScriptRoot $test)
 if($LASTEXITCODE -ne 0){throw "Offline test failed: $test"}
}
$protected=[ordered]@{}
foreach($dir in 'archive\pc\mod','r6\scripts','bin\x64\plugins\cyber_engine_tweaks\mods'){
 foreach($f in Get-ChildItem (Join-Path $game $dir) -Recurse -File|Where-Object {$_.Name -like '*TowerContinued*' -or $_.FullName -match '[\\/]PTFR_'}){
  $protected[$f.FullName]=(Get-FileHash -LiteralPath $f.FullName).Hash
 }
}
if(@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Game started; abort'}
for($i=0;$i -lt $pairs.Count;$i++){
 New-Item -ItemType Directory -Force -Path (Split-Path -Parent $targets[$i])|Out-Null
 # No overwrites, including a target created after the preflight.
 [IO.File]::Copy((Join-Path $WorkspaceRoot $pairs[$i][0]),$targets[$i],$false)
 if((Get-FileHash $targets[$i]).Hash -ne (Get-FileHash (Join-Path $WorkspaceRoot $pairs[$i][0])).Hash){throw 'Installed hash mismatch'}
}
foreach($p in $protected.Keys){if((Get-FileHash -LiteralPath $p).Hash -ne $protected[$p]){throw "Protected file changed: $p"}}
$receipt=@{status='INSTALLED_IDLE_OPT_IN';utc=[DateTime]::UtcNow.ToString('o');files=$targets;sha256=@($targets|ForEach-Object {(Get-FileHash $_).Hash});preserved_files=$protected.Count;save_or_story_fact_change=$false;live_tested=$false}
[IO.File]::WriteAllText((Join-Path $audit 'install_receipt.json'),($receipt|ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false))
$receipt|ConvertTo-Json -Depth 6
