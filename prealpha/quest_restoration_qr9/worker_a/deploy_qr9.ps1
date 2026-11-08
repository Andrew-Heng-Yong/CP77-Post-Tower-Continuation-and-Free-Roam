param(
 [ValidateSet('Core','Diagnostics')][string]$Component='Core',
 [ValidateSet('Preflight','Install','Verify','ValidateRollback','Rollback','Recover')][string]$Action='Preflight',
 [ValidateSet('Before','After')][string]$ExpectedState='After',
 [string]$RecoveryRoot='',
 [string]$ReportFile='',
 [switch]$BackupMaster,
 [string]$FixtureRoot='',
 [string]$FixtureManifest='',
 [string]$FixtureManifestSHA='',
 [string[]]$FixtureProcesses=@(),
 [ValidateSet('','AfterBackup','AfterFirstReplace','BeforeReceipt','AfterStage','AfterFirstRollback','CrashAfterBackup','CrashAfterFirstReplace','CrashBeforeReceipt','CrashAfterFirstRollback','GameStartsAfterFirstReplace','TargetDriftAfterFirstReplace','SaveChangesAfterFirstReplace','ExternalChangesAfterFirstReplace')][string]$FailurePoint=''
)
# Prepared tools only. Codex must never invoke real Install/Rollback/Recover in QR9.
# Writes are exactly the manifest component changes plus its private recovery/report.
# A two-file replacement is journaled, with per-file atomic replacement; Windows
# does not provide a globally atomic pair here. An interrupted journal needs Recover.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$PinnedCoreManifestSHA='06CD479C47E32403371E360092648431EAE1BC93DEE3E61BD6822560133CBCF1'
$PinnedDiagnosticsManifestSHA=''
$worker=[IO.Path]::GetFullPath($PSScriptRoot)
$fixture= -not [string]::IsNullOrWhiteSpace($FixtureRoot)
$script:fakeGameStarted=$false
$script:hashCache=@{}
$script:journal=$null
$script:journalPath=$null
$script:transactionStarted=$false

