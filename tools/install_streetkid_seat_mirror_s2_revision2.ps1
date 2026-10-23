param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),
      [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if (@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count) { throw 'Exit the game before installing S2 revision2' }
$root=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
$archiveDir=Join-Path $root 'archive\pc\mod'
$cetDir=Join-Path $root 'bin\x64\plugins\cyber_engine_tweaks\mods'
$scriptDir=Join-Path $root 'r6\scripts'
foreach($dir in @($archiveDir,$cetDir,$scriptDir)) {
  if(-not (Test-Path -LiteralPath $dir -PathType Container)) { throw 'Unexpected game root' }
}
$audit=Join-Path $WorkspaceRoot 'research\b0_streetkid_seat_mirror_s2'
$manifest=Get-Content -LiteralPath (Join-Path $audit 'build_manifest.json') -Raw|ConvertFrom-Json
$live=Get-Content -LiteralPath (Join-Path $WorkspaceRoot 'research\b0_streetkid_scene_load_s3\live_revision2_result.json') -Raw|ConvertFrom-Json
if($manifest.status -ne 'ACTION_TEST_BUILT_AFTER_S3_PASS' -or $manifest.revision -ne 2 -or
   -not $manifest.action_install_authorized -or -not $manifest.crash_actor_index_fixed -or
   $manifest.registration_id -ne 51719 -or ($manifest.dense_actor_ids -join ',') -ne '0,1,2' -or
   $manifest.resources.Count -ne 3 -or $manifest.story_fact_writes.Count -ne 0 -or
   $manifest.vanilla_replacements.Count -ne 0 -or $live.status -ne 'PASS_S3_REVISION2') { throw 'Repair/action-test scope or live prerequisite changed' }
$prior=Get-Content -LiteralPath (Join-Path $audit 'install_receipt.json') -Raw|ConvertFrom-Json
$disabled=Get-Content -LiteralPath (Join-Path $audit 'disable_receipt.json') -Raw|ConvertFrom-Json
$build=Join-Path $WorkspaceRoot 'build\Streetkid_Seat_Mirror_S2\TowerContinued_Streetkid_Seat_Mirror_S2.archive'
$pairs=@(
  [pscustomobject]@{Source=$build;Target=(Join-Path $archiveDir 'TowerContinued_Streetkid_Seat_Mirror_S2.archive')},
  [pscustomobject]@{Source=($build+'.xl');Target=(Join-Path $archiveDir 'TowerContinued_Streetkid_Seat_Mirror_S2.archive.xl')},
  [pscustomobject]@{Source=(Join-Path $WorkspaceRoot 'diagnostics\PTFR_Streetkid_Seat_Mirror_S2\init.lua');Target=(Join-Path $cetDir 'PTFR_Streetkid_Seat_Mirror_S2\init.lua')}
)
if((Get-FileHash -LiteralPath $pairs[0].Source -Algorithm SHA256).Hash -ne $manifest.sha256 -or
   (Get-FileHash -LiteralPath $pairs[1].Source -Algorithm SHA256).Hash -ne $manifest.xl_sha256) { throw 'Build differs from reviewed manifest' }
if($disabled.status -ne 'REGISTRATION_DISABLED' -or $disabled.original_path -ne $pairs[1].Target -or
   (Test-Path -LiteralPath $pairs[1].Target) -or
   (Get-FileHash -LiteralPath $disabled.recoverable_backup -Algorithm SHA256).Hash -ne $prior.additive_sha256[1]) { throw 'Unexpected disabled S2 registration state' }
$backupDir=Join-Path $audit 'revision1_backup'
if(Test-Path -LiteralPath $backupDir) { throw 'Prior replacement backup exists; refusing overwrite' }
foreach($pair in $pairs) {
  if(-not (Test-Path -LiteralPath $pair.Source -PathType Leaf) -or
     -not [IO.Path]::GetFullPath($pair.Target).StartsWith($root+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Invalid source/target' }
}
foreach($i in 0,2) {
  if($prior.additive_files[$i] -ne $pairs[$i].Target -or
     (Get-FileHash -LiteralPath $pairs[$i].Target -Algorithm SHA256).Hash -ne $prior.additive_sha256[$i]) { throw 'Old S2 file differs from installation receipt' }
}
$protected=[ordered]@{}
foreach($dir in @($archiveDir,$cetDir,$scriptDir)) {
  foreach($file in Get-ChildItem -LiteralPath $dir -File -Recurse | Where-Object {($_.Name -like '*TowerContinued*' -or $_.FullName -match '[\\/]PTFR_') -and $_.FullName -notin @($pairs[0].Target,$pairs[2].Target)}) {
    $protected[$file.FullName]=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
  }
}
New-Item -ItemType Directory -Path $backupDir|Out-Null
foreach($i in 0,2) {
  $backup=Join-Path $backupDir ([IO.Path]::GetFileName($pairs[$i].Target))
  Copy-Item -LiteralPath $pairs[$i].Target -Destination $backup
  if((Get-FileHash -LiteralPath $backup -Algorithm SHA256).Hash -ne $prior.additive_sha256[$i]) { throw 'Backup verification failed' }
}
if (@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count) { throw 'Game started; no installed payload changed' }
foreach($pair in $pairs) {
  Copy-Item -LiteralPath $pair.Source -Destination $pair.Target -Force
  if((Get-FileHash -LiteralPath $pair.Source -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $pair.Target -Algorithm SHA256).Hash) { throw 'Installed file hash mismatch' }
}
foreach($path in $protected.Keys) {
  if((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $protected[$path]) { throw "Other component changed: $path" }
}
$receipt=[ordered]@{status='INSTALLED_IDLE';revision=2;installed_utc=[DateTime]::UtcNow.ToString('o');
  files=@($pairs|ForEach-Object {$_.Target});sha256=@($pairs|ForEach-Object {(Get-FileHash -LiteralPath $_.Target -Algorithm SHA256).Hash});
  preserved_files=$protected.Count;backup=$backupDir;prerequisite='PASS_S3_REVISION2';
  save_or_story_fact_change=$false;live_action_tested=$false}
[IO.File]::WriteAllText((Join-Path $audit 'install_receipt_revision2.json'),($receipt|ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false))
$receipt|ConvertTo-Json -Depth 6
