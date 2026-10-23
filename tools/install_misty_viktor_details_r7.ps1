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
$prior=Get-Content (Join-Path $audit 'repair_r6_install_receipt.json') -Raw|ConvertFrom-Json
$manifest=Get-Content (Join-Path $audit 'details_r7_manifest.json') -Raw|ConvertFrom-Json
$tests=Get-Content (Join-Path $audit 'details_r7_tests.json') -Raw|ConvertFrom-Json

function AssertGameClosed {
 if(@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Cyberpunk running; installation deferred'}
}
function AssertHash([string]$Path,[string]$Expected,[string]$Reason){
 if((Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash -ne $Expected){throw ($Reason+': '+$Path)}
}
function RequireWithin([string]$Path,[string]$Root){
 $resolved=[IO.Path]::GetFullPath($Path)
 if(-not $resolved.StartsWith($Root+'\',[StringComparison]::OrdinalIgnoreCase)){throw ('Path escaped intended root: '+$resolved)}
 return $resolved
}
if($manifest.status -ne 'BUILT_R7_DETAILS_NOT_INSTALLED_OR_LIVE' -or
   $tests.status -ne 'PASS_R7_OFFLINE_NOT_LIVE' -or
   $tests.archive_sha256 -ne $manifest.sha256 -or $tests.xl_sha256 -ne $manifest.xl_sha256){throw 'R7 offline tests missing/stale'}
if($prior.status -ne 'INSTALLED_R6_LOCAL_REPAIR_IDLE_OPTIN_LIVE_PENDING' -or $prior.files.Count -ne 3){throw 'R6 installation receipt changed'}
$expectedArchive=Join-Path $workspace 'build\MistyViktorDetailsR7\TowerContinued_MistyViktorShellOptIn.archive'
if([IO.Path]::GetFullPath($manifest.archive) -ne $expectedArchive){throw 'R7 archive source escaped prescribed build'}
$files=@(
 [pscustomobject]@{relative='archive\pc\mod\TowerContinued_MistyViktorShellOptIn.archive';source=$expectedArchive;hash=$manifest.sha256},
 [pscustomobject]@{relative='archive\pc\mod\TowerContinued_MistyViktorShellOptIn.archive.xl';source=($expectedArchive+'.xl');hash=$manifest.xl_sha256},
 [pscustomobject]@{relative='bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_MistyViktor_World\init.lua';source=(Join-Path $workspace 'diagnostics\PTFR_MistyViktor_World\init.lua');hash=$tests.probe_sha256}
)
AssertGameClosed
$targetHashes=[ordered]@{}
for($i=0;$i -lt $files.Count;$i++){
 $file=$files[$i]
 $target=RequireWithin (Join-Path $game $file.relative) $game
 $source=RequireWithin $file.source $workspace
 if($file.relative -ne $prior.files[$i].relative){throw 'R6 target receipt mismatch'}
 AssertHash $target $prior.files[$i].sha256 'Installed R6 changed'
 AssertHash $source $file.hash 'R7 source changed'
 $targetHashes[$target]=$prior.files[$i].sha256
}
$protected=[ordered]@{}
foreach($file in (Get-ChildItem -LiteralPath (Join-Path $game 'archive\pc\mod') -File -Filter 'TowerContinued*')){
 if(-not $targetHashes.Contains($file.FullName)){$protected[$file.FullName]=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash}
}
foreach($root in @((Join-Path $game 'r6\scripts'),(Join-Path $game 'bin\x64\plugins\cyber_engine_tweaks\mods'))){
 foreach($directory in (Get-ChildItem -LiteralPath $root -Directory -Filter 'PTFR_*')){
  foreach($file in (Get-ChildItem -LiteralPath $directory.FullName -Recurse -File)){
   if(-not $targetHashes.Contains($file.FullName)){$protected[$file.FullName]=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash}
  }
 }
}
function AssertProtected {
 foreach($path in $protected.Keys){AssertHash $path $protected[$path] 'Protected installed file changed'}
}
# Recheck originals after inventory collection. ValidateOnly stops here before
# creating backups, staging files, receipts or any destination write.
foreach($path in $targetHashes.Keys){AssertHash $path $targetHashes[$path] 'Installed R6 changed during validation'}
AssertGameClosed
if($ValidateOnly){
 AssertProtected
 [pscustomobject]@{status='VALIDATED_ONLY_NOT_INSTALLED';r6_targets=$files.Count;protected_files=$protected.Count;originals_unchanged=$true;destination_writes=0;game_running=$false;archive_sha256=$manifest.sha256;probe_sha256=$tests.probe_sha256}|ConvertTo-Json
 return
}
$backup=RequireWithin (Join-Path $audit ('rollback_r6_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')+'_'+[Guid]::NewGuid().ToString('N').Substring(0,8))) $workspace
New-Item -ItemType Directory -Path $backup|Out-Null
for($i=0;$i -lt $files.Count;$i++){
 $target=RequireWithin (Join-Path $game $files[$i].relative) $game
 $saved=RequireWithin (Join-Path $backup $files[$i].relative) $backup
 New-Item -ItemType Directory -Force (Split-Path -Parent $saved)|Out-Null
 AssertHash $target $prior.files[$i].sha256 'R6 target changed before backup'
 Copy-Item -LiteralPath $target -Destination $saved
 AssertHash $saved $prior.files[$i].sha256 'R6 rollback hash mismatch'
}
AssertGameClosed
# Include an index before copying so even a partially written failed copy has a
# verified backup and is included in rollback. Never overwrite unrelated files.
$attempted=[Collections.Generic.List[int]]::new()
try {
 for($i=0;$i -lt $files.Count;$i++){
  AssertGameClosed
  $target=RequireWithin (Join-Path $game $files[$i].relative) $game
  AssertHash $target $prior.files[$i].sha256 'R6 target changed before replacement'
  AssertHash $files[$i].source $files[$i].hash 'R7 source changed before replacement'
  $attempted.Add($i)
  Copy-Item -LiteralPath $files[$i].source -Destination $target -Force
  AssertHash $target $files[$i].hash 'R7 installed hash mismatch'
 }
 AssertProtected
 AssertGameClosed
 $receipt=[ordered]@{
  status='INSTALLED_R7_DETAILS_IDLE_OPTIN_LIVE_PENDING';utc=[DateTime]::UtcNow.ToString('o')
  files=@($files|ForEach-Object {@{relative=$_.relative;sha256=$_.hash}})
  rollback_directory=$backup;protected_files=$protected.Count;private_sector_count=$manifest.private_sector_count;private_block_count=$manifest.private_block_count
  terminal_retained_on_stop=$manifest.terminal_retained_on_stop;crowd_ref=$manifest.crowd_ref
  explicit_character_spawners=0;vehicle_spawners=$manifest.truck_spawners;native_scene_starts=0;story_fact_writes=0;save_files_modified=$false;gameplay_commands_executed=0;live_tested=$false
 }
 [IO.File]::WriteAllText((Join-Path $audit 'details_r7_install_receipt.json'),($receipt|ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false))
 $receipt|ConvertTo-Json -Depth 5
} catch {
 $failure=$_.Exception.Message
 $rollbackErrors=[Collections.Generic.List[string]]::new()
 $restored=[Collections.Generic.List[string]]::new()
 # If the game was launched during installation, do not mutate files beneath
 # it. Preserve all exact backups and report the deferred rollback explicitly.
 $running=@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count -gt 0
 if($running -and $attempted.Count){$rollbackErrors.Add('Cyberpunk started during installation; rollback deferred until the game is closed')}
 else {
  for($j=$attempted.Count-1;$j -ge 0;$j--){
   $i=$attempted[$j]
   $target=RequireWithin (Join-Path $game $files[$i].relative) $game
   $saved=RequireWithin (Join-Path $backup $files[$i].relative) $backup
   try {
    AssertGameClosed
    AssertHash $saved $prior.files[$i].sha256 'Rollback backup changed'
    Copy-Item -LiteralPath $saved -Destination $target -Force
    AssertHash $target $prior.files[$i].sha256 'Rollback target verification failed'
    $restored.Add($files[$i].relative)
   } catch {$rollbackErrors.Add($files[$i].relative+': '+$_.Exception.Message)}
  }
 }
 $originalsRestored=$true
 foreach($path in $targetHashes.Keys){
  try{AssertHash $path $targetHashes[$path] 'Original R6 target not restored'}catch{$originalsRestored=$false;$rollbackErrors.Add($_.Exception.Message)}
 }
 try{AssertProtected}catch{$rollbackErrors.Add($_.Exception.Message)}
 $failed=[ordered]@{status='R7_INSTALL_FAILED';utc=[DateTime]::UtcNow.ToString('o');failure=$failure;rollback_directory=$backup;attempted=@($attempted);restored=@($restored);original_r6_targets_restored=$originalsRestored;rollback_errors=@($rollbackErrors);game_running=$running}
 try{[IO.File]::WriteAllText((Join-Path $audit 'details_r7_failed_install_receipt.json'),($failed|ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false))}catch{Write-Warning ('Could not write failure receipt: '+$_.Exception.Message)}
 $failed|ConvertTo-Json -Depth 5|Write-Output
 throw ('R7 installation failed: '+$failure+'. Original R6 targets restored='+$originalsRestored+'. Backups: '+$backup)
}
