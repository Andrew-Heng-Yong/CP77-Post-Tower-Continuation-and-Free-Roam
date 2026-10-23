param(
 [string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),
 [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
 [string]$AuditDirectory='',
 [ValidateSet('ValidateInstall','Install','ValidateRollback','Rollback')][string]$Mode='ValidateInstall'
)
# Exactly one script replacement, with an exact predecessor backup. No save,
# archive, graph, profile definition, refund journal or compiler-cache writes.
. (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1')
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\')
$root=Join-Path $workspace 'research/restriction_profiles/profile_hp_reload_r3_3'
$game=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
$actual='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$fixture=$game.StartsWith($root+'\fixture_',[StringComparison]::OrdinalIgnoreCase)
if($game -ne $actual -and -not $fixture){throw 'Unsupported deployment root'}
$audit=if($AuditDirectory){R5Within $AuditDirectory $workspace}else{$root}
if($fixture -and (-not $AuditDirectory -or -not $audit.StartsWith((Split-Path -Parent $game)+'\',[StringComparison]::OrdinalIgnoreCase))){throw 'Fixture audit mismatch'}
if(-not $fixture -and $AuditDirectory){throw 'Actual audit must be canonical'}
R5Closed
$tp=Join-Path $root 'tests.json';$t=Get-Content -LiteralPath $tp -Raw|ConvertFrom-Json
if($t.status -ne 'PASS_HP_RELOAD_R3_3_OFFLINE_LIVE_PENDING' -or -not $t.exact_delta -or -not $t.full_scc -or -not $t.compiled_readback){throw 'Missing offline checks'}
R5Match (Join-Path $PSScriptRoot 'test_profile_hp_reload_r3_3.py') $t.test_sha256
$f=$t.file
if($f.source -cne 'build/ProfileHpReloadR3_3/ProfilePhysical.reds' -or $f.relative -cne 'r6/scripts/PTFR_Restrictions_R3/ProfilePhysical.reds' -or $f.predecessor -ne '40EE422B1134BE27783E427767FDD2024C6D83FA72D86CE19C7EA230A616DF84'){throw 'Unexpected scope/predecessor'}
$source=R5Within (Join-Path $workspace $f.source) $workspace
$target=R5Within (Join-Path $game $f.relative) $game
R5Match $source $f.sha256
$rollback=$Mode -in @('ValidateRollback','Rollback')
if(-not $fixture){
 $d=Get-Content -LiteralPath (Join-Path $root 'deployment_tests.json') -Raw|ConvertFrom-Json
 if($d.status -ne 'PASS_HP_RELOAD_R3_3_RECOVERABLE_FIXTURE' -or $d.installer_sha256 -ne (R5Hash $PSCommandPath) -or $d.tests_sha256 -ne (R5Hash $tp)){throw 'Fixture stale'}
 R5Match (Join-Path $PSScriptRoot 'test_profile_hp_reload_r3_3_deployment.ps1') $d.fixture_sha256
 R5Match (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1') $d.helpers_sha256
 foreach($entry in $t.pinned.PSObject.Properties){R5Match $entry.Name $entry.Value}
 foreach($entry in $t.dependencies.PSObject.Properties){if($entry.Name -ne $target){R5Match $entry.Name $entry.Value}}
 $observed=@();foreach($folder in $t.dependency_roots){$observed+=@(Get-ChildItem -LiteralPath $folder -Recurse -File -Filter '*.reds'|ForEach-Object FullName)}
 $expected=@($t.dependencies.PSObject.Properties|ForEach-Object Name)
 if(@(Compare-Object @($expected|Sort-Object -Unique) @($observed|Sort-Object -Unique)).Count){throw 'Compiled dependency inventory changed'}
 if(-not $rollback){foreach($entry in $t.protected.PSObject.Properties){R5Match $entry.Name $entry.Value}}
}
$rp=Join-Path $audit 'install_receipt.json';$rr=Join-Path $audit 'rollback_receipt.json'
$backup=R5Within (Join-Path $audit 'backup/ProfilePhysical.reds') $audit
if($rollback){
 $r=Get-Content -LiteralPath $rp -Raw|ConvertFrom-Json
 if($r.status -ne 'INSTALLED_HP_RELOAD_R3_3_LIVE_PENDING' -or $r.game_root -ne $game -or $r.tests_sha256 -ne (R5Hash $tp) -or $r.installer_sha256 -ne (R5Hash $PSCommandPath) -or $r.backup -ne $backup){throw 'Receipt mismatch'}
 if($r.file.relative -ne $f.relative -or $r.file.sha256 -ne $f.sha256 -or $r.file.predecessor -ne $f.predecessor){throw 'Receipt file mismatch'}
 if(Test-Path -LiteralPath $rr){throw 'Already recovered'}
 R5Match $target $f.sha256;R5Match $backup $f.predecessor
}else{
 if((Test-Path -LiteralPath $rp) -or (Test-Path -LiteralPath $backup)){throw 'Existing receipt or backup'}
 R5Match $target $f.predecessor
}
$protected=R5Snapshot $game @($target)
if(-not $fixture){
 foreach($folder in @('archive/pc/mod','red4ext/plugins','r6/scripts','r6/cache')){
  foreach($p in Get-ChildItem -LiteralPath (Join-Path $game $folder) -Recurse -File){
   if($p.FullName -ne $target -and ($folder -eq 'r6/cache' -or $p.Extension -in @('.archive','.xl','.reds','.dll'))){$protected[$p.FullName]=R5Hash $p.FullName}
  }
 }
}
R5Closed
if($Mode.StartsWith('Validate')){[ordered]@{status='VALIDATED';mode=$Mode;replacements=1;additions=0;protected_files=$protected.Count}|ConvertTo-Json;return}
New-Item -ItemType Directory -Force $audit|Out-Null
if(-not $rollback){
 New-Item -ItemType Directory -Force (Split-Path -Parent $backup)|Out-Null
 R5Match $target $f.predecessor
 [IO.File]::Copy($target,$backup,$false);R5Match $backup $f.predecessor
 $from=$source;$expectedBefore=$f.predecessor;$expectedAfter=$f.sha256
}else{
 $recoverable=R5Within (Join-Path $audit ('recoverable_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')+'/ProfilePhysical.reds')) $audit
 New-Item -ItemType Directory -Force (Split-Path -Parent $recoverable)|Out-Null
 [IO.File]::Copy($target,$recoverable,$false);R5Match $recoverable $f.sha256
 $from=$backup;$expectedBefore=$f.sha256;$expectedAfter=$f.predecessor
}
try{
 R5Closed;R5Match $target $expectedBefore;R5Match $from $expectedAfter
 [IO.File]::Copy($from,$target,$true);R5Match $target $expectedAfter
 R5Unchanged $protected
 if(-not $fixture){foreach($entry in $t.pinned.PSObject.Properties){R5Match $entry.Name $entry.Value}}
 if($rollback){
  R5Json $rr ([ordered]@{status='HP_RELOAD_R3_3_FILES_RECOVERED';recoverable=$recoverable;warning='Predecessor HP reload gate restored; no save/world rollback.'})
  'HP_RELOAD_R3_3_FILES_RECOVERED'
 }else{
  R5Json $rp ([ordered]@{status='INSTALLED_HP_RELOAD_R3_3_LIVE_PENDING';utc=[DateTime]::UtcNow.ToString('o');game_root=$game;file=$f;backup=$backup;tests_sha256=R5Hash $tp;installer_sha256=R5Hash $PSCommandPath;protected=$protected;replacements=1;additions=0;game_closed=$true;cache_writes=0;direct_save_writes=0;live_tested=$false})
  [ordered]@{status='INSTALLED_HP_RELOAD_R3_3_LIVE_PENDING';replacements=1;protected_files=$protected.Count}|ConvertTo-Json
 }
}catch{
 $reason=$_.Exception.Message
 # Keep the exact backup even if a file-copy/verification step fails. Do not
 # overwrite an unexpected third-party target during automatic recovery.
 $current=R5Hash $target
 if($current -eq $expectedAfter){
  R5Closed
  $revert=if($rollback){$recoverable}else{$backup}
  R5Match $revert $expectedBefore
  [IO.File]::Copy($revert,$target,$true);R5Match $target $expectedBefore
 }
 R5Json (Join-Path $audit 'deployment_failure.json') @{failure=$reason;backup=$backup;target_sha256=R5Hash $target;warning='Inspect target before launching; backup is retained. No save/cache recovery performed.'}
 throw $reason
}
