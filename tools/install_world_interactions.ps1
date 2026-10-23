param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),[string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if(@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Game must be closed'}
$game=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
$targets=@((Join-Path $game 'archive\pc\mod\TowerContinued_WorldInteractions.archive'),(Join-Path $game 'archive\pc\mod\TowerContinued_WorldInteractions.archive.xl'),(Join-Path $game 'bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_WorldInteractions_Audit\init.lua'))
foreach($t in $targets){if(-not [IO.Path]::GetFullPath($t).StartsWith($game+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Out-of-root target'};if(Test-Path -LiteralPath $t){throw 'Target exists; no overwrite'}}
$python='C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
foreach($test in 'test_world_interactions.py','test_world_interactions_lua.py'){& $python (Join-Path $PSScriptRoot $test);if($LASTEXITCODE -ne 0){throw 'Offline audit failed'}}
$protected=[ordered]@{}
foreach($dir in 'archive\pc\mod','r6\scripts','bin\x64\plugins\cyber_engine_tweaks\mods'){
 foreach($f in Get-ChildItem (Join-Path $game $dir) -Recurse -File|Where-Object {$_.Name -like '*TowerContinued*' -or $_.FullName -match '[\\/]PTFR_'}){$protected[$f.FullName]=(Get-FileHash -LiteralPath $f.FullName).Hash}
}
$sources=@((Join-Path $WorkspaceRoot 'build\WorldInteractions\TowerContinued_WorldInteractions.archive'),(Join-Path $WorkspaceRoot 'build\WorldInteractions\TowerContinued_WorldInteractions.archive.xl'),(Join-Path $WorkspaceRoot 'archive\b0_world_interactions\cet\init.lua'))
foreach($s in $sources){if(-not (Test-Path -LiteralPath $s -PathType Leaf)){throw "Missing source: $s"}}
if(@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Game started; abort'}
for($i=0;$i -lt $targets.Count;$i++){New-Item -ItemType Directory -Force -Path (Split-Path -Parent $targets[$i])|Out-Null;[IO.File]::Copy($sources[$i],$targets[$i],$false);if((Get-FileHash $sources[$i]).Hash -ne (Get-FileHash $targets[$i]).Hash){throw 'Installed hash mismatch'}}
foreach($p in $protected.Keys){if((Get-FileHash -LiteralPath $p).Hash -ne $protected[$p]){throw "Protected file changed: $p"}}
$receipt=@{status='INSTALLED_AUTOMATIC_CANDIDATES';utc=[DateTime]::UtcNow.ToString('o');files=$targets;sha256=@($targets|ForEach-Object {(Get-FileHash $_).Hash});preserved_files=$protected.Count;adapters=@('Radio','Memorial','Coaster');live_tested=$false;save_files_modified=$false;native_fact_changes_at_install=$false}
[IO.File]::WriteAllText((Join-Path $WorkspaceRoot 'research\b0_world_interactions\batch\install_receipt.json'),($receipt|ConvertTo-Json -Depth 5),[Text.UTF8Encoding]::new($false));$receipt|ConvertTo-Json -Depth 5
