param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),[string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if(@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Game must be closed'}
$game=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
$targets=@('TowerContinued_RemainingMirrors.archive','TowerContinued_RemainingMirrors.archive.xl'|ForEach-Object {Join-Path $game ('archive\pc\mod\'+$_)})
foreach($t in $targets){
 if(-not [IO.Path]::GetFullPath($t).StartsWith($game+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Out-of-root target'}
 if(Test-Path -LiteralPath $t){throw 'Target exists; no overwrite'}
}
& 'C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' (Join-Path $PSScriptRoot 'test_remaining_mirrors.py')
if($LASTEXITCODE -ne 0){throw 'Offline audit failed'}
$protected=[ordered]@{}
foreach($dir in 'archive\pc\mod','r6\scripts','bin\x64\plugins\cyber_engine_tweaks\mods'){
 foreach($f in Get-ChildItem (Join-Path $game $dir) -Recurse -File|Where-Object {$_.Name -like '*TowerContinued*' -or $_.FullName -match '[\\/]PTFR_'}){
  $protected[$f.FullName]=(Get-FileHash -LiteralPath $f.FullName).Hash
 }
}
if(@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Game started; abort'}
foreach($t in $targets){
 $source=Join-Path $WorkspaceRoot ('build\RemainingMirrors\'+[IO.Path]::GetFileName($t))
 [IO.File]::Copy($source,$t,$false)
 if((Get-FileHash $source).Hash -ne (Get-FileHash $t).Hash){throw 'Installed hash mismatch'}
}
foreach($p in $protected.Keys){if((Get-FileHash -LiteralPath $p).Hash -ne $protected[$p]){throw "Protected file changed: $p"}}
$receipt=@{status='INSTALLED_GUARDED_CANDIDATES';utc=[DateTime]::UtcNow.ToString('o');files=$targets;sha256=@($targets|ForEach-Object {(Get-FileHash $_).Hash});preserved_files=$protected.Count;site_ids=@(4,6,12,14,15,19,24,37);live_tested=$false;save_or_story_fact_change=$false}
[IO.File]::WriteAllText((Join-Path $WorkspaceRoot 'research\b0_remaining_mirrors\install_receipt.json'),($receipt|ConvertTo-Json -Depth 5),[Text.UTF8Encoding]::new($false))
$receipt|ConvertTo-Json -Depth 5
