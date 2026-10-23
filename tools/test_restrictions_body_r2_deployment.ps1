param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
. (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1')
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\')
$out=Join-Path $workspace 'research/restriction_profiles/body_r2'
$actual='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$testsPath=Join-Path $out 'tests.json'
$tests=Get-Content -LiteralPath $testsPath -Raw|ConvertFrom-Json
$fixture=R5Within (Join-Path $out ('fixture_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')+'_'+[guid]::NewGuid().ToString('N').Substring(0,8))) $workspace
$game=Join-Path $fixture 'game';$audit=Join-Path $fixture 'audit'
$deploy=Join-Path $PSScriptRoot 'deploy_restrictions_body_r2.ps1'
$replacement='r6/scripts/PTFR_Restrictions_R1/CyberwarePolicy.reds'
$scope=@($tests.files.relative)
$actualBefore=R5Snapshot $actual
$actualCaches=[ordered]@{}
foreach($name in @('final.redscripts','final.redscripts.modded','final.redscripts.ts','tweakdb.bin','tweakdb_ep1.bin')){
 $from=R5Within (Join-Path $actual ('r6/cache/'+$name)) $actual
 $actualCaches[$from]=R5Hash $from
 $to=R5Within (Join-Path $game ('r6/cache/'+$name)) $game
 New-Item -ItemType Directory -Force (Split-Path -Parent $to)|Out-Null
 [IO.File]::Copy($from,$to,$false)
 R5Match $to $actualCaches[$from]
}
$r1=Get-Content -LiteralPath (Join-Path $workspace 'research/restriction_profiles/implementation_r1/install_receipt.json') -Raw|ConvertFrom-Json
$r11=Get-Content -LiteralPath (Join-Path $workspace 'research/afterlife_world/interactions_r11/install_receipt.json') -Raw|ConvertFrom-Json
foreach($file in @($r1.files)+@($r11.files)){
 $from=R5Within (Join-Path $actual $file.relative) $actual
 R5Match $from $file.sha256
 $to=R5Within (Join-Path $game $file.relative) $game
 New-Item -ItemType Directory -Force (Split-Path -Parent $to)|Out-Null
 [IO.File]::Copy($from,$to,$false);R5Match $to $file.sha256
}
New-Item -ItemType Directory -Force $audit|Out-Null
$baseline=R5Snapshot $game
$targets=@($scope|ForEach-Object {R5Within (Join-Path $game $_) $game})
$protected=R5Snapshot $game $targets
$negative=[Collections.Generic.List[string]]::new()
function Expect-Refusal([string]$Name,[scriptblock]$Action){
 $refused=$false
 try{& $Action|Out-Null}catch{$refused=$true}
 if(-not $refused){throw "Negative fixture was accepted: $Name"}
 $negative.Add($Name)
 R5Unchanged $protected
}
function Check-Installed {
 foreach($file in $tests.files){R5Match (R5Within (Join-Path $game $file.relative) $game) $file.sha256}
 R5Unchanged $protected
}
& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $audit
R5Unchanged $baseline

# Invalid predecessor and pre-existing additions must not be overwritten.
$target=R5Within (Join-Path $game $replacement) $game
$wrongSource=R5Within (Join-Path $workspace 'redscript/PTFR_Restrictions_R2/BodyCatalogue.reds') $workspace
[IO.File]::Copy($wrongSource,$target,$true)
$wrongHash=R5Hash $target
Expect-Refusal 'wrong_predecessor_hash' {& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $audit -Mode ValidateInstall}
R5Match $target $wrongHash
[IO.File]::Copy((Join-Path $actual $replacement),$target,$true)
R5Unchanged $baseline
$addition=@($tests.files|Where-Object relative -ne $replacement)[0]
$additionTarget=R5Within (Join-Path $game $addition.relative) $game
New-Item -ItemType Directory -Force (Split-Path -Parent $additionTarget)|Out-Null
[IO.File]::Copy($wrongSource,$additionTarget,$false)
Expect-Refusal 'preexisting_addition' {& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $audit -Mode Install}
R5Match $additionTarget $wrongHash
$quarantine=R5Within (Join-Path $fixture 'preexisting_addition_preserved.reds') $fixture
Move-Item -LiteralPath $additionTarget -Destination $quarantine
R5Match $quarantine $wrongHash
R5Unchanged $baseline

& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $audit -Mode Install
Check-Installed
Expect-Refusal 'repeated_install' {& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $audit -Mode Install}
Check-Installed
& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $audit -Mode ValidateRollback
$receiptPath=Join-Path $audit 'install_receipt.json'
$receiptText=Get-Content -LiteralPath $receiptPath -Raw
$receipt=$receiptText|ConvertFrom-Json
if($receipt.additions -ne 3 -or $receipt.replacements -ne 1 -or $receipt.removals -ne 0 -or $receipt.progression_rollback){throw 'Unexpected receipt scope or progression rollback claim'}

foreach($case in @('receipt_scope','receipt_new_hash','receipt_before_hash','stale_build_receipt','escaped_backup')){
 $changed=$receiptText|ConvertFrom-Json
 $entry=@($changed.files|Where-Object relative -eq $replacement)[0]
 switch($case){
  'receipt_scope' {$entry.relative='r6/scripts/NotInScope.reds'}
  'receipt_new_hash' {$entry.sha256='0'*64}
  'receipt_before_hash' {$entry.before_sha256='0'*64}
  'stale_build_receipt' {$changed.tests_sha256='0'*64}
  'escaped_backup' {$entry.backup=Join-Path $workspace 'redscript/PTFR_Restrictions_R1/CyberwarePolicy.reds'}
 }
 R5Json $receiptPath $changed
 Expect-Refusal $case {& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $audit -Mode ValidateRollback}
 Check-Installed
 R5Json $receiptPath ($receiptText|ConvertFrom-Json)
}

# Missing or corrupt backups must not trigger partial rollback.
$originalBackup=R5Within (@($receipt.files|Where-Object relative -eq $replacement)[0].backup) $audit
$heldBackup=R5Within (Join-Path $fixture 'withheld_original.reds') $fixture
Move-Item -LiteralPath $originalBackup -Destination $heldBackup
Expect-Refusal 'missing_original_backup' {& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $audit -Mode Rollback}
Check-Installed
Move-Item -LiteralPath $heldBackup -Destination $originalBackup
$backupHash=R5Hash $originalBackup
[IO.File]::Copy($wrongSource,$originalBackup,$true)
Expect-Refusal 'wrong_original_backup_hash' {& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $audit -Mode Rollback}
Check-Installed
[IO.File]::Copy((Join-Path $actual $replacement),$originalBackup,$true)
R5Match $originalBackup $backupHash

# An installed file changed by somebody else is never silently replaced.
[IO.File]::Copy((Join-Path $actual $replacement),$additionTarget,$true)
$foreignHash=R5Hash $additionTarget
Expect-Refusal 'modified_installed_addition' {& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $audit -Mode Rollback}
R5Match $additionTarget $foreignHash
[IO.File]::Copy((Join-Path $workspace $addition.source),$additionTarget,$true)
Check-Installed

& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $audit -Mode Rollback
R5Unchanged $baseline
foreach($file in $tests.files|Where-Object relative -ne $replacement){
 if(Test-Path -LiteralPath (Join-Path $game $file.relative)){throw 'Rollback retained an R2 addition'}
}
$rolled=Get-Content -LiteralPath (Join-Path $audit 'rollback_receipt.json') -Raw|ConvertFrom-Json
foreach($file in $tests.files){
 R5Match (R5Within (Join-Path $rolled.recovery $file.relative) $rolled.recovery) $file.sha256
}
if($rolled.progression_rollback -or $rolled.replacements -ne 1 -or $rolled.removals -ne 3){throw 'Incorrect rollback scope'}
Expect-Refusal 'repeated_rollback' {& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $audit -Mode Rollback}
R5Unchanged $baseline;R5Unchanged $actualBefore;R5Unchanged $actualCaches
$result=@{status='PASS_RESTRICTIONS_BODY_R2_INSTALL_ROLLBACK_FIXTURE';fixture=$fixture;replacements=1;additions=3;removals=0;negative_checks=@($negative);negative_count=$negative.Count;protected_unchanged=$true;actual_tracked_files_unchanged=$actualBefore.Count;cache_files_unchanged=$actualCaches.Count;recoverable_rollback=$true;progression_rollback=$false;game_writes=0;save_writes=0;installer_sha256=(R5Hash $deploy);fixture_sha256=(R5Hash $PSCommandPath);helpers_sha256=(R5Hash (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1'));tests_sha256=(R5Hash $testsPath)}
R5Json (Join-Path $out 'deployment_tests.json') $result
$result|ConvertTo-Json -Depth 5
