param(
 [string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),
 [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
 [string]$AuditDirectory='',
 [ValidateSet('ValidateInstall','Install','ValidateRollback','Rollback')][string]$Mode='ValidateInstall'
)
# Exact one-file patch. File recovery never reverses saved progression.
. (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1')
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\')
$sourceAudit=Join-Path $workspace 'research\restriction_profiles\body_cost_r2_1'
$audit=if($AuditDirectory){R5Within $AuditDirectory $workspace}else{$sourceAudit}
$game=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
$actual='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$fixture=$game.StartsWith($sourceAudit+'\fixture_',[StringComparison]::OrdinalIgnoreCase)
if($game -ne $actual -and -not $fixture){throw 'Unsupported deployment root'}
if($fixture -and (-not $AuditDirectory -or -not $audit.StartsWith((Split-Path -Parent $game)+'\',[StringComparison]::OrdinalIgnoreCase))){throw 'Fixture audit must be inside the same fixture root'}
if(-not $fixture -and $AuditDirectory){throw 'Actual deployment must use its canonical audit directory'}
New-Item -ItemType Directory -Force $audit|Out-Null
$relative='r6/scripts/PTFR_Restrictions_R2/DevelopmentHooks.reds'
$sourceRelative='redscript/PTFR_Restrictions_R2/DevelopmentHooks.reds'
$beforeHash='49D3BB837704DA60F2A2B300D991025B7A01EC0E9ABA2FB59621A41760317DAB'
$afterHash='0BF91CD59E8D8414ED57BF44DED0067FED847CDAD0BFB4B85462E678A6316D6D'
$target=R5Within (Join-Path $game $relative) $game
$source=R5Within (Join-Path $workspace $sourceRelative) $workspace
$testsPath=Join-Path $sourceAudit 'tests.json'
$tests=Get-Content -LiteralPath $testsPath -Raw|ConvertFrom-Json
if($tests.status -ne 'PASS_BODY_COST_R2_1_OFFLINE_LIVE_PENDING' -or -not $tests.exact_one_method_delta -or -not $tests.equipmentex_full_compile){throw 'Cost-fix offline checks missing'}
if(@($tests.files).Count -ne 1 -or $tests.files[0].relative -ne $relative -or $tests.files[0].source -ne $sourceRelative -or $tests.files[0].before_sha256 -ne $beforeHash -or $tests.files[0].sha256 -ne $afterHash){throw 'Unexpected cost-fix scope or hashes'}
if(@($tests.checked_sources.PSObject.Properties).Count -ne 6){throw 'Expected six checked restriction sources'}
foreach($entry in $tests.checked_sources.PSObject.Properties){
 if([IO.Path]::IsPathRooted($entry.Name)){throw 'Checked source must be workspace-relative'}
 R5Match (R5Within (Join-Path $workspace $entry.Name) $workspace) $entry.Value
 if($entry.Name -ne $sourceRelative){R5Match (R5Within (Join-Path $game $entry.Name.Replace('redscript/','r6/scripts/')) $game) $entry.Value}
}
R5Match $source $afterHash
R5Match (Join-Path $game 'r6/cache/final.redscripts') $tests.base_sha256
$receiptPath=Join-Path $audit 'install_receipt.json'
$rollbackPath=Join-Path $audit 'rollback_receipt.json'
$rollback=$Mode -in @('ValidateRollback','Rollback')
$backupRoot='';$backup=''
if($rollback){
 $receipt=Get-Content -LiteralPath $receiptPath -Raw|ConvertFrom-Json
 if($receipt.status -ne 'INSTALLED_BODY_COST_R2_1_LIVE_PENDING' -or $receipt.game_root -ne $game){throw 'Receipt/root mismatch'}
 if(@($receipt.files).Count -ne 1 -or $receipt.files[0].relative -ne $relative -or $receipt.files[0].source -ne $sourceRelative -or $receipt.files[0].sha256 -ne $afterHash -or $receipt.files[0].before_sha256 -ne $beforeHash){throw 'Receipt scope/hash mismatch'}
 if($receipt.tests_sha256 -ne (R5Hash $testsPath) -or $receipt.installer_sha256 -ne (R5Hash $PSCommandPath)){throw 'Receipt build/tool mismatch'}
 $backupRoot=R5Within $receipt.backup_root $audit
 if(-not (Split-Path -Leaf $backupRoot).StartsWith('backup_')){throw 'Unexpected backup root'}
 $backup=R5Within (Join-Path $backupRoot $relative) $backupRoot
 if($receipt.files[0].backup -ne $backup){throw 'Receipt backup path mismatch'}
 R5Match $backup $beforeHash
 R5Match $target $afterHash
 if(Test-Path -LiteralPath $rollbackPath){throw 'Already rolled back'}
}else{
 R5Match $target $beforeHash
 if(Test-Path -LiteralPath $receiptPath){throw 'Install receipt already exists'}
}
$dependencies=[ordered]@{}
if(-not $fixture){
 # Preserve historical receipt/source evidence, allowing only this target to
 # differ during rollback. Cache outputs are snapshotted at deployment time.
 foreach($entry in $tests.protected_inputs.PSObject.Properties){
  $path=[IO.Path]::GetFullPath($entry.Name)
  if($path -ne $target -and -not $path.StartsWith($actual+'\r6\cache\',[StringComparison]::OrdinalIgnoreCase)){
   R5Match $path $entry.Value
  }
 }
 if(-not @($tests.dependency_hashes.PSObject.Properties).Count -or -not @($tests.dependency_roots).Count){throw 'Compiled dependency inventory missing'}
 foreach($entry in $tests.dependency_hashes.PSObject.Properties){
  $path=R5Within $entry.Name $actual
  R5Match $path $entry.Value
  $dependencies[$path]=$entry.Value
 }
 $candidateTargets=@($tests.checked_sources.PSObject.Properties|ForEach-Object {R5Within (Join-Path $game $_.Name.Replace('redscript/','r6/scripts/')) $game})
 $observed=@()
 foreach($root in $tests.dependency_roots){
  $root=R5Within $root $actual
  if(-not (Test-Path -LiteralPath $root -PathType Container)){throw 'Dependency directory missing'}
  $observed+=@(Get-ChildItem -LiteralPath $root -Filter '*.reds' -File -Recurse|Where-Object FullName -notin $candidateTargets|ForEach-Object FullName)
 }
 $expected=@($dependencies.Keys|Where-Object {$_ -notin $candidateTargets})
 if(@(Compare-Object @($observed|Sort-Object -Unique) @($expected|Sort-Object -Unique)).Count){throw 'Enabled sources differ from compiled dependency inventory'}
 if($Mode -eq 'Install'){
  $fixtureResult=Get-Content -LiteralPath (Join-Path $sourceAudit 'deployment_tests.json') -Raw|ConvertFrom-Json
  if($fixtureResult.status -ne 'PASS_BODY_COST_R2_1_INSTALL_ROLLBACK_FIXTURE'){throw 'Deployment fixture pass missing'}
  R5Match $PSCommandPath $fixtureResult.installer_sha256
  R5Match $testsPath $fixtureResult.tests_sha256
  R5Match (Join-Path $PSScriptRoot 'test_restrictions_body_cost_r2_1_deployment.ps1') $fixtureResult.fixture_sha256
  R5Match (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1') $fixtureResult.helpers_sha256
 }
}
R5Closed
$protected=R5Snapshot $game @($target)
$cacheHashes=[ordered]@{}
foreach($name in @('final.redscripts','final.redscripts.modded','final.redscripts.ts','tweakdb.bin','tweakdb_ep1.bin')){
 $path=R5Within (Join-Path $game ('r6/cache/'+$name)) $game
 $cacheHashes[$path]=R5Hash $path
}
if($Mode -like 'Validate*'){
 R5Unchanged $protected;R5Unchanged $cacheHashes;R5Unchanged $dependencies
 $result=@{status=('BODY_COST_R2_1_'+$Mode.ToUpper());game_root=$game;replacements=1;additions=0;removals=0;protected_files=$protected.Count;cache_files=$cacheHashes.Count;game_unchanged=$true;progression_rollback=$false}
 R5Json (Join-Path $audit ($Mode+'.json')) $result
 $result|ConvertTo-Json;return
}
$tag=[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')+'_'+[guid]::NewGuid().ToString('N').Substring(0,8)
$recovery=R5Within (Join-Path $audit ('recoverable_'+$tag)) $audit
$saved=R5Within (Join-Path $recovery $relative) $recovery
if(-not $rollback){
 $backupRoot=R5Within (Join-Path $audit ('backup_'+$tag)) $audit
 $backup=R5Within (Join-Path $backupRoot $relative) $backupRoot
 New-Item -ItemType Directory -Force (Split-Path -Parent $backup)|Out-Null
 R5Closed;R5Match $target $beforeHash
 [IO.File]::Copy($target,$backup,$false);R5Match $backup $beforeHash
}
$attempted=$false
try{
 R5Closed;R5Match $source $afterHash;R5Match $backup $beforeHash
 if($rollback){
  R5Match $target $afterHash
  New-Item -ItemType Directory -Force (Split-Path -Parent $saved)|Out-Null
  [IO.File]::Copy($target,$saved,$false);R5Match $saved $afterHash
  $attempted=$true
  [IO.File]::Copy($backup,$target,$true);R5Match $target $beforeHash
 }else{
  R5Match $target $beforeHash
  $attempted=$true
  [IO.File]::Copy($source,$target,$true);R5Match $target $afterHash
 }
 R5Closed;R5Unchanged $protected;R5Unchanged $cacheHashes;R5Unchanged $dependencies
 $afterProtected=R5Snapshot $game @($target)
 if(@(Compare-Object @($protected.Keys) @($afterProtected.Keys)).Count){throw 'Protected file inventory changed during deployment'}
 $result=[ordered]@{status=$(if($rollback){'ROLLED_BACK_BODY_COST_R2_1_FILES_ONLY'}else{'INSTALLED_BODY_COST_R2_1_LIVE_PENDING'});utc=[DateTime]::UtcNow.ToString('o');game_root=$game;files=@(@{relative=$relative;source=$sourceRelative;sha256=$afterHash;before_sha256=$beforeHash;backup=$backup});replacements=1;additions=0;removals=0;protected_files=$protected.Count;protected_hashes=$protected;cache_hashes=$cacheHashes;dependency_hashes=$dependencies;backup_root=$backupRoot;recovery=$recovery;game_closed=$true;live_tested=$false;save_writes=0;story_writes=0;progression_rollback=$false;tests_sha256=(R5Hash $testsPath);installer_sha256=(R5Hash $PSCommandPath)}
 R5Json $(if($rollback){$rollbackPath}else{$receiptPath}) $result
 [pscustomobject]$result|Select-Object status,utc,replacements,additions,removals,protected_files|ConvertTo-Json
}catch{
 $failure=$_.Exception.Message;$recoveryError=''
 if($attempted){
  try{
   R5Closed
   if($rollback){
    R5Match $target $beforeHash;R5Match $saved $afterHash
    [IO.File]::Copy($saved,$target,$true);R5Match $target $afterHash
   }else{
    R5Match $target $afterHash;R5Match $backup $beforeHash
    [IO.File]::Copy($backup,$target,$true);R5Match $target $beforeHash
   }
  }catch{$recoveryError=$_.Exception.Message}
 }
 R5Json (Join-Path $audit 'deployment_failure.json') @{failure=$failure;backup=$backup;recovery=$recovery;recovery_error=$recoveryError;warning='Check exact target hashes before launching after a deployment failure. No save or progression recovery was performed.'}
 throw $failure
}
