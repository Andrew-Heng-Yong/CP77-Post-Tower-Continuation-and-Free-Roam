param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
. (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1')
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\')
$out=Join-Path $workspace 'research/restriction_profiles/profile_hp_r3_1'
$actual='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$testsPath=Join-Path $out 'tests.json'
$tests=Get-Content -LiteralPath $testsPath -Raw|ConvertFrom-Json
$fixture=R5Within (Join-Path $out ('fixture_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')+'_'+[guid]::NewGuid().ToString('N').Substring(0,8))) $workspace
$game=Join-Path $fixture 'game';$audit=Join-Path $fixture 'audit'
$deploy=Join-Path $PSScriptRoot 'deploy_restrictions_profile_hp_r3_1.ps1'
$actualBefore=R5Snapshot $actual
$actualCaches=[ordered]@{};$fixtureCaches=[ordered]@{}
foreach($name in @('final.redscripts','final.redscripts.modded','final.redscripts.ts','tweakdb.bin','tweakdb_ep1.bin')){
 $from=R5Within (Join-Path $actual ('r6/cache/'+$name)) $actual
 $actualCaches[$from]=R5Hash $from
 $to=R5Within (Join-Path $game ('r6/cache/'+$name)) $game
 New-Item -ItemType Directory -Force (Split-Path -Parent $to)|Out-Null
 [IO.File]::Copy($from,$to,$false);R5Match $to $actualCaches[$from]
 $fixtureCaches[$to]=$actualCaches[$from]
}
foreach($entry in $tests.checked_sources.PSObject.Properties){
 $relative=$entry.Name.Replace('redscript/','r6/scripts/')
 $change=@($tests.files|Where-Object relative -eq $relative)
 $from=R5Within (Join-Path $actual $relative) $actual
 if($change.Count -and -not $change[0].before_sha256){
  if(Test-Path -LiteralPath $from){throw 'Actual addition already exists'}
  continue
 }
 $hash=if($change.Count){$change[0].before_sha256}else{$entry.Value}
 R5Match $from $hash
 $to=R5Within (Join-Path $game $relative) $game
 New-Item -ItemType Directory -Force (Split-Path -Parent $to)|Out-Null
 [IO.File]::Copy($from,$to,$false);R5Match $to $hash
}
New-Item -ItemType Directory -Force $audit|Out-Null
$baseline=R5Snapshot $game
$targets=@($tests.files|ForEach-Object {R5Within (Join-Path $game $_.relative) $game})
$protected=R5Snapshot $game $targets
$negative=[Collections.Generic.List[string]]::new()
function Expect-Refusal([string]$Name,[scriptblock]$Action){
 $before=R5Snapshot $game
 $refused=$false
 try{& $Action|Out-Null}catch{$refused=$true}
 if(-not $refused){throw "Negative fixture accepted: $Name"}
 R5Unchanged $before;R5Unchanged $protected;R5Unchanged $fixtureCaches
 $after=R5Snapshot $game
 if(@(Compare-Object @($before.Keys) @($after.Keys)).Count){throw "Negative fixture changed inventory: $Name"}
 $negative.Add($Name)
}
function Check-Installed {
 foreach($file in $tests.files){R5Match (R5Within (Join-Path $game $file.relative) $game) $file.sha256}
 R5Unchanged $protected;R5Unchanged $fixtureCaches
}
& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $audit
R5Unchanged $baseline
$wrong=Join-Path $workspace 'redscript/PTFR_Restrictions_R2/BodyCatalogue.reds'
foreach($file in $tests.files|Where-Object before_sha256){
 $target=R5Within (Join-Path $game $file.relative) $game
 [IO.File]::Copy($wrong,$target,$true)
 Expect-Refusal ('wrong_predecessor_'+(Split-Path -Leaf $target)) {& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $audit -Mode Install}
 [IO.File]::Copy((Join-Path $actual $file.relative),$target,$true)
}
foreach($file in $tests.files|Where-Object {-not $_.before_sha256}){
 $target=R5Within (Join-Path $game $file.relative) $game
 New-Item -ItemType Directory -Force (Split-Path -Parent $target)|Out-Null
 [IO.File]::Copy($wrong,$target,$false)
 Expect-Refusal ('preexisting_addition_'+(Split-Path -Leaf $target)) {& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $audit -Mode Install}
 $held=R5Within (Join-Path $fixture ('preexisting_'+(Split-Path -Leaf $target))) $fixture
 Move-Item -LiteralPath $target -Destination $held
 R5Match $held (R5Hash $wrong)
}
R5Unchanged $baseline
& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $audit -Mode Install
Check-Installed
Expect-Refusal 'repeated_install' {& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $audit -Mode Install}
& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $audit -Mode ValidateRollback
$receiptPath=Join-Path $audit 'install_receipt.json'
$receiptText=Get-Content -LiteralPath $receiptPath -Raw
$receipt=$receiptText|ConvertFrom-Json
if($receipt.replacements -ne 2 -or $receipt.additions -ne 0 -or $receipt.removals -ne 0 -or $receipt.progression_rollback){throw 'Incorrect deployment scope'}
foreach($case in @('receipt_scope','receipt_source','receipt_after_hash','receipt_before_hash','receipt_tool_hash','receipt_tests_hash','escaped_backup','duplicate_scope')){
 $changed=$receiptText|ConvertFrom-Json
 switch($case){
  'receipt_scope' {$changed.files[0].relative='r6/scripts/NotInScope.reds'}
  'receipt_source' {$changed.files[0].source='redscript/NotInScope.reds'}
  'receipt_after_hash' {$changed.files[0].sha256='0'*64}
  'receipt_before_hash' {$changed.files[0].before_sha256='0'*64}
  'receipt_tool_hash' {$changed.installer_sha256='0'*64}
  'receipt_tests_hash' {$changed.tests_sha256='0'*64}
  'escaped_backup' {$changed.files[0].backup=$wrong}
  'duplicate_scope' {$changed.files[1].relative=$changed.files[0].relative}
 }
 R5Json $receiptPath $changed
 Expect-Refusal $case {& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $audit -Mode Rollback}
 Check-Installed
 R5Json $receiptPath ($receiptText|ConvertFrom-Json)
}
foreach($file in $receipt.files|Where-Object before_sha256){
 $backup=R5Within $file.backup $audit
 $held=R5Within (Join-Path $fixture ('held_'+(Split-Path -Leaf $backup))) $fixture
 Move-Item -LiteralPath $backup -Destination $held
 Expect-Refusal ('missing_backup_'+(Split-Path -Leaf $backup)) {& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $audit -Mode Rollback}
 Check-Installed
 Move-Item -LiteralPath $held -Destination $backup
 [IO.File]::Copy($wrong,$backup,$true)
 Expect-Refusal ('corrupt_backup_'+(Split-Path -Leaf $backup)) {& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $audit -Mode Rollback}
 Check-Installed
 [IO.File]::Copy((Join-Path $actual $file.relative),$backup,$true)
}
foreach($file in $tests.files){
 $target=R5Within (Join-Path $game $file.relative) $game
 [IO.File]::Copy($wrong,$target,$true)
 Expect-Refusal ('foreign_installed_'+(Split-Path -Leaf $target)) {& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $audit -Mode Rollback}
 [IO.File]::Copy((Join-Path $workspace $file.source),$target,$true)
 Check-Installed
}
& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $audit -Mode Rollback
R5Unchanged $baseline
foreach($file in $tests.files|Where-Object {-not $_.before_sha256}){
 if(Test-Path -LiteralPath (R5Within (Join-Path $game $file.relative) $game)){throw 'Rollback retained an addition'}
}
$rolled=Get-Content -LiteralPath (Join-Path $audit 'rollback_receipt.json') -Raw|ConvertFrom-Json
foreach($file in $tests.files){R5Match (R5Within (Join-Path $rolled.recovery $file.relative) $rolled.recovery) $file.sha256}
if($rolled.replacements -ne 2 -or $rolled.removals -ne 0 -or $rolled.additions -ne 0 -or $rolled.progression_rollback){throw 'Incorrect recovery scope'}
Expect-Refusal 'repeated_rollback' {& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $audit -Mode Rollback}
R5Unchanged $baseline;R5Unchanged $actualBefore;R5Unchanged $actualCaches;R5Unchanged $fixtureCaches
$result=@{status='PASS_PROFILE_HP_R3_1_INSTALL_ROLLBACK_FIXTURE';fixture=$fixture;replacements=2;additions=0;removals=0;negative_checks=@($negative);negative_count=$negative.Count;actual_tracked_files_unchanged=$actualBefore.Count;cache_files_unchanged=$actualCaches.Count;recoverable_rollback=$true;progression_rollback=$false;game_writes=0;save_writes=0;installer_sha256=(R5Hash $deploy);fixture_sha256=(R5Hash $PSCommandPath);helpers_sha256=(R5Hash (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1'));tests_sha256=(R5Hash $testsPath)}
R5Json (Join-Path $out 'deployment_tests.json') $result
$result|ConvertTo-Json -Depth 5
