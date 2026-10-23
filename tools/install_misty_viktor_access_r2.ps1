param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue){throw 'Game running'}
$gameRoot=[IO.Path]::GetFullPath('C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
$audit=Join-Path $WorkspaceRoot 'research\misty_viktor_world'
$prior=Get-Content (Join-Path $audit 'revision1\install_receipt.json') -Raw|ConvertFrom-Json
$tests=Get-Content (Join-Path $audit 'access_r2_tests.json') -Raw|ConvertFrom-Json
$m=Get-Content (Join-Path $audit 'access_r2_manifest.json') -Raw|ConvertFrom-Json
if($tests.status -ne 'PASS_R2_OFFLINE_NOT_LIVE' -or $tests.archive_sha256 -ne $m.sha256){throw 'Tests absent/stale'}
$sources=@($m.archive,($m.archive+'.xl'),(Join-Path $WorkspaceRoot 'diagnostics\PTFR_MistyViktor_World\init.lua'))
$hashes=@($tests.archive_sha256,$tests.xl_sha256,$tests.probe_sha256)
$backup=Join-Path $audit ('rollback_r1_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ'))
foreach($property in $prior.prior_hashes.PSObject.Properties){if((Get-FileHash -LiteralPath $property.Name).Hash -ne $property.Value){throw "Protected file changed: $($property.Name)"}}
for($i=0;$i -lt 3;$i++){
  $target=[IO.Path]::GetFullPath((Join-Path $gameRoot $prior.files[$i].relative))
  if(-not $target.StartsWith($gameRoot+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Target escapes game'}
  if((Get-FileHash -LiteralPath $target).Hash -ne $prior.files[$i].sha256){throw 'Installed R1 does not match receipt'}
  if((Get-FileHash -LiteralPath $sources[$i]).Hash -ne $hashes[$i]){throw 'New source changed after tests'}
}
New-Item -ItemType Directory -Force $backup|Out-Null
for($i=0;$i -lt 3;$i++){
  $target=Join-Path $gameRoot $prior.files[$i].relative
  $saved=Join-Path $backup $prior.files[$i].relative
  New-Item -ItemType Directory -Force (Split-Path -Parent $saved)|Out-Null
  Copy-Item -LiteralPath $target -Destination $saved
  if((Get-FileHash -LiteralPath $saved).Hash -ne $prior.files[$i].sha256){throw 'Rollback backup mismatch'}
}
if(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue){throw 'Game started; deferred'}
$installed=@();$changed=0
for($i=0;$i -lt 3;$i++){
  $target=Join-Path $gameRoot $prior.files[$i].relative
  if($hashes[$i] -ne $prior.files[$i].sha256){Copy-Item -LiteralPath $sources[$i] -Destination $target -Force;$changed++}
  if((Get-FileHash -LiteralPath $target).Hash -ne $hashes[$i]){throw 'Installed hash mismatch'}
  $installed+=@{relative=$prior.files[$i].relative;sha256=$hashes[$i]}
}
foreach($property in $prior.prior_hashes.PSObject.Properties){if((Get-FileHash -LiteralPath $property.Name).Hash -ne $property.Value){throw "Protected file changed: $($property.Name)"}}
$receipt=[ordered]@{status='INSTALLED_R2_IDLE_OPTIN_LIVE_PENDING';utc=[DateTime]::UtcNow.ToString('o');files=$installed;changed_files=$changed;unchanged_registration=$true;prior_project_files_preserved=$prior.prior_project_files_preserved;rollback_directory=$backup;geometry_changed=$false;gameplay_commands_executed=0;save_files_modified=$false;live_tested=$false}
[IO.File]::WriteAllText((Join-Path $audit 'access_r2_install_receipt.json'),($receipt|ConvertTo-Json -Depth 5))
$receipt|ConvertTo-Json -Depth 4
