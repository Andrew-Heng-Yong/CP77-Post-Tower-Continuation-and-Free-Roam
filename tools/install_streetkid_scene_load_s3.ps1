param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),
      [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
      [switch]$RepairActorIndex)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if (@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count) { throw 'Exit the game before installing S3' }
$root=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
$archiveDir=Join-Path $root 'archive\pc\mod'
$cetDir=Join-Path $root 'bin\x64\plugins\cyber_engine_tweaks\mods'
$scriptDir=Join-Path $root 'r6\scripts'
foreach($dir in @($archiveDir,$cetDir,$scriptDir)) {
  if (-not (Test-Path -LiteralPath $dir -PathType Container)) { throw "Unexpected game root: $dir" }
}
$manifest=Get-Content -LiteralPath (Join-Path $WorkspaceRoot 'research\b0_streetkid_scene_load_s3\build_manifest.json') -Raw|ConvertFrom-Json
$expectedStatus=if($RepairActorIndex){'ACTOR_INDEX_REPAIR_BUILT'}else{'WORKSPACE_ONLY_LOAD_PROBE_UNINSTALLED'}
if ($manifest.status -ne $expectedStatus -or $manifest.registration_id -ne 20431 -or
    $manifest.resources.Count -ne 3 -or $manifest.story_fact_writes.Count -ne 0 -or
    $manifest.vanilla_replacements.Count -ne 0 -or $manifest.action_events -ne 0 -or
    $manifest.choices -ne 0 -or $manifest.workspots -ne 0 -or $manifest.duration_ms -ne 2000 -or
    -not $manifest.repaired_V_acquisition_only -or $manifest.opt_in_fact -ne 'PTFRSKS3_Enabled') { throw 'S3 scope changed' }
if ($RepairActorIndex -and ($manifest.revision -ne 2 -or -not $manifest.crash_actor_index_fixed -or
    ($manifest.dense_actor_ids -join ',') -ne '0,1,2')) { throw 'Actor-index repair contract missing' }
$disabled=Get-Content -LiteralPath (Join-Path $WorkspaceRoot 'research\b0_streetkid_seat_mirror_s2\disable_receipt.json') -Raw|ConvertFrom-Json
$s2Registration=Join-Path $archiveDir 'TowerContinued_Streetkid_Seat_Mirror_S2.archive.xl'
if ($disabled.status -ne 'REGISTRATION_DISABLED' -or $disabled.original_path -ne $s2Registration -or
    (Test-Path -LiteralPath $s2Registration) -or
    (Get-FileHash -LiteralPath $disabled.recoverable_backup -Algorithm SHA256).Hash -ne $disabled.sha256) { throw 'S2 must remain recoverably disabled' }
$archive=Join-Path $WorkspaceRoot 'build\Streetkid_Scene_Load_S3\TowerContinued_Streetkid_Scene_Load_S3.archive'
$xl=$archive+'.xl'
$lua=Join-Path $WorkspaceRoot 'diagnostics\PTFR_Streetkid_Scene_Load_S3\init.lua'
if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash -ne $manifest.sha256 -or
    (Get-FileHash -LiteralPath $xl -Algorithm SHA256).Hash -ne $manifest.xl_sha256) { throw 'Reviewed build hash changed' }