function Full([string]$p){[IO.Path]::GetFullPath($p).TrimEnd([IO.Path]::DirectorySeparatorChar)}
function NoLinks([string]$p){
 $current=Full $p
 while($current){
  if(Test-Path -LiteralPath $current){$i=Get-Item -LiteralPath $current -Force;if($i.Attributes -band [IO.FileAttributes]::ReparsePoint){throw ('Linked path refused: '+$current)}}
  $parent=[IO.Path]::GetDirectoryName($current);if($parent -eq $current){break};$current=$parent
 }
}
function Beneath([string]$root,[string]$path){
 $r=Full $root;$p=Full $path
 if(-not $p.StartsWith($r+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw ('Path escaped intended root: '+$p)}
 NoLinks $p;return $p
}
function Safe([string]$root,[string]$relative){
 if([string]::IsNullOrWhiteSpace($relative) -or $relative.Contains('\') -or $relative.Contains(':') -or $relative.StartsWith('/')){throw 'Canonical relative path required'}
 foreach($segment in $relative.Split('/')){if($segment -in @('','.','..') -or $segment -notmatch '^[A-Za-z0-9_. -]+$' -or $segment.EndsWith('.') -or $segment.EndsWith(' ')){throw ('Unsafe path segment: '+$relative)}}
 return Beneath $root (Join-Path $root $relative)
}
function Digest([string]$text){$utf8=[Text.UTF8Encoding]::new($false);[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($utf8.GetBytes($text)))}
function FileHash([string]$path,[switch]$Fresh){
 if(-not(Test-Path -LiteralPath $path -PathType Leaf)){return $null}
 NoLinks $path;$f=Get-Item -LiteralPath $path -Force;$key=$f.FullName.ToLowerInvariant();$stamp=[string]$f.Length+':'+[string]$f.LastWriteTimeUtc.Ticks
 if(-not $Fresh -and $script:hashCache.ContainsKey($key) -and $script:hashCache[$key].stamp -eq $stamp){return $script:hashCache[$key].hash}
 $hash=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash;$f.Refresh()
 if($stamp -ne ([string]$f.Length+':'+[string]$f.LastWriteTimeUtc.Ticks)){throw ('Input changed during hash: '+$path)}
 $script:hashCache[$key]=@{stamp=$stamp;hash=$hash};return $hash
}
function Closed {
 $running=@()
 if($fixture){$running=@($FixtureProcesses);if($script:fakeGameStarted){$running+=,'Cyberpunk2077'}}
 else{$running=@(Get-Process -ErrorAction SilentlyContinue|Where-Object {$_.ProcessName -in $manifest.process_names}|ForEach-Object {$_.ProcessName})}
 if($running.Count){throw ('Game or REDlauncher must be closed naturally: '+($running -join ', '))}
}
function EnsureDir([string]$path){NoLinks $path;[void][IO.Directory]::CreateDirectory($path);NoLinks $path}
function CheckFile([string]$path,$expected,[Nullable[long]]$size=$null,[switch]$Fresh){
 if($null -eq $expected){if(Test-Path -LiteralPath $path){throw ('Expected absent path is occupied: '+$path)};return}
 if((FileHash $path -Fresh:$Fresh) -cne $expected){throw ('Hash drift: '+$path)}
 if($null -ne $size -and (Get-Item -LiteralPath $path).Length -ne $size){throw ('Size drift: '+$path)}
}
function CheckManaged([string]$state){
 foreach($row in $manifest.files){$field=if($state -eq 'Before'){'before'}else{'after'};$bytes=if($state -eq 'Before'){$row.before_bytes}else{$row.after_bytes};CheckFile (Safe $game $row.path) $row[$field] $bytes}
}
function CheckDependencies([string]$state){foreach($row in $manifest.required_files){if($state -eq 'Before' -and $row.active_only){continue};CheckFile (Safe $game $row.path) $row.sha256 $row.bytes}}
function CheckPackage {
 foreach($proof in $manifest.proofs){CheckFile $proof.path $proof.sha256}
 foreach($row in $manifest.files){CheckFile (Safe $manifest.package_root $row.path) $row.after $row.after_bytes}
 if($manifest.zip){CheckFile $manifest.zip $manifest.zip_sha256}
 $tree=TreeSnapshot $manifest.package_root -Hashes
 if((@($tree.files|Where-Object {$_.kind -eq 'file'}|ForEach-Object {$_.path}|Sort-Object)-join ',') -cne (@($manifest.files.path|Sort-Object)-join ',')){throw 'Exact source package inventory drift'}
}
function TreeSnapshot([string]$root,[switch]$Hashes,[switch]$SkipManaged){
 NoLinks $root;if(-not(Test-Path -LiteralPath $root -PathType Container)){throw ('Snapshot root missing: '+$root)}
 $pending=[Collections.Generic.Stack[string]]::new();$pending.Push((Full $root));$rows=[Collections.Generic.List[object]]::new()
 while($pending.Count){
  $dir=$pending.Pop()
  foreach($entry in Get-ChildItem -LiteralPath $dir -Force){
   $relative=[IO.Path]::GetRelativePath($root,$entry.FullName).Replace('\','/')
   if($SkipManaged -and $managedSet.Contains($relative)){continue}
   if($entry.Attributes -band [IO.FileAttributes]::ReparsePoint){if($Hashes){throw ('Linked save entry cannot be fully snapshotted: '+$entry.FullName)};$rows.Add([ordered]@{path=$relative;kind='REPARSE_NOT_FOLLOWED';attributes=[long]$entry.Attributes});continue}
   if($entry.PSIsContainer){$pending.Push($entry.FullName);if(-not $SkipManaged -or -not $managedAncestors.Contains($relative)){$rows.Add([ordered]@{path=$relative;kind='directory'})};continue}
   if($Hashes){$rows.Add([ordered]@{path=$relative;kind='file';bytes=$entry.Length;sha256=(FileHash $entry.FullName)})}
   else{$rows.Add([ordered]@{path=$relative;kind='file';bytes=$entry.Length;mtime_utc_ticks=$entry.LastWriteTimeUtc.Ticks})}
  }
 }
 $sorted=@($rows|Sort-Object path);return @{root=(Full $root);files=$sorted;tree_sha256=(Digest ($sorted|ConvertTo-Json -Depth 12 -Compress));mode=$(if($Hashes){'EXACT_NAMES_BYTES_SHA'}else{'NAMES_BYTES_MTIME_REPARSE_METADATA'})}
}
function ProtectionSnapshot {
 $deps=@();foreach($row in $manifest.required_files){$path=Safe $game $row.path;$deps+=,@{path=$row.path;sha256=(FileHash $path);bytes=(Get-Item -LiteralPath $path).Length}}
 return @{saves=(TreeSnapshot $save -Hashes);unmanaged=(TreeSnapshot $game -SkipManaged);dependencies=$deps}
}
function CompareProtection($before,$after){
 if($before.saves.tree_sha256 -cne $after.saves.tree_sha256){throw 'Save names/bytes changed during this transaction; saves were not restored or edited'}
 if($before.unmanaged.tree_sha256 -cne $after.unmanaged.tree_sha256){throw 'Unmanaged game metadata changed during this transaction; unknown files were not restored or edited'}
 if(($before.dependencies|ConvertTo-Json -Compress -Depth 10) -cne ($after.dependencies|ConvertTo-Json -Compress -Depth 10)){throw 'External dependency bytes changed during this transaction'}
}
function WriteJournal {
 $script:journal.updated_utc=[DateTime]::UtcNow.ToString('o');$body=$script:journal|ConvertTo-Json -Depth 60 -Compress
 $envelope=[ordered]@{schema='PTFR_QR9_JOURNAL_V1';payload_json=$body;payload_sha256=(Digest $body)}|ConvertTo-Json -Depth 5
 $temp=Safe $recovery ('journal.'+[Guid]::NewGuid().ToString('N')+'.tmp')
 $utf8=[Text.UTF8Encoding]::new($false);$bytes=$utf8.GetBytes($envelope);$stream=[IO.FileStream]::new($temp,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
 try{$stream.Write($bytes,0,$bytes.Length);$stream.Flush($true)}finally{$stream.Dispose()}
 [IO.File]::Move($temp,$script:journalPath,$true)
}
function ReadJournal {
 $jp=Safe $recovery 'journal.json';if(-not(Test-Path -LiteralPath $jp -PathType Leaf)){throw 'Missing transaction journal; never infer recovery state from a directory name'}
 $envelope=Get-Content -LiteralPath $jp -Raw|ConvertFrom-Json -AsHashtable -Depth 80
 if($envelope.schema -cne 'PTFR_QR9_JOURNAL_V1' -or (Digest $envelope.payload_json) -cne $envelope.payload_sha256){throw 'Corrupt or partial transaction journal'}
 $j=$envelope.payload_json|ConvertFrom-Json -AsHashtable -Depth 70
 if($j.manifest_sha256 -cne $manifestSHA -or $j.component -cne $Component -or $j.game_root -cne $game -or $j.save_root -cne $save){throw 'Journal belongs to another manifest/component/root'}
 return $j
}
function Payload([string]$side,$row){Safe $recovery ($side+'/'+$row.path)}
function CheckRecoveryPayloads {
 foreach($row in $changes){if($null -ne $row.before){CheckFile (Payload 'old' $row) $row.before $row.before_bytes};CheckFile (Payload 'new' $row) $row.after $row.after_bytes}
}
function MasterPlan {
 if($Component -ne 'Core' -or -not $manifest.ContainsKey('master_backup')){throw 'This component has no reviewed master backup plan'}
 $plan=$manifest.master_backup;$slot=Safe $save $plan.slot
 $names=@(Get-ChildItem -LiteralPath $slot -Force -File|ForEach-Object {$_.Name}|Sort-Object)
 if(($names -join ',') -cne (@($plan.files.Keys|Sort-Object)-join ',')){throw 'Selected master file inventory drift'}
 $rows=@();foreach($name in $plan.files.Keys){$r=$plan.files[$name];$src=Safe $slot $name;CheckFile $src $r.sha256 $r.bytes;$rows+=,@{name=$name;source=$src;sha256=$r.sha256;bytes=$r.bytes;backup_relative=('master_before/'+$plan.slot+'/'+$name)}}
 return @{slot=$plan.slot;files=$rows;save_writes=0;automatic_restore=$false}
}
function CreateMasterBackup {
 $plan=MasterPlan
 foreach($row in $plan.files){$dst=Safe $recovery $row.backup_relative;EnsureDir ([IO.Path]::GetDirectoryName($dst));[IO.File]::Copy($row.source,$dst,$false);CheckFile $dst $row.sha256 $row.bytes;$row.backup_sha256=FileHash $dst}
 $script:journal.master_backup=$plan;WriteJournal
}
function CheckMasterBackup {
 if($script:journal.Contains('master_backup') -and $script:journal.master_backup){
  foreach($row in $script:journal.master_backup.files){
   $source=Safe (Safe $save $manifest.master_backup.slot) $row.name
   $expected=$manifest.master_backup.files[$row.name];if(-not $expected){throw 'Unknown master backup receipt file'}
   $backup=Safe $recovery ('master_before/'+$manifest.master_backup.slot+'/'+$row.name)
   CheckFile $backup $expected.sha256 $expected.bytes
   # New working-slot saves are allowed. Original ManualSave-23 must remain intact.
   CheckFile $source $expected.sha256 $expected.bytes
  }
 }
}
function ApplyState($row,[string]$state){
 Closed;$target=Safe $game $row.path;$wanted=if($state -eq 'Before'){$row.before}else{$row.after};$other=if($state -eq 'Before'){$row.after}else{$row.before};$current=FileHash $target -Fresh
 if($current -ceq $wanted){return}
 if($current -cne $other){throw ('Unexpected target state refused: '+$row.path)}
 if($null -eq $wanted){CheckFile $target $other -Fresh;Closed;[IO.File]::Delete($target);if(Test-Path -LiteralPath $target){throw 'Known addon file removal failed'};return}
 $source=Payload $(if($state -eq 'Before'){'old'}else{'new'}) $row;CheckFile $source $wanted
 $stage=Safe $recovery ('stage/'+$state.ToLowerInvariant()+'/'+$row.path);EnsureDir ([IO.Path]::GetDirectoryName($stage))
 if(Test-Path -LiteralPath $stage){CheckFile $stage $wanted}else{[IO.File]::Copy($source,$stage,$false)}
 CheckFile $stage $wanted
 if($state -eq 'After' -and $script:journal.operation -eq 'Install'){Fault 'AfterStage'}
 Closed;$target=Safe $game $row.path;CheckFile $target $other -Fresh
 EnsureDir ([IO.Path]::GetDirectoryName($target))
 if($null -eq $other){[IO.File]::Move($stage,$target,$false)}else{[IO.File]::Replace($stage,$target,[NullString]::Value)}
 CheckFile $target $wanted -Fresh
}
function CleanKnownStages {
 $known=@()
 foreach($row in $changes){foreach($state in @('Before','After')){$p=Safe $recovery ('stage/'+$state.ToLowerInvariant()+'/'+$row.path);if(Test-Path -LiteralPath $p){$h=if($state -eq 'Before'){$row.before}else{$row.after};if($null -eq $h){throw 'Unexpected absent-side stage'};CheckFile $p $h;$known+=,$p}}}
 foreach($p in $known){[IO.File]::Delete($p)}
}
function RestoreActionStart {
 Closed;$state=if($script:journal.operation -eq 'Rollback'){'After'}else{'Before'}
 foreach($row in $changes){$target=Safe $game $row.path;$h=FileHash $target -Fresh;if($h -cne $row.before -and $h -cne $row.after){throw ('Unknown mixed target requires manual review: '+$row.path)}}
 # Only backups needed for actual writes are required; an untouched PREPARING
 # journal can be closed safely even if backup preparation was interrupted.
 foreach($row in $changes){$wanted=if($state -eq 'Before'){$row.before}else{$row.after};if((FileHash (Safe $game $row.path)) -cne $wanted){$source=Payload $(if($state -eq 'Before'){'old'}else{'new'}) $row;if($null -ne $wanted){CheckFile $source $wanted}}}
 foreach($row in $changes){ApplyState $row $state};CheckManaged $state;CleanKnownStages
 $script:journal.state=if($state -eq 'After'){'INSTALLED_VERIFIED'}else{'RESTORED_BEFORE_VERIFIED'};return $state
}
function Fault([string]$point){
 if(-not $fixture){return}
 if($FailurePoint -eq ('Crash'+$point)){[Environment]::Exit(72)}
 if($point -eq 'AfterFirstReplace' -and $FailurePoint -eq 'GameStartsAfterFirstReplace'){$script:fakeGameStarted=$true;throw 'Fixture game-start interruption'}
 if($point -eq 'AfterFirstReplace' -and $FailurePoint -eq 'TargetDriftAfterFirstReplace'){
  $p=Safe $game $changes[0].path;[IO.File]::WriteAllText($p,'FIXTURE_UNKNOWN_CHANGED_BYTES');throw 'Fixture unknown target drift'
 }
 if($point -eq 'AfterFirstReplace' -and $FailurePoint -eq 'SaveChangesAfterFirstReplace'){$p=Safe $save 'OtherSave/sav.dat';[IO.File]::WriteAllText($p,'FIXTURE_HUMAN_SAVE_CHANGE');return}
 if($point -eq 'AfterFirstReplace' -and $FailurePoint -eq 'ExternalChangesAfterFirstReplace'){$p=Safe $game $manifest.required_files[0].path;[IO.File]::WriteAllText($p,'FIXTURE_EXTERNAL_MOD_CHANGE');return}
 if($FailurePoint -ceq $point){throw ('Fixture interruption: '+$point)}
}
function Report($data){
 if($ReportFile){$rp=Beneath $worker $ReportFile;if(Test-Path -LiteralPath $rp){throw 'Never overwrite a report'};EnsureDir ([IO.Path]::GetDirectoryName($rp));[IO.File]::WriteAllText($rp,($data|ConvertTo-Json -Depth 70),[Text.UTF8Encoding]::new($false))}
 $brief=[ordered]@{status=$data.status;component=$Component;action=$Action;managed_paths=$manifest.files.Count;changing_paths=$changes.Count;recovery_root=$recovery;manifest_sha256=$manifestSHA;save_writes=0;game_launches=0;report=$ReportFile};$brief|ConvertTo-Json -Compress
}

# Resolve real paths only from the pinned manifest. Fixture overrides can never
# point outside this worker's explicit fixtures subtree and never follow links.
if($fixture){
 $FixtureRoot=Beneath (Join-Path $worker 'fixtures') $FixtureRoot
 if(-not $FixtureManifest -or $FixtureManifestSHA -notmatch '^[A-Fa-f0-9]{64}$'){throw 'Fixture manifest and exact SHA required'}
 $manifestFile=Beneath $FixtureRoot $FixtureManifest;$expectedManifestSHA=$FixtureManifestSHA.ToUpperInvariant()
}else{
 if($FixtureManifest -or $FixtureManifestSHA -or $FixtureProcesses.Count -or $FailurePoint){throw 'Fixture-only parameter on a real action'}
 $manifestFile=Join-Path $worker $(if($Component -eq 'Core'){'core_manifest_02.json'}else{'diagnostics_manifest_01.json'})
 $expectedManifestSHA=if($Component -eq 'Core'){$PinnedCoreManifestSHA}else{$PinnedDiagnosticsManifestSHA}
 if($expectedManifestSHA -notmatch '^[A-F0-9]{64}$'){throw 'Component is not frozen/review-ready'}
}
CheckFile $manifestFile $expectedManifestSHA;$manifestSHA=FileHash $manifestFile;$manifest=Get-Content -LiteralPath $manifestFile -Raw|ConvertFrom-Json -AsHashtable -Depth 40
if($manifest.schema -cne 'PTFR_QR9_COMPONENT_V1' -or $manifest.component -cne $Component -or $manifest.source_epoch -cne 'QR8:02'){throw 'Manifest type/epoch drift'}
$game=if($fixture){Safe $FixtureRoot 'game'}else{Full $manifest.game_root};$save=if($fixture){Safe $FixtureRoot 'saves'}else{Full $manifest.save_root}
NoLinks $game;NoLinks $save
if(-not $RecoveryRoot){$RecoveryRoot=if($fixture){Safe $FixtureRoot ('recovery/'+$Component.ToLowerInvariant())}else{Join-Path $worker ('recovery/'+$Component.ToLowerInvariant()+'_qr8_02_01')}}
$recovery=if($fixture){Beneath $FixtureRoot $RecoveryRoot}else{Beneath (Join-Path $worker 'recovery') $RecoveryRoot}
if([IO.Path]::GetPathRoot($game) -cne [IO.Path]::GetPathRoot($recovery)){throw 'Recovery staging and game must be on the same volume for atomic file replacement'}
foreach($root in @($game,$save,(Full $manifest.package_root))){if($recovery -eq $root -or $recovery.StartsWith($root+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or $root.StartsWith($recovery+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'Recovery/source/game/save containment overlap'}}
$managedSet=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
$managedAncestors=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
foreach($row in $manifest.files){[void](Safe $game $row.path);[void](Safe $manifest.package_root $row.path);if(-not $managedSet.Add($row.path)){throw 'Duplicate managed path'};if($row.after -notmatch '^[A-F0-9]{64}$' -or ($null -ne $row.before -and $row.before -notmatch '^[A-F0-9]{64}$')){throw 'Invalid manifest hash'}}
foreach($relative in $managedSet){$parts=$relative.Split('/');for($i=1;$i -lt $parts.Length;$i++){[void]$managedAncestors.Add(($parts[0..($i-1)] -join '/'))}}
$changes=@($manifest.files|Where-Object {$_.before -cne $_.after})
if($Component -eq 'Core'){
 if($manifest.files.Count -ne 51 -or $changes.Count -ne 2 -or (@($changes.path|Sort-Object)-join ',') -cne 'archive/pc/mod/zzzz_PTFR_Combined.archive,archive/pc/mod/zzzz_PTFR_Combined.archive.xl' -or @($manifest.files|Where-Object {$null -eq $_.before}).Count){throw 'Core51/two-existing-path scope drift'}
}else{
 $wanted=@('bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_QR9_Diagnostics/init.lua','bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_QR9_Diagnostics/watch.json')
 if($manifest.files.Count -ne 2 -or $changes.Count -ne 2 -or @($manifest.files|Where-Object {$null -ne $_.before}).Count -or (@($manifest.files.path|Sort-Object)-join ',') -cne (@($wanted|Sort-Object)-join ',')){throw 'Diagnostic absent-baseline scope drift'}
}
$script:journalPath=Safe $recovery 'journal.json'
if($ReportFile){$rp=Beneath $worker $ReportFile;if(Test-Path -LiteralPath $rp){throw 'Never overwrite a report'}}
if($BackupMaster -and ($Component -ne 'Core' -or $Action -notin @('Preflight','Install'))){throw 'BackupMaster is only a reviewed Core Preflight/Install option'}
Closed
if($Action -in @('Preflight','Install')){
 CheckPackage;CheckDependencies 'After';CheckManaged 'Before'
 if(Test-Path -LiteralPath $recovery){throw 'Recovery path occupied; preserve it and use Verify/Recover or a reviewed fresh transaction path'}
 $protection=ProtectionSnapshot;$masterPlan=if($BackupMaster){MasterPlan}else{$null}
 if($Action -eq 'Preflight'){Report @{status='PREFLIGHT_READY';source_epoch=$manifest.source_epoch;process_guard=$manifest.process_names;managed_files=$manifest.files;protection=$protection;package_checked=$true;recovery_path_fresh=$true;optional_master_backup_plan=$masterPlan;limits=@('Read-only game/save preflight; no real write permissions were exercised.','External dependencies are exact-hashed; other unmanaged game files are protected by write-set containment and fresh transaction metadata.','Save snapshot is current, not a preparation-date restore requirement.','BackupMaster would copy only the three exact selected master files into recovery during a later explicitly authorized user Install. No backup was copied by Preflight.')};exit}
 EnsureDir $recovery;$script:transactionStarted=$true
 $script:journal=[ordered]@{schema=1;component=$Component;manifest_sha256=$manifestSHA;game_root=$game;save_root=$save;operation='Install';state='PREPARING';created_utc=[DateTime]::UtcNow.ToString('o');updated_utc='';completed_paths=@();last_error=$null;protection_before=$protection;protection_after=$null;original_install_protection=$protection;master_backup=$null;save_writes=0;game_launches=0}
 WriteJournal
 try{
  if($BackupMaster){CreateMasterBackup}
  foreach($row in $changes){
   if($null -ne $row.before){$old=Payload 'old' $row;EnsureDir ([IO.Path]::GetDirectoryName($old));[IO.File]::Copy((Safe $game $row.path),$old,$false);CheckFile $old $row.before $row.before_bytes}
   $new=Payload 'new' $row;EnsureDir ([IO.Path]::GetDirectoryName($new));[IO.File]::Copy((Safe $manifest.package_root $row.path),$new,$false);CheckFile $new $row.after $row.after_bytes
  }
  $script:journal.state='PREPARED';WriteJournal;Fault 'AfterBackup';$script:journal.state='APPLYING';WriteJournal
  $count=0;foreach($row in $changes){ApplyState $row 'After';$script:journal.completed_paths+=,$row.path;WriteJournal;$count++;if($count -eq 1){Fault 'AfterFirstReplace'}}
  CheckManaged 'After';CheckDependencies 'After';Closed;$after=ProtectionSnapshot;CompareProtection $protection $after;$script:journal.protection_after=$after;Fault 'BeforeReceipt';$script:journal.state='INSTALLED_VERIFIED';WriteJournal
  CleanKnownStages;Report @{status='INSTALLED_VERIFIED';journal=$script:journal;receipt=$script:journalPath;file_rollback_is_not_save_rollback=$true};exit
 }catch{
  $errorText=$_.Exception.Message;$script:journal.last_error=$errorText
  try{$state=RestoreActionStart;$script:journal.protection_after=ProtectionSnapshot;CompareProtection $protection $script:journal.protection_after;WriteJournal}
  catch{$script:journal.state='RECOVERY_REQUIRED';$script:journal.last_error=$errorText+'; recovery: '+$_.Exception.Message;WriteJournal}
  throw ('Install stopped; '+$script:journal.state+': '+$script:journal.last_error)
 }
}

$script:journal=ReadJournal
CheckMasterBackup
if($Action -eq 'Recover'){
 CheckDependencies $(if($script:journal.operation -eq 'Rollback'){'After'}else{'Before'})
 $fresh=ProtectionSnapshot
 try{$state=RestoreActionStart;$after=ProtectionSnapshot;CompareProtection $fresh $after;$script:journal.protection_before=$fresh;$script:journal.protection_after=$after;WriteJournal;Report @{status=('RECOVERED_'+$state.ToUpperInvariant());journal=$script:journal;file_rollback_is_not_save_rollback=$true};exit}
 catch{$script:journal.state='RECOVERY_REQUIRED';$script:journal.last_error=$_.Exception.Message;WriteJournal;throw}
}
if($Action -eq 'Verify'){
 $allowed=if($ExpectedState -eq 'After'){@('INSTALLED_VERIFIED')}else{@('ROLLED_BACK_VERIFIED','RESTORED_BEFORE_VERIFIED')}
 if($script:journal.state -notin $allowed){throw 'Journal is not committed in the requested state; use Recover for an interrupted transaction'}
 CheckManaged $ExpectedState;CheckDependencies $ExpectedState
 if($ExpectedState -eq 'After'){CheckRecoveryPayloads}
 Report @{status=('VERIFIED_'+$ExpectedState.ToUpperInvariant());receipt=$script:journalPath;file_rollback_is_not_save_rollback=$true};exit
}
if($script:journal.state -cne 'INSTALLED_VERIFIED'){throw 'Rollback requires a committed installed receipt'}
CheckManaged 'After';CheckDependencies 'After';CheckRecoveryPayloads
if($Action -eq 'ValidateRollback'){Report @{status='ROLLBACK_READY';receipt=$script:journalPath;save_policy='The next rollback snapshots then-current saves; it never restores the original installation snapshot.';file_rollback_is_not_save_rollback=$true};exit}
if($Action -eq 'Rollback'){
 $fresh=ProtectionSnapshot;$script:journal.operation='Rollback';$script:journal.state='ROLLING_BACK';$script:journal.protection_before=$fresh;$script:journal.protection_after=$null;$script:journal.completed_paths=@();WriteJournal
 try{
  $count=0;foreach($row in $changes){ApplyState $row 'Before';$script:journal.completed_paths+=,$row.path;WriteJournal;$count++;if($count -eq 1){Fault 'AfterFirstRollback'}}
  CheckManaged 'Before';Closed;$after=ProtectionSnapshot;CompareProtection $fresh $after;$script:journal.protection_after=$after;$script:journal.state='ROLLED_BACK_VERIFIED';WriteJournal;CleanKnownStages;Report @{status='ROLLED_BACK_VERIFIED';receipt=$script:journalPath;save_writes=0;file_rollback_is_not_save_rollback=$true};exit
 }catch{
  $errorText=$_.Exception.Message;$script:journal.last_error=$errorText
  try{$state=RestoreActionStart;$script:journal.protection_after=ProtectionSnapshot;CompareProtection $fresh $script:journal.protection_after;WriteJournal}
  catch{$script:journal.state='RECOVERY_REQUIRED';$script:journal.last_error=$errorText+'; recovery: '+$_.Exception.Message;WriteJournal}
  throw ('Rollback stopped; '+$script:journal.state+': '+$script:journal.last_error)
 }
}
throw 'Unreachable action'
