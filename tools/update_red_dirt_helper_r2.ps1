param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),[string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if(@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Game must be closed'}
$game=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
$audit=Join-Path $WorkspaceRoot 'research\b0_mirror_rollout\validation_c5_red_dirt'
$prior=Get-Content (Join-Path $audit 'install_receipt.json') -Raw|ConvertFrom-Json
$target=Join-Path $game 'bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_RedDirt_Mirror\init.lua'
$source=Join-Path $WorkspaceRoot 'diagnostics\PTFR_RedDirt_Mirror\init.lua'
$backup=Join-Path $audit 'helper_revision1.lua'
if(-not $target.StartsWith($game+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Outside game root'}
if($target -ne $prior.files[2] -or (Get-FileHash $target).Hash -ne $prior.sha256[2]){throw 'Unexpected installed helper'}
if(Test-Path -LiteralPath $backup){throw 'Backup exists; do not overwrite'}
$python='C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $python (Join-Path $PSScriptRoot 'test_red_dirt_lua.py')
if($LASTEXITCODE -ne 0){throw 'Lua regression failed'}
$protected=[ordered]@{}
foreach($dir in 'archive\pc\mod','r6\scripts','bin\x64\plugins\cyber_engine_tweaks\mods'){
 foreach($f in Get-ChildItem (Join-Path $game $dir) -Recurse -File|Where-Object {($_.Name -like '*TowerContinued*' -or $_.FullName -match '[\\/]PTFR_') -and $_.FullName -ne $target}){
  $protected[$f.FullName]=(Get-FileHash -LiteralPath $f.FullName).Hash
 }
}
[IO.File]::Copy($target,$backup,$false)
if((Get-FileHash $backup).Hash -ne $prior.sha256[2]){throw 'Backup mismatch'}
if(@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Game started; abort'}
[IO.File]::Copy($source,$target,$true)
if((Get-FileHash $target).Hash -ne (Get-FileHash $source).Hash){throw 'Installed hash mismatch'}
foreach($p in $protected.Keys){if((Get-FileHash -LiteralPath $p).Hash -ne $protected[$p]){throw "Protected file changed: $p"}}
$receipt=@{status='HELPER_REVISION2_INSTALLED';utc=[DateTime]::UtcNow.ToString('o');file=$target;sha256=(Get-FileHash $target).Hash;backup=$backup;preserved_files=$protected.Count;native_files_changed=$false;save_or_story_fact_change=$false;live_tested=$false}
[IO.File]::WriteAllText((Join-Path $audit 'helper_revision2_receipt.json'),($receipt|ConvertTo-Json -Depth 5),[Text.UTF8Encoding]::new($false))
$receipt|ConvertTo-Json -Depth 5
