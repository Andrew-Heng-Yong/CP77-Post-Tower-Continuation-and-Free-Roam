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
function Inside([string]$path,[string]$root){
 $full=[IO.Path]::GetFullPath($path)
 if(-not $full.StartsWith($root+'\',[StringComparison]::OrdinalIgnoreCase)){throw ('Path escaped target root: '+$full)}
 $cursor=$full
 while($cursor.Length -ge $root.Length){
  if(Test-Path -LiteralPath $cursor){if(((Get-Item -LiteralPath $cursor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw ('Reparse point: '+$cursor)}}
  if($cursor.Equals($root,[StringComparison]::OrdinalIgnoreCase)){break}
  $cursor=[IO.Path]::GetDirectoryName($cursor)
  if(-not $cursor){throw 'Invalid target ancestry'}
 }
 return $full
}
function Closed {if(@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Cyberpunk must be fully closed'}}
function HashIs([string]$path,[string]$sha){
 if($sha -notmatch '^[0-9A-Fa-f]{64}$' -or -not (Test-Path -LiteralPath $path -PathType Leaf) -or (Get-FileHash -LiteralPath $path).Hash -ne $sha){throw ('Missing/hash mismatch: '+$path)}
}
Closed
$manifestPath=Inside (Join-Path $audit 'lighting_r8_package_manifest.json') $workspace
$manifest=Get-Content -LiteralPath $manifestPath -Raw|ConvertFrom-Json
if($manifest.status -ne 'BUILT_R8_AUTOMATIC_PACKAGE_NOT_INSTALLED' -or $manifest.original_alias_changes -ne 12 -or $manifest.private_cold_nodes -ne 5 -or -not $manifest.automatic_neon -or -not $manifest.automatic_police_after_r7 -or -not $manifest.automatic_r7_driver -or -not $manifest.automatic_journal_driver -or -not $manifest.automatic_time_driver -or $manifest.story_fact_writes -ne 0){throw 'R8 package scope mismatch'}
$expectedArchive=Inside (Join-Path $workspace 'build\MistyLightingR8\TowerContinued_MistyLightingR8.archive') $workspace
if([IO.Path]::GetFullPath($manifest.archive) -ne $expectedArchive){throw 'R8 archive source moved'}
$sources=@(
 [pscustomobject]@{relative='archive\pc\mod\TowerContinued_MistyLightingR8.archive';source=$expectedArchive;sha=$manifest.archive_sha256},
 [pscustomobject]@{relative='archive\pc\mod\TowerContinued_MistyLightingR8.archive.xl';source=$expectedArchive+'.xl';sha=$manifest.xl_sha256},
 [pscustomobject]@{relative='r6\scripts\PTFR_MistyViktor_Auto\MistyViktorAuto.reds';source=(Inside (Join-Path $workspace 'redscript\PTFR_MistyViktor_Auto\MistyViktorAuto.reds') $workspace);sha=$manifest.driver_sha256},
 [pscustomobject]@{relative='r6\scripts\PTFR_TowerJournal_Auto\TowerJournalAuto.reds';source=(Inside (Join-Path $workspace 'redscript\PTFR_TowerJournal_Auto\TowerJournalAuto.reds') $workspace);sha=$manifest.journal_driver_sha256},
 [pscustomobject]@{relative='r6\scripts\PTFR_Time_Auto\TimeAuto.reds';source=(Inside (Join-Path $workspace 'redscript\PTFR_Time_Auto\TimeAuto.reds') $workspace);sha=$manifest.time_driver_sha256}
)
foreach($item in $sources){HashIs $item.source $item.sha;$target=Inside (Join-Path $game $item.relative) $game;if(Test-Path -LiteralPath $target){throw ('R8 destination already exists: '+$target)}}
$oldReceiptPath=Inside (Join-Path $audit 'original_lamp_s1_install_receipt.json') $workspace
$old=Get-Content -LiteralPath $oldReceiptPath -Raw|ConvertFrom-Json
if($old.status -ne 'INSTALLED_SINGLETON_ORIGINAL_ALIAS_IDLE_OPTIN_LIVE_PENDING' -or $old.files.Count -ne 3){throw 'S1 receipt mismatch'}
foreach($item in $old.files){HashIs (Inside (Join-Path $game $item.relative) $game) $item.sha256}
foreach($name in @('details_r7_install_receipt.json','light_poc_install_receipt.json')){
 $receipt=Get-Content (Inside (Join-Path $audit $name) $workspace) -Raw|ConvertFrom-Json
 foreach($item in $receipt.files){HashIs (Inside (Join-Path $game $item.relative) $game) $item.sha256}
}
$receiptPath=Inside (Join-Path $audit 'lighting_r8_install_receipt.json') $workspace
if(Test-Path -LiteralPath $receiptPath){throw 'Prior R8 install receipt exists'}
$python='C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$testText=(& $python (Join-Path $workspace 'tools\test_misty_lighting_r8.py') 2>&1|Out-String)
if($LASTEXITCODE -ne 0 -or $testText -notmatch '^PASS: exact 12-alias'){throw ('Offline R8 check failed: '+$testText)}
$cli=Join-Path $workspace 'research\finalboards_dismissal\tooling\redscript-cli.exe'
$lint=(& $cli lint -s $sources[2].source -s $sources[3].source -s $sources[4].source -b (Join-Path $game 'r6\cache\final.redscripts.modded') 2>&1|Out-String)
if($lint -notmatch 'Lint successful' -or $lint -match 'ERROR'){throw ('Automatic drivers did not compile cleanly: '+$lint)}
$protected=[ordered]@{}
$oldPaths=@($old.files|ForEach-Object {Inside (Join-Path $game $_.relative) $game})
foreach($scope in @('archive\pc\mod','r6\scripts','r6\tweaks','bin\x64\plugins\cyber_engine_tweaks\mods')){
 $dir=Inside (Join-Path $game $scope) $game
 if(-not (Test-Path -LiteralPath $dir -PathType Container)){continue}
 foreach($item in (Get-ChildItem -LiteralPath $dir -Recurse -File -Force)){
  $relative=[IO.Path]::GetRelativePath($game,$item.FullName)
  if(@($relative.Split('\')|Where-Object {$_ -like 'TowerContinued*' -or $_ -like 'PTFR_*'}).Count){
   $path=Inside $item.FullName $game
   if($path -notin $oldPaths){$protected[$path]=(Get-FileHash -LiteralPath $path).Hash}
  }
 }
}
function AssertProtected {foreach($path in $protected.Keys){HashIs $path $protected[$path]}}
AssertProtected;Closed
$backup=Inside (Join-Path $audit 'rollback_s1_to_r8') $workspace
foreach($item in $old.files){$saved=Inside (Join-Path $backup $item.relative) $workspace;if(Test-Path -LiteralPath $saved){throw ('S1 recovery destination exists: '+$saved)}}
if($ValidateOnly){@{status='VALIDATED_ONLY_NOT_INSTALLED';r8_additions=5;s1_recoverable_moves=3;protected_files=$protected.Count;game_closed=$true;offline_test='PASS';redscript_lint='PASS'}|ConvertTo-Json;return}
$savedOld=[Collections.Generic.List[object]]::new();$created=[Collections.Generic.List[object]]::new()
try{
 foreach($item in $old.files){
  Closed;AssertProtected
  $from=Inside (Join-Path $game $item.relative) $game
  HashIs $from $item.sha256
  $to=Inside (Join-Path $backup $item.relative) $workspace
  New-Item -ItemType Directory -Path (Split-Path -Parent $to) -Force|Out-Null
  Move-Item -LiteralPath $from -Destination $to -ErrorAction Stop
  $savedOld.Add([pscustomobject]@{source=$from;backup=$to;sha=$item.sha256;relative=$item.relative})
  HashIs $to $item.sha256
 }
 foreach($item in $sources){
  Closed;AssertProtected;HashIs $item.source $item.sha
  $target=Inside (Join-Path $game $item.relative) $game
  if(Test-Path -LiteralPath $target){throw ('R8 target appeared: '+$target)}
  $parent=Inside (Split-Path -Parent $target) $game
  if(-not (Test-Path -LiteralPath $parent -PathType Container)){New-Item -ItemType Directory -Path $parent -Force|Out-Null}
  $temp=Inside ($target+'.'+[Guid]::NewGuid().ToString('N')+'.ptfr-new') $game
  $writer=[IO.File]::Open($temp,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
  try{$reader=[IO.File]::OpenRead($item.source);try{$reader.CopyTo($writer);$writer.Flush($true)}finally{$reader.Dispose()}}finally{$writer.Dispose()}
  HashIs $temp $item.sha;Closed
  [IO.File]::Move($temp,$target)
  $created.Add([pscustomobject]@{path=$target;relative=$item.relative;sha=$item.sha})
  HashIs $target $item.sha
 }
 Closed;AssertProtected
 $data=[ordered]@{status='INSTALLED_R8_AUTOMATIC_LIVE_PENDING';utc=[DateTime]::UtcNow.ToString('o');files=@($sources|ForEach-Object {@{relative=$_.relative;sha256=$_.sha}});s1_recovered=@($old.files|ForEach-Object {@{relative=$_.relative;sha256=$_.sha256}});s1_recovery_root=$backup;replaced_files=0;protected_files=$protected.Count;automatic_neon=$true;automatic_police_after_r7=$true;automatic_r7=$true;automatic_journal=$true;automatic_time=$true;original_alias_count=12;private_cold_nodes=5;story_fact_writes=0;save_files_modified=$false;live_tested=$false;rollback='With game closed, move exact five R8 additions to a recovery folder and restore the three verified S1 files from s1_recovery_root.'}
 $bytes=[Text.UTF8Encoding]::new($false).GetBytes(($data|ConvertTo-Json -Depth 8))
 $stream=[IO.File]::Open($receiptPath,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
 try{$stream.Write($bytes,0,$bytes.Length);$stream.Flush($true)}finally{$stream.Dispose()}
 $data|ConvertTo-Json -Depth 8
}catch{
 $reason=$_.Exception.Message
 if(-not @(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count){
  $recovery=Inside (Join-Path $audit ('failed_r8_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ'))) $workspace
  foreach($item in $created){if(Test-Path -LiteralPath $item.path){HashIs $item.path $item.sha;$to=Inside (Join-Path $recovery $item.relative) $workspace;New-Item -ItemType Directory -Path (Split-Path -Parent $to) -Force|Out-Null;Move-Item -LiteralPath $item.path -Destination $to -ErrorAction Stop}}
  foreach($item in $savedOld){if(Test-Path -LiteralPath $item.backup){HashIs $item.backup $item.sha;New-Item -ItemType Directory -Path (Split-Path -Parent $item.source) -Force|Out-Null;Move-Item -LiteralPath $item.backup -Destination $item.source -ErrorAction Stop}}
 }
 throw ('R8 installation failed and recovery attempted: '+$reason)
}
