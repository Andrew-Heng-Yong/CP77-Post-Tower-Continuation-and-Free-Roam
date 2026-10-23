param(
 [string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),
 [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
 [string]$AuditDirectory='',
 [ValidateSet('ValidateInstall','Install','ValidateRollback','Rollback')][string]$Mode='ValidateInstall'
)
# Exact two-replacement/two-addition deployment. File rollback cannot reverse
# saved Body or Relic refunds. No save files or compiler caches are deployed.
. (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1')
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\')
$sourceAudit=Join-Path $workspace 'research\restriction_profiles\relic_r2_2'
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
 @{name='BodyPolicy.reds';before='187A1ED8489FDC43EE77DE21475736534D05DAEC97FEB340EE1EC15AACDFA868';after='731758C7717CD164FA967DF993E480BE07C40B5BDF8096F6A770A933F0A36FAE'},
 @{name='DevelopmentHooks.reds';before='0BF91CD59E8D8414ED57BF44DED0067FED847CDAD0BFB4B85462E678A6316D6D';after='6D87171DCFCFFA1F4DC10276B7D30AF10BCFFAFF26A1989F324DE42AFDDF7BD3'},
 @{name='RelicCatalogue.reds';before=$null;after='376FBA3D8DAD24DD3C6F2AB7C9147D5B3CB662F37893C3A4F983D8910FE3C24C'},
 @{name='RelicMenu.reds';before=$null;after='220616A6F6E3A107633E50FC424BDABC0A193ECC0F3D706C19E4FD2BA7F1D8DF'}
)
$scope=@($pins|ForEach-Object {'r6/scripts/PTFR_Restrictions_R2/'+$_.name})
$targets=@($scope|ForEach-Object {R5Within (Join-Path $game $_) $game})
$testsPath=Join-Path $sourceAudit 'tests.json'
$tests=Get-Content -LiteralPath $testsPath -Raw | ConvertFrom-Json
if($tests.status -ne 'PASS_RELIC_R2_2_OFFLINE_LIVE_PENDING' -or -not $tests.source_contracts -or -not $tests.equipmentex_full_compile){throw 'Relic offline source/full dependency compile checks missing'}
if(@($tests.checked_sources.PSObject.Properties).Count -ne 8){throw 'Expected eight checked restriction sources'}
foreach($checked in $tests.checked_sources.PSObject.Properties){
 if([IO.Path]::IsPathRooted($checked.Name)){throw 'Checked source must be workspace-relative'}
 R5Match (R5Within (Join-Path $workspace $checked.Name) $workspace) $checked.Value
 $installedRelative=$checked.Name.Replace('redscript/','r6/scripts/')
 if($installedRelative -notin $scope){R5Match (R5Within (Join-Path $game $installedRelative) $game) $checked.Value}
}
$files=@($tests.files)
if($files.Count -ne 4 -or @(Compare-Object $scope @($files.relative)).Count -or @($files.relative|Select-Object -Unique).Count -ne 4){throw 'Unexpected Relic install scope'}
foreach($file in $files){
 if($file.source -ne $file.relative.Replace('r6/scripts/','redscript/')){throw 'Unexpected Relic source mapping'}
 $pin=@($pins|Where-Object {('r6/scripts/PTFR_Restrictions_R2/'+$_.name) -eq $file.relative})[0]
 if($file.before_sha256 -ne $pin.before -or $file.sha256 -ne $pin.after){throw 'Unexpected file predecessor/candidate hash'}
 if($tests.checked_sources.($file.source) -ne $file.sha256){throw 'Tested source mapping mismatch'}
 R5Match (R5Within (Join-Path $workspace $file.source) $workspace) $file.sha256
}
R5Match (Join-Path $game 'r6/cache/final.redscripts') $tests.base_sha256
$receiptPath=Join-Path $audit 'install_receipt.json'
$rollbackPath=Join-Path $audit 'rollback_receipt.json'
$backupRoot=''
if($rollback){
 $receipt=Get-Content -LiteralPath $receiptPath -Raw | ConvertFrom-Json
 if($receipt.status -ne 'INSTALLED_RELIC_R2_2_LIVE_PENDING' -or $receipt.game_root -ne $game){throw 'Receipt/root mismatch'}
 if(@($receipt.files).Count -ne 4 -or @(Compare-Object $scope @($receipt.files.relative)).Count -or @($receipt.files.relative|Select-Object -Unique).Count -ne 4){throw 'Receipt scope mismatch'}
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
 if($deployment.status -ne 'PASS_RELIC_R2_2_INSTALL_ROLLBACK_FIXTURE'){throw 'Relic workspace deployment fixture pass missing'}
 R5Match $PSCommandPath $deployment.installer_sha256
 R5Match $testsPath $deployment.tests_sha256
 R5Match (Join-Path $PSScriptRoot 'test_restrictions_relic_r2_2_deployment.ps1') $deployment.fixture_sha256
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
 $result=@{status=('RELIC_R2_2_'+$Mode.ToUpper());game_root=$game;replacements=2;additions=$(if($rollback){0}else{2});removals=$(if($rollback){2}else{0});protected_files=$protected.Count;cache_files=$cacheHashes.Count;game_unchanged=$true;progression_rollback=$false}
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
 $result=[ordered]@{status=$(if($rollback){'ROLLED_BACK_RELIC_R2_2_FILES_ONLY'}else{'INSTALLED_RELIC_R2_2_LIVE_PENDING'});utc=[DateTime]::UtcNow.ToString('o');game_root=$game;files=@($receiptFiles);replacements=2;additions=$(if($rollback){0}else{2});removals=$(if($rollback){2}else{0});protected_files=$protected.Count;protected_hashes=$protected;cache_hashes=$cacheHashes;dependency_hashes=$dependencySnapshot;backup_root=$backupRoot;recovery=$recovery;game_closed=$true;live_tested=$false;save_writes=0;story_writes=0;progression_rollback=$false;warning='File rollback does not reverse saved Body/Relic refunds or restore spent progression. Use an untouched pre-test save for full recovery.';tests_sha256=(R5Hash $testsPath);installer_sha256=(R5Hash $PSCommandPath)}
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
