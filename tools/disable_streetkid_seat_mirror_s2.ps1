param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),
      [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if (@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count) { throw 'Exit the game first' }
$root=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
$target=Join-Path $root 'archive\pc\mod\TowerContinued_Streetkid_Seat_Mirror_S2.archive.xl'
$receipt=Get-Content (Join-Path $WorkspaceRoot 'research\b0_streetkid_seat_mirror_s2\install_receipt.json') -Raw|ConvertFrom-Json
if ($receipt.additive_files[1] -ne $target) { throw 'Registration target does not match install receipt' }
if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash -ne $receipt.additive_sha256[1]) { throw 'Registration hash changed' }
$backupDir=Join-Path $WorkspaceRoot 'research\b0_streetkid_seat_mirror_s2\disabled_registration'
$backup=Join-Path $backupDir 'TowerContinued_Streetkid_Seat_Mirror_S2.archive.xl'
if (Test-Path -LiteralPath $backup) { throw 'Backup already exists; refusing overwrite' }
$protected=[ordered]@{}
foreach($dir in @((Join-Path $root 'archive\pc\mod'),(Join-Path $root 'r6\scripts'),(Join-Path $root 'bin\x64\plugins\cyber_engine_tweaks\mods'))) {
  foreach($file in Get-ChildItem -LiteralPath $dir -File -Recurse | Where-Object {($_.Name -like '*TowerContinued*' -or $_.FullName -match '[\\/]PTFR_') -and $_.FullName -ne $target}) {
    $protected[$file.FullName]=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
  }
}
New-Item -ItemType Directory -Force -Path $backupDir|Out-Null
Move-Item -LiteralPath $target -Destination $backup -ErrorAction Stop
if ((Test-Path -LiteralPath $target) -or (Get-FileHash -LiteralPath $backup -Algorithm SHA256).Hash -ne $receipt.additive_sha256[1]) { throw 'Disable verification failed' }
foreach($path in $protected.Keys) {
  if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $protected[$path]) { throw "Other component changed: $path" }
}
$result=[ordered]@{status='REGISTRATION_DISABLED';disabled_utc=[DateTime]::UtcNow.ToString('o');original_path=$target;recoverable_backup=$backup;sha256=$receipt.additive_sha256[1];preserved_files=$protected.Count;save_or_story_fact_change=$false}
[IO.File]::WriteAllText((Join-Path $WorkspaceRoot 'research\b0_streetkid_seat_mirror_s2\disable_receipt.json'),($result|ConvertTo-Json),[Text.UTF8Encoding]::new($false))
$result|ConvertTo-Json
