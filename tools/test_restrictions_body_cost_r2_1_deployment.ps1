param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
. (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1')
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\')
$out=Join-Path $workspace 'research/restriction_profiles/body_cost_r2_1'
$actual='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$testsPath=Join-Path $out 'tests.json'
$tests=Get-Content -LiteralPath $testsPath -Raw|ConvertFrom-Json
$fixture=R5Within (Join-Path $out ('fixture_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')+'_'+[guid]::NewGuid().ToString('N').Substring(0,8))) $workspace
$game=Join-Path $fixture 'game';$audit=Join-Path $fixture 'audit'
$deploy=Join-Path $PSScriptRoot 'deploy_restrictions_body_cost_r2_1.ps1'
$relative=$tests.files[0].relative
$actualBefore=R5Snapshot $actual
$actualCaches=[ordered]@{}
foreach($name in @('final.redscripts','final.redscripts.modded','final.redscripts.ts','tweakdb.bin','tweakdb_ep1.bin')){
 $from=R5Within (Join-Path $actual ('r6/cache/'+$name)) $actual
 $actualCaches[$from]=R5Hash $from
 $to=R5Within (Join-Path $game ('r6/cache/'+$name)) $game
 New-Item -ItemType Directory -Force (Split-Path -Parent $to)|Out-Null
 [IO.File]::Copy($from,$to,$false)
}
foreach($entry in $tests.checked_sources.PSObject.Properties){
 $toRelative=$entry.Name.Replace('redscript/','r6/scripts/')
 $from=R5Within (Join-Path $actual $toRelative) $actual
 R5Match $from $(if($toRelative -eq $relative){$tests.files[0].before_sha256}else{$entry.Value})
 $to=R5Within (Join-Path $game $toRelative) $game
 New-Item -ItemType Directory -Force (Split-Path -Parent $to)|Out-Null
 [IO.File]::Copy($from,$to,$false)
}
New-Item -ItemType Directory -Force $audit|Out-Null
$target=R5Within (Join-Path $game $relative) $game
$baseline=R5Snapshot $game
$protected=R5Snapshot $game @($target)
$negative=[Collections.Generic.List[string]]::new()
function Expect-Refusal([string]$Name,[scriptblock]$Action){
 $refused=$false
 try{& $Action|Out-Null}catch{$refused=$true}
 if(-not $refused){throw "Negative fixture accepted: $Name"}
 $negative.Add($Name);R5Unchanged $protected
}
function Check-Installed {R5Match $target $tests.files[0].sha256;R5Unchanged $protected}
& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $audit
R5Unchanged $baseline
$wrong=Join-Path $workspace 'redscript/PTFR_Restrictions_R2/BodyCatalogue.reds'
[IO.File]::Copy($wrong,$target,$true)
Expect-Refusal 'wrong_predecessor' {& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $audit -Mode Install}
R5Match $target (R5Hash $wrong)
[IO.File]::Copy((Join-Path $actual $relative),$target,$true)
& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $audit -Mode Install
Check-Installed
Expect-Refusal 'repeated_install' {& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $audit -Mode Install}
& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $audit -Mode ValidateRollback
$receiptPath=Join-Path $audit 'install_receipt.json'
$receiptText=Get-Content -LiteralPath $receiptPath -Raw
$receipt=$receiptText|ConvertFrom-Json
if($receipt.replacements -ne 1 -or $receipt.additions -ne 0 -or $receipt.removals -ne 0 -or $receipt.progression_rollback){throw 'Incorrect deployment scope'}
foreach($case in @('receipt_scope','receipt_after_hash','receipt_before_hash','receipt_tool_hash','receipt_tests_hash','escaped_backup')){
 $changed=$receiptText|ConvertFrom-Json
 switch($case){
  'receipt_scope' {$changed.files[0].relative='r6/scripts/NotInScope.reds'}
  'receipt_after_hash' {$changed.files[0].sha256='0'*64}
  'receipt_before_hash' {$changed.files[0].before_sha256='0'*64}
  'receipt_tool_hash' {$changed.installer_sha256='0'*64}
  'receipt_tests_hash' {$changed.tests_sha256='0'*64}
  'escaped_backup' {$changed.files[0].backup=$wrong}
 }
 R5Json $receiptPath $changed
 Expect-Refusal $case {& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $audit -Mode Rollback}
 Check-Installed
 R5Json $receiptPath ($receiptText|ConvertFrom-Json)
}
$backup=R5Within $receipt.files[0].backup $audit
$held=R5Within (Join-Path $fixture 'original_backup_held.reds') $fixture
Move-Item -LiteralPath $backup -Destination $held
Expect-Refusal 'missing_backup' {& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $audit -Mode Rollback}
Check-Installed
Move-Item -LiteralPath $held -Destination $backup
[IO.File]::Copy($wrong,$backup,$true)
Expect-Refusal 'corrupt_backup' {& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $audit -Mode Rollback}
Check-Installed
[IO.File]::Copy((Join-Path $actual $relative),$backup,$true)
[IO.File]::Copy($wrong,$target,$true)
Expect-Refusal 'foreign_installed_file' {& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $audit -Mode Rollback}
R5Match $target (R5Hash $wrong)
[IO.File]::Copy((Join-Path $workspace $tests.files[0].source),$target,$true)
& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $audit -Mode Rollback
R5Unchanged $baseline
$rolled=Get-Content -LiteralPath (Join-Path $audit 'rollback_receipt.json') -Raw|ConvertFrom-Json
R5Match (R5Within (Join-Path $rolled.recovery $relative) $rolled.recovery) $tests.files[0].sha256
Expect-Refusal 'repeated_rollback' {& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $audit -Mode Rollback}
R5Unchanged $baseline;R5Unchanged $actualBefore;R5Unchanged $actualCaches
$result=@{status='PASS_BODY_COST_R2_1_INSTALL_ROLLBACK_FIXTURE';fixture=$fixture;replacements=1;additions=0;removals=0;negative_checks=@($negative);negative_count=$negative.Count;actual_tracked_files_unchanged=$actualBefore.Count;cache_files_unchanged=$actualCaches.Count;recoverable_rollback=$true;progression_rollback=$false;game_writes=0;save_writes=0;installer_sha256=(R5Hash $deploy);fixture_sha256=(R5Hash $PSCommandPath);helpers_sha256=(R5Hash (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1'));tests_sha256=(R5Hash $testsPath)}
R5Json (Join-Path $out 'deployment_tests.json') $result
$result|ConvertTo-Json -Depth 5