$pairs=@(
  [pscustomobject]@{Source=$archive;Target=(Join-Path $archiveDir 'TowerContinued_Streetkid_Scene_Load_S3.archive')},
  [pscustomobject]@{Source=$xl;Target=(Join-Path $archiveDir 'TowerContinued_Streetkid_Scene_Load_S3.archive.xl')},
  [pscustomobject]@{Source=$lua;Target=(Join-Path $cetDir 'PTFR_Streetkid_Scene_Load_S3\init.lua')}
)
$backupDir=Join-Path $WorkspaceRoot 'research\b0_streetkid_scene_load_s3\revision1_backup'
if($RepairActorIndex) {
  $prior=Get-Content -LiteralPath (Join-Path $WorkspaceRoot 'research\b0_streetkid_scene_load_s3\install_receipt.json') -Raw|ConvertFrom-Json
  $priorDisable=Get-Content -LiteralPath (Join-Path $WorkspaceRoot 'research\b0_streetkid_scene_load_s3\disable_receipt.json') -Raw|ConvertFrom-Json
  if($prior.status -ne 'INSTALLED_IDLE' -or $priorDisable.status -ne 'REGISTRATION_DISABLED' -or
     (Test-Path -LiteralPath $pairs[1].Target) -or (Test-Path -LiteralPath $backupDir)) { throw 'Unexpected S3 recovery state or existing repair backup' }
  foreach($i in 0,2) {
    if($prior.additive_files[$i] -ne $pairs[$i].Target -or
       (Get-FileHash -LiteralPath $pairs[$i].Target -Algorithm SHA256).Hash -ne $prior.additive_sha256[$i]) { throw 'Prior S3 payload differs from receipt' }
  }
  if((Get-FileHash -LiteralPath $priorDisable.recoverable_backup -Algorithm SHA256).Hash -ne $prior.additive_sha256[1]) { throw 'S3 disabled registration backup changed' }
}
foreach($pair in $pairs) {
  if (-not (Test-Path -LiteralPath $pair.Source -PathType Leaf)) { throw "Missing source: $($pair.Source)" }
  if (-not $RepairActorIndex -and (Test-Path -LiteralPath $pair.Target)) { throw "Refusing overwrite: $($pair.Target)" }
  if (-not [IO.Path]::GetFullPath($pair.Target).StartsWith($root+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Target escaped game root' }
}
$protected=[ordered]@{}
foreach($dir in @($archiveDir,$cetDir,$scriptDir)) {
  foreach($file in Get-ChildItem -LiteralPath $dir -File -Recurse | Where-Object {$_.Name -like '*TowerContinued*' -or $_.FullName -match '[\\/]PTFR_'}) {
    if(-not $RepairActorIndex -or $file.FullName -notin @($pairs[0].Target,$pairs[2].Target)) {
      $protected[$file.FullName]=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
    }
  }
}
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $pairs[2].Target)|Out-Null
if($RepairActorIndex) {
  New-Item -ItemType Directory -Path $backupDir|Out-Null
  foreach($i in 0,2) {
    $backupPath=Join-Path $backupDir ([IO.Path]::GetFileName($pairs[$i].Target))
    Copy-Item -LiteralPath $pairs[$i].Target -Destination $backupPath
    if((Get-FileHash -LiteralPath $backupPath -Algorithm SHA256).Hash -ne $prior.additive_sha256[$i]) { throw 'Repair backup mismatch' }
  }
}
if (@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count) { throw 'Game started before installation; no payload changed' }
foreach($pair in $pairs) {
  Copy-Item -LiteralPath $pair.Source -Destination $pair.Target -ErrorAction Stop -Force
  if ((Get-FileHash -LiteralPath $pair.Source -Algorithm SHA256).Hash -ne
      (Get-FileHash -LiteralPath $pair.Target -Algorithm SHA256).Hash) { throw "Copy mismatch: $($pair.Target)" }
}
foreach($path in $protected.Keys) {
  if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $protected[$path]) { throw "Existing component changed: $path" }
}
if (Test-Path -LiteralPath $s2Registration) { throw 'S2 registration unexpectedly present' }
$receipt=[ordered]@{
  status='INSTALLED_IDLE';installed_utc=[DateTime]::UtcNow.ToString('o')
  additive_files=@($pairs|ForEach-Object {$_.Target})
  additive_sha256=@($pairs|ForEach-Object {(Get-FileHash -LiteralPath $_.Target -Algorithm SHA256).Hash})
  preserved_files=$protected.Count;S2_registration_disabled=$true
  save_or_story_fact_change=$false;live_scene_tested=$false;action_events=0
}
if($RepairActorIndex) {
  $receipt.revision=2;$receipt.crash_actor_index_fixed=$true;$receipt.recoverable_payload_backup=$backupDir
}
$receiptName=if($RepairActorIndex){'install_receipt_revision2.json'}else{'install_receipt.json'}
[IO.File]::WriteAllText((Join-Path $WorkspaceRoot ('research\b0_streetkid_scene_load_s3\'+$receiptName)),($receipt|ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false))
$receipt|ConvertTo-Json -Depth 6
