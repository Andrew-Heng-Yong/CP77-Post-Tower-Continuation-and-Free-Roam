param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),
      [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
      [ValidateSet(3,4)][int]$Revision=3)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if(@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Exit the game before installing'}
$root=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
$audit=Join-Path $WorkspaceRoot 'research\b0_streetkid_seat_mirror_s2'
$previousRevision=$Revision-1
$prior=Get-Content (Join-Path $audit "install_receipt_revision$previousRevision.json") -Raw|ConvertFrom-Json
$manifest=Get-Content (Join-Path $audit 'build_manifest.json') -Raw|ConvertFrom-Json
if($manifest.revision -ne $Revision -or $manifest.status -ne 'ACTION_TEST_BUILT_AFTER_S3_PASS' -or
   -not $manifest.action_install_authorized -or $manifest.resources.Count -ne 3 -or
   $manifest.story_fact_writes.Count -ne 0 -or $manifest.vanilla_replacements.Count -ne 0 -or
   ($manifest.dense_actor_ids -join ',') -ne '0,1,2' -or $manifest.registration_id -ne 51719){throw 'Unreviewed manifest'}
$relative=@('archive\pc\mod\TowerContinued_Streetkid_Seat_Mirror_S2.archive',
 'archive\pc\mod\TowerContinued_Streetkid_Seat_Mirror_S2.archive.xl',
 'bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_Streetkid_Seat_Mirror_S2\init.lua')
$sources=@((Join-Path $WorkspaceRoot 'build\Streetkid_Seat_Mirror_S2\TowerContinued_Streetkid_Seat_Mirror_S2.archive'),
 (Join-Path $WorkspaceRoot 'build\Streetkid_Seat_Mirror_S2\TowerContinued_Streetkid_Seat_Mirror_S2.archive.xl'),
 (Join-Path $WorkspaceRoot 'diagnostics\PTFR_Streetkid_Seat_Mirror_S2\init.lua'))
$targets=@($relative|ForEach-Object {Join-Path $root $_})
for($i=0;$i -lt 3;$i++){
 if(-not [IO.Path]::GetFullPath($targets[$i]).StartsWith($root+'\',[StringComparison]::OrdinalIgnoreCase) -or
    $prior.files[$i] -ne $targets[$i] -or -not (Test-Path -LiteralPath $sources[$i] -PathType Leaf) -or
    (Get-FileHash -LiteralPath $targets[$i] -Algorithm SHA256).Hash -ne $prior.sha256[$i]){throw 'Unexpected installed/source file'}
}
if((Get-FileHash -LiteralPath $sources[0]).Hash -ne $manifest.sha256 -or
   (Get-FileHash -LiteralPath $sources[1]).Hash -ne $manifest.xl_sha256){throw 'Build manifest mismatch'}
$python='C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
foreach($test in 'test_streetkid_seat_mirror_s2.py','test_streetkid_seat_mirror_s2_lua.py'){
 & $python (Join-Path $PSScriptRoot $test)
 if($LASTEXITCODE -ne 0){throw "Test failed: $test"}
}
$backup=Join-Path $audit "revision${previousRevision}_backup"
if(Test-Path -LiteralPath $backup){throw 'Backup exists: refusing overwrite'}
$protected=[ordered]@{}
foreach($dir in 'archive\pc\mod','r6\scripts','bin\x64\plugins\cyber_engine_tweaks\mods'){
 foreach($file in Get-ChildItem -LiteralPath (Join-Path $root $dir) -File -Recurse|Where-Object {
   ($_.Name -like '*TowerContinued*' -or $_.FullName -match '[\\/]PTFR_') -and $_.FullName -notin $targets
 }){$protected[$file.FullName]=(Get-FileHash -LiteralPath $file.FullName).Hash}
}
New-Item -ItemType Directory -Path $backup|Out-Null
for($i=0;$i -lt 3;$i++){
 $path=Join-Path $backup ([IO.Path]::GetFileName($targets[$i]))
 Copy-Item -LiteralPath $targets[$i] -Destination $path
 if((Get-FileHash -LiteralPath $path).Hash -ne $prior.sha256[$i]){throw 'Backup verification failed'}
}
if(@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Game started; installed payload unchanged'}
try {
 for($i=0;$i -lt 3;$i++){
  Copy-Item -LiteralPath $sources[$i] -Destination $targets[$i] -Force
  if((Get-FileHash -LiteralPath $targets[$i]).Hash -ne (Get-FileHash -LiteralPath $sources[$i]).Hash){throw 'Copy mismatch'}
 }
} catch {
 for($i=0;$i -lt 3;$i++){Copy-Item -LiteralPath (Join-Path $backup ([IO.Path]::GetFileName($targets[$i]))) -Destination $targets[$i] -Force}
 throw
}
foreach($path in $protected.Keys){if((Get-FileHash -LiteralPath $path).Hash -ne $protected[$path]){throw "Protected file changed: $path"}}
$receipt=[ordered]@{status='INSTALLED_IDLE';revision=$Revision;installed_utc=[DateTime]::UtcNow.ToString('o');
 files=$targets;sha256=@($targets|ForEach-Object {(Get-FileHash -LiteralPath $_).Hash});
 preserved_files=$protected.Count;backup=$backup;save_or_story_fact_change=$false;live_action_tested=$false}
[IO.File]::WriteAllText((Join-Path $audit "install_receipt_revision$Revision.json"),($receipt|ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false))
$receipt|ConvertTo-Json -Depth 6
