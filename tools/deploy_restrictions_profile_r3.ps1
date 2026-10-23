param(
 [string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),
 [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
 [string]$AuditDirectory='',
 [ValidateSet('ValidateInstall','Install','ValidateRollback','Rollback')][string]$Mode='ValidateInstall'
)
# Exact three-replacement/four-addition deployment. File rollback cannot reverse
# saved Body or Profile refunds. No save files or compiler caches are deployed.
. (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1')
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\')
$sourceAudit=Join-Path $workspace 'research\restriction_profiles\profile_r3'
$audit=if($AuditDirectory){R5Within $AuditDirectory $workspace}else{$sourceAudit}
$game=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
$actual='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$fixture=$game.StartsWith($sourceAudit+'\fixture_',[StringComparison]::OrdinalIgnoreCase)
if($game -ne $actual -and -not $fixture){throw 'Unsupported deployment root'}
if($fixture -and (-not $AuditDirectory -or -not $audit.StartsWith((Split-Path -Parent $game)+'\',[StringComparison]::OrdinalIgnoreCase))){throw 'Fixture needs a separate audit directory inside its fixture root'}
if(-not $fixture -and $AuditDirectory){throw 'Actual deployment must use its canonical audit directory'}
New-Item -ItemType Directory -Force $audit | Out-Null
$rollback=$Mode -in @('ValidateRollback','Rollback')
$pins=@(
 @{relative='r6/scripts/PTFR_Restrictions_R1/CyberwarePolicy.reds';before='D9CF279E8FB15BA2319CB6CFBB1D2B1E71656B691986D202D9F89CEA95D3CBD1';after='8F969B4170A7F0389CC004857C3C7887F18F698369AE0E7E3FA8E5B946BD7FC3'},
 @{relative='r6/scripts/PTFR_Restrictions_R2/BodyPolicy.reds';before='731758C7717CD164FA967DF993E480BE07C40B5BDF8096F6A770A933F0A36FAE';after='B4F6BF72EE7E3D222FA3F96B92EF27FC0D61E8FE72504B88F445B8B272984532'},
 @{relative='r6/scripts/PTFR_Restrictions_R2/DevelopmentHooks.reds';before='6D87171DCFCFFA1F4DC10276B7D30AF10BCFFAFF26A1989F324DE42AFDDF7BD3';after='40D13E958C8C5C4BF4FBB54F825A58508CB14E64FE325D43E763533928C95873'},
 @{relative='r6/scripts/PTFR_Restrictions_R3/ProfileDefinition.generated.reds';before=$null;after='5F742765A479E3BDC2404F812E0CB74C3D0AB10A74D8C26759FC21D2CA9AD338'},
 @{relative='r6/scripts/PTFR_Restrictions_R3/ProfileHooks.reds';before=$null;after='2BC6060FAD09771CE2498A639DF65D3A2652A554D063D26E251CBA392028184B'},
 @{relative='r6/scripts/PTFR_Restrictions_R3/ProfilePhysical.reds';before=$null;after='40EE422B1134BE27783E427767FDD2024C6D83FA72D86CE19C7EA230A616DF84'},
 @{relative='r6/scripts/PTFR_Restrictions_R3/ProfilePolicy.reds';before=$null;after='A38475983EE24FD678643D98D803E4BC10E5EBD927E11E83C55A25F89781A081'}
)
$scope=@($pins|ForEach-Object {$_.relative})
$targets=@($scope|ForEach-Object {R5Within (Join-Path $game $_) $game})
$testsPath=Join-Path $sourceAudit 'tests.json'
$tests=Get-Content -LiteralPath $testsPath -Raw | ConvertFrom-Json
if($tests.status -ne 'PASS_PROFILE_R3_OFFLINE_LIVE_PENDING' -or -not $tests.source_contracts -or -not $tests.equipmentex_full_compile){throw 'Profile offline source/full dependency compile checks missing'}
if(@($tests.checked_sources.PSObject.Properties).Count -ne 12){throw 'Expected twelve checked restriction sources'}
foreach($checked in $tests.checked_sources.PSObject.Properties){
 if([IO.Path]::IsPathRooted($checked.Name)){throw 'Checked source must be workspace-relative'}
 R5Match (R5Within (Join-Path $workspace $checked.Name) $workspace) $checked.Value
 $installedRelative=$checked.Name.Replace('redscript/','r6/scripts/')
 if($installedRelative -notin $scope){R5Match (R5Within (Join-Path $game $installedRelative) $game) $checked.Value}
}
$files=@($tests.files)
if($files.Count -ne 7 -or @(Compare-Object $scope @($files.relative)).Count -or @($files.relative|Select-Object -Unique).Count -ne 7){throw 'Unexpected Profile install scope'}
foreach($file in $files){
 if($file.source -ne $file.relative.Replace('r6/scripts/','redscript/')){throw 'Unexpected Profile source mapping'}
 $pin=@($pins|Where-Object {$_.relative -eq $file.relative})[0]
 if($file.before_sha256 -ne $pin.before -or $file.sha256 -ne $pin.after){throw 'Unexpected file predecessor/candidate hash'}
 if($tests.checked_sources.($file.source) -ne $file.sha256){throw 'Tested source mapping mismatch'}
 R5Match (R5Within (Join-Path $workspace $file.source) $workspace) $file.sha256
}
R5Match (Join-Path $game 'r6/cache/final.redscripts') $tests.base_sha256
foreach($entry in $tests.definition_inputs.PSObject.Properties){
 R5Match (R5Within (Join-Path $workspace $entry.Name) $workspace) $entry.Value
}
foreach($entry in $tests.tested_tools.PSObject.Properties){
 R5Match (R5Within (Join-Path $workspace $entry.Name) $workspace) $entry.Value
}
$receiptPath=Join-Path $audit 'install_receipt.json'
$rollbackPath=Join-Path $audit 'rollback_receipt.json'
$backupRoot=''
if($rollback){
 $receipt=Get-Content -LiteralPath $receiptPath -Raw | ConvertFrom-Json
 if($receipt.status -ne 'INSTALLED_PROFILE_R3_LIVE_PENDING' -or $receipt.game_root -ne $game){throw 'Receipt/root mismatch'}
 if(@($receipt.files).Count -ne 7 -or @(Compare-Object $scope @($receipt.files.relative)).Count -or @($receipt.files.relative|Select-Object -Unique).Count -ne 7){throw 'Receipt scope mismatch'}
 if($receipt.tests_sha256 -ne (R5Hash $testsPath) -or $receipt.installer_sha256 -ne (R5Hash $PSCommandPath)){throw 'Receipt build/tool mismatch'}
 $backupRoot=R5Within $receipt.backup_root $audit
 if(-not (Split-Path -Leaf $backupRoot).StartsWith('backup_')){throw 'Unexpected backup root'}
 foreach($file in $files){
  $entry=@($receipt.files|Where-Object relative -eq $file.relative)[0]
  if($entry.source -ne $file.source -or $entry.sha256 -ne $file.sha256 -or $entry.before_sha256 -ne $file.before_sha256){throw 'Receipt hash mismatch'}
  R5Match (R5Within (Join-Path $game $file.relative) $game) $file.sha256
  if($file.before_sha256){
   $expectedBackup=R5Within (Join-Path $backupRoot $file.relative) $backupRoot
   if($entry.backup -ne $expectedBackup){throw 'Receipt backup path mismatch'}
   R5Match $expectedBackup $file.before_sha256
  }elseif($entry.backup){throw 'An addition must not have a predecessor backup'}
 }
 if(Test-Path -LiteralPath $rollbackPath){throw 'Already rolled back'}
}else{
 foreach($file in $files){
  $target=R5Within (Join-Path $game $file.relative) $game
  if($file.before_sha256){R5Match $target $file.before_sha256}
  elseif(Test-Path -LiteralPath $target){throw 'Addition target exists; refusing overwrite'}
 }
 if(Test-Path -LiteralPath $receiptPath){throw 'Install receipt already exists'}
}
$dependencySnapshot=[ordered]@{}
if(-not $fixture){
 foreach($entry in $tests.protected_inputs.PSObject.Properties){
  $path=[IO.Path]::GetFullPath($entry.Name)
  if($path -notin $targets -and -not $path.StartsWith($actual+'\r6\cache\',[StringComparison]::OrdinalIgnoreCase)){
   R5Match $path $entry.Value
  }
 }
 if(-not @($tests.dependency_hashes.PSObject.Properties).Count -or -not @($tests.dependency_roots).Count){throw 'Dependency hashes/roots missing'}
 foreach($dep in $tests.dependency_hashes.PSObject.Properties){
  $path=R5Within $dep.Name $actual
  if($path -notin @($scope|ForEach-Object {R5Within (Join-Path $game $_) $game})){
   R5Match $path $dep.Value; $dependencySnapshot[$path]=$dep.Value
  }
 }
 # The staged candidate replaces these exact sources; every other enabled
 # source must still be part of the tested dependency inventory.
 $candidateTargets=@($tests.checked_sources.PSObject.Properties|ForEach-Object {R5Within (Join-Path $game $_.Name.Replace('redscript/','r6/scripts/')) $game})
 $observed=@()
 foreach($root in $tests.dependency_roots){
  $root=R5Within $root $actual
  if(-not (Test-Path -LiteralPath $root -PathType Container)){throw 'Dependency directory missing'}
  $observed+=@(Get-ChildItem -LiteralPath $root -Filter '*.reds' -File -Recurse|Where-Object FullName -notin $candidateTargets|ForEach-Object FullName)
 }
 $expected=@($dependencySnapshot.Keys|Where-Object {$_ -notin $candidateTargets})
 if(@(Compare-Object @($observed|Sort-Object -Unique) @($expected|Sort-Object -Unique)).Count){throw 'Enabled source inventory differs from the compiled dependency set'}
}
if($Mode -eq 'Install' -and -not $fixture){
 $deployment=Get-Content -LiteralPath (Join-Path $sourceAudit 'deployment_tests.json') -Raw|ConvertFrom-Json
 if($deployment.status -ne 'PASS_PROFILE_R3_INSTALL_ROLLBACK_FIXTURE'){throw 'Profile workspace deployment fixture pass missing'}
 R5Match $PSCommandPath $deployment.installer_sha256
 R5Match $testsPath $deployment.tests_sha256
 R5Match (Join-Path $PSScriptRoot 'test_restrictions_profile_r3_deployment.ps1') $deployment.fixture_sha256
 R5Match (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1') $deployment.helpers_sha256
}
R5Closed
$targets=@($files|ForEach-Object {R5Within (Join-Path $game $_.relative) $game})
$protected=R5Snapshot $game $targets
$cacheHashes=[ordered]@{}
foreach($name in @('final.redscripts','final.redscripts.modded','final.redscripts.ts','tweakdb.bin','tweakdb_ep1.bin')){
 $path=R5Within (Join-Path $game ('r6/cache/'+$name)) $game
 if(-not (Test-Path -LiteralPath $path -PathType Leaf)){throw 'Required existing cache/database file missing'}
 $cacheHashes[$path]=R5Hash $path
}
R5Unchanged $protected;R5Unchanged $cacheHashes;R5Unchanged $dependencySnapshot
if($Mode -like 'Validate*'){
 $result=@{status=('PROFILE_R3_'+$Mode.ToUpper());game_root=$game;replacements=3;additions=$(if($rollback){0}else{4});removals=$(if($rollback){4}else{0});protected_files=$protected.Count;cache_files=$cacheHashes.Count;game_unchanged=$true;progression_rollback=$false}
 R5Json (Join-Path $audit ($Mode+'.json')) $result
 $result|ConvertTo-Json;return
}
$tag=[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')+'_'+[guid]::NewGuid().ToString('N').Substring(0,8)
$recovery=R5Within (Join-Path $audit ('recoverable_'+$tag)) $audit
if(-not $rollback){
 $backupRoot=R5Within (Join-Path $audit ('backup_'+$tag)) $audit
 foreach($file in $files|Where-Object before_sha256){
  $backup=R5Within (Join-Path $backupRoot $file.relative) $backupRoot
  $target=R5Within (Join-Path $game $file.relative) $game
  New-Item -ItemType Directory -Force (Split-Path -Parent $backup)|Out-Null
  R5Closed;R5Match $target $file.before_sha256
  [IO.File]::Copy($target,$backup,$false);R5Match $backup $file.before_sha256
 }
}
$attempted=[Collections.Generic.List[object]]::new()
$receiptFiles=[Collections.Generic.List[object]]::new()
try{
 foreach($file in $files){
  R5Closed
  $target=R5Within (Join-Path $game $file.relative) $game
  $source=R5Within (Join-Path $workspace $file.source) $workspace
  $saved=R5Within (Join-Path $recovery $file.relative) $recovery
  $backup=if($file.before_sha256){R5Within (Join-Path $backupRoot $file.relative) $backupRoot}else{''}
  R5Match $source $file.sha256
  if($rollback){
   R5Match $target $file.sha256
   New-Item -ItemType Directory -Force (Split-Path -Parent $saved)|Out-Null
   if($backup){
    R5Match $backup $file.before_sha256
    [IO.File]::Copy($target,$saved,$false);R5Match $saved $file.sha256
    $attempted.Add($file)
    [IO.File]::Copy($backup,$target,$true);R5Match $target $file.before_sha256
   }else{
    $attempted.Add($file)
    Move-Item -LiteralPath $target -Destination $saved
    R5Match $saved $file.sha256
   }
  }else{
   if($backup){R5Match $target $file.before_sha256;R5Match $backup $file.before_sha256}
   elseif(Test-Path -LiteralPath $target){throw 'Addition appeared during deployment'}
   New-Item -ItemType Directory -Force (Split-Path -Parent $target)|Out-Null
   $attempted.Add($file)
   [IO.File]::Copy($source,$target,[bool]$backup);R5Match $target $file.sha256
  }
  $receiptFiles.Add(@{relative=$file.relative;source=$file.source;sha256=$file.sha256;before_sha256=$file.before_sha256;backup=$backup})
 }
 R5Closed;R5Unchanged $protected;R5Unchanged $cacheHashes;R5Unchanged $dependencySnapshot
 $afterProtected=R5Snapshot $game $targets
 if(@(Compare-Object @($protected.Keys) @($afterProtected.Keys)).Count){throw 'Protected file inventory changed during deployment'}
 $result=[ordered]@{status=$(if($rollback){'ROLLED_BACK_PROFILE_R3_FILES_ONLY'}else{'INSTALLED_PROFILE_R3_LIVE_PENDING'});utc=[DateTime]::UtcNow.ToString('o');game_root=$game;files=@($receiptFiles);replacements=3;additions=$(if($rollback){0}else{4});removals=$(if($rollback){4}else{0});protected_files=$protected.Count;protected_hashes=$protected;cache_hashes=$cacheHashes;dependency_hashes=$dependencySnapshot;backup_root=$backupRoot;recovery=$recovery;game_closed=$true;live_tested=$false;save_writes=0;story_writes=0;progression_rollback=$false;warning='File rollback does not reverse saved Body/Profile refunds or restore spent progression. Use an untouched pre-test save for full recovery.';tests_sha256=(R5Hash $testsPath);installer_sha256=(R5Hash $PSCommandPath)}
 R5Json $(if($rollback){$rollbackPath}else{$receiptPath}) $result
 [pscustomobject]$result|Select-Object status,utc,replacements,additions,removals,protected_files|ConvertTo-Json
}catch{
 $failure=$_.Exception.Message
 $errors=[Collections.Generic.List[string]]::new()
 for($i=$attempted.Count-1;$i -ge 0;$i--){
  $file=$attempted[$i]
  try{
   R5Closed
   $target=R5Within (Join-Path $game $file.relative) $game
   $saved=R5Within (Join-Path $recovery $file.relative) $recovery
   if($rollback){
    if(Test-Path -LiteralPath $target){
     if((R5Hash $target) -eq $file.sha256){continue}
     if(-not $file.before_sha256 -or (R5Hash $target) -ne $file.before_sha256){throw 'Unknown target changed during rollback; refusing overwrite'}
    }
    R5Match $saved $file.sha256
    [IO.File]::Copy($saved,$target,[bool]$file.before_sha256);R5Match $target $file.sha256
   }elseif($file.before_sha256){
    if((R5Hash $target) -eq $file.before_sha256){continue}
    R5Match $target $file.sha256
    $backup=R5Within (Join-Path $backupRoot $file.relative) $backupRoot
    R5Match $backup $file.before_sha256
    [IO.File]::Copy($backup,$target,$true);R5Match $target $file.before_sha256
   }elseif(Test-Path -LiteralPath $target){
    R5Match $target $file.sha256
    New-Item -ItemType Directory -Force (Split-Path -Parent $saved)|Out-Null
    Move-Item -LiteralPath $target -Destination $saved
   }
  }catch{$errors.Add($_.Exception.Message)}
 }
 R5Json (Join-Path $audit 'deployment_failure.json') @{failure=$failure;backup_root=$backupRoot;recovery=$recovery;recovery_errors=@($errors);warning='Do not launch after a failed deployment until exact file hashes are checked. No save rollback was performed.'}
 throw $failure
}
