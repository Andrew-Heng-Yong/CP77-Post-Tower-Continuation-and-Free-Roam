param(
 [string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),
 [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
 [switch]$ValidateOnly
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\')
$game=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
$audit=Join-Path $workspace 'research\misty_viktor_world'
$prior=Get-Content (Join-Path $audit 'details_r7_install_receipt.json') -Raw|ConvertFrom-Json
$manifest=Get-Content (Join-Path $audit 'access_r9_manifest.json') -Raw|ConvertFrom-Json
$tests=Get-Content (Join-Path $audit 'access_r9_tests.json') -Raw|ConvertFrom-Json
$previousR9Path=Join-Path $audit 'access_r9_install_receipt.json'

function AssertGameClosed {if(@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Cyberpunk running; installation deferred'}}
function AssertHash([string]$Path,[string]$Expected,[string]$Reason){if((Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash -ne $Expected){throw ($Reason+': '+$Path)}}
function RequireWithin([string]$Path,[string]$Root){$resolved=[IO.Path]::GetFullPath($Path);if(-not $resolved.StartsWith($Root+'\',[StringComparison]::OrdinalIgnoreCase)){throw ('Path escaped intended root: '+$resolved)};return $resolved}

if($manifest.status -ne 'BUILT_R9_ACCESS_CLERK_NOT_INSTALLED_OR_LIVE' -or $tests.status -ne 'PASS_R9_OFFLINE_NOT_LIVE' -or
   $tests.archive_sha256 -ne $manifest.sha256 -or $tests.xl_sha256 -ne $manifest.xl_sha256){throw 'R9 offline tests missing or stale'}
if($prior.status -ne 'INSTALLED_R7_DETAILS_IDLE_OPTIN_LIVE_PENDING' -or $prior.files.Count -ne 3){throw 'R7 installation receipt changed'}
$source=RequireWithin (Join-Path $workspace 'build\MistyViktorAccessR9\TowerContinued_MistyViktorShellOptIn.archive') $workspace
$target=RequireWithin (Join-Path $game 'archive\pc\mod\TowerContinued_MistyViktorShellOptIn.archive') $game
$relative='archive\pc\mod\TowerContinued_MistyViktorShellOptIn.archive'
if($prior.files[0].relative -ne $relative){throw 'R7 archive target changed'}
$installedExpected=$prior.files[0].sha256
$baselineR7Rollback=$null
if(Test-Path -LiteralPath $previousR9Path){
 $previousR9=Get-Content $previousR9Path -Raw|ConvertFrom-Json
 if($previousR9.status -eq 'INSTALLED_R9_ACCESS_CLERK_LIVE_PENDING' -and $previousR9.files.Count -eq 1 -and
    (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash -eq $previousR9.files[0].sha256){
  $installedExpected=$previousR9.files[0].sha256
  $baselineR7Rollback=$previousR9.rollback_directory
 }
}
AssertGameClosed
AssertHash $source $manifest.sha256 'R9 source changed'
AssertHash $target $installedExpected 'Installed predecessor archive changed'

$protected=[ordered]@{}
foreach($file in (Get-ChildItem -LiteralPath (Join-Path $game 'archive\pc\mod') -File -Filter 'TowerContinued*')){if($file.FullName -ne $target){$protected[$file.FullName]=(Get-FileHash $file.FullName -Algorithm SHA256).Hash}}
foreach($root in @((Join-Path $game 'r6\scripts'),(Join-Path $game 'bin\x64\plugins\cyber_engine_tweaks\mods'))){
 foreach($directory in (Get-ChildItem -LiteralPath $root -Directory -Filter 'PTFR_*')){foreach($file in (Get-ChildItem $directory.FullName -Recurse -File)){$protected[$file.FullName]=(Get-FileHash $file.FullName -Algorithm SHA256).Hash}}
}
function AssertProtected {foreach($path in $protected.Keys){AssertHash $path $protected[$path] 'Protected installed file changed'}}
AssertGameClosed;AssertHash $target $installedExpected 'Installed predecessor changed during validation';AssertProtected
if($ValidateOnly){[pscustomobject]@{status='VALIDATED_ONLY_NOT_INSTALLED';targets=1;protected_files=$protected.Count;destination_writes=0;game_running=$false;archive_sha256=$manifest.sha256}|ConvertTo-Json;return}

$backup=RequireWithin (Join-Path $audit ('rollback_pre_r9_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')+'_'+[Guid]::NewGuid().ToString('N').Substring(0,8))) $workspace
New-Item -ItemType Directory -Path $backup|Out-Null
$saved=RequireWithin (Join-Path $backup $relative) $backup
New-Item -ItemType Directory -Force (Split-Path -Parent $saved)|Out-Null
Copy-Item -LiteralPath $target -Destination $saved
AssertHash $saved $installedExpected 'Pre-R9 rollback hash mismatch'
try {
 AssertGameClosed;AssertHash $target $installedExpected 'Predecessor target changed before replacement'
 Copy-Item -LiteralPath $source -Destination $target -Force
 AssertHash $target $manifest.sha256 'R9 installed hash mismatch';AssertProtected;AssertGameClosed
 $receipt=[ordered]@{
  status='INSTALLED_R9_ACCESS_CLERK_LIVE_PENDING';utc=[DateTime]::UtcNow.ToString('o')
  files=@(@{relative=$relative;sha256=$manifest.sha256});unchanged_xl_sha256=$manifest.xl_sha256
  rollback_directory=$backup;baseline_r7_rollback_directory=$baselineR7Rollback;protected_files=$protected.Count
  saved_r7_active_migration=$manifest.saved_r7_active_migration
  door_actions=4;clerk_entries_targeted=1;native_scene_starts=0;story_fact_writes=0;save_files_modified=$false;gameplay_commands_executed=0;live_tested=$false
 }
 [IO.File]::WriteAllText((Join-Path $audit 'access_r9_install_receipt.json'),($receipt|ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false))
 $receipt|ConvertTo-Json -Depth 5
} catch {
 $failure=$_.Exception.Message;$rollbackErrors=[Collections.Generic.List[string]]::new();$restored=$false
 if(@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count){$rollbackErrors.Add('Cyberpunk started during installation; rollback deferred until the game is closed')}
 else {try{AssertHash $saved $installedExpected 'Rollback backup changed';Copy-Item $saved $target -Force;AssertHash $target $installedExpected 'Rollback verification failed';$restored=$true}catch{$rollbackErrors.Add($_.Exception.Message)}}
 $failed=[ordered]@{status='R9_INSTALL_FAILED';utc=[DateTime]::UtcNow.ToString('o');failure=$failure;rollback_directory=$backup;original_r7_archive_restored=$restored;rollback_errors=@($rollbackErrors)}
 [IO.File]::WriteAllText((Join-Path $audit 'access_r9_failed_install_receipt.json'),($failed|ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false))
 $failed|ConvertTo-Json -Depth 5|Write-Output
 throw ('R9 installation failed: '+$failure+'. R7 archive restored='+$restored+'. Backup: '+$backup)
}
