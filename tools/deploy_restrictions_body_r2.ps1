param(
 [string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),
 [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
 [string]$AuditDirectory='',
 [ValidateSet('ValidateInstall','Install','ValidateRollback','Rollback')][string]$Mode='ValidateInstall'
)
# File-only deployment. Rolling these files back does NOT undo saved Body/perk
# refunds or restore points already spent elsewhere. Never modify save files.
. (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1')
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\')
$sourceAudit=Join-Path $workspace 'research\restriction_profiles\body_r2'
$audit=if($AuditDirectory){R5Within $AuditDirectory $workspace}else{$sourceAudit}
$game=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
$actual='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$fixture=$game.StartsWith($sourceAudit+'\fixture_',[StringComparison]::OrdinalIgnoreCase)
if($game -ne $actual -and -not $fixture){throw 'Unsupported deployment root'}
if($fixture -and (-not $AuditDirectory -or -not $audit.StartsWith((Split-Path -Parent $game)+'\',[StringComparison]::OrdinalIgnoreCase))){throw 'Fixture needs a separate audit directory inside its fixture root'}
if(-not $fixture -and $AuditDirectory){throw 'Actual deployment must use its canonical audit directory'}
New-Item -ItemType Directory -Force $audit | Out-Null
$rollback=$Mode -in @('ValidateRollback','Rollback')
$replacement='r6/scripts/PTFR_Restrictions_R1/CyberwarePolicy.reds'
$beforeHash='105434C7AFCDC50C6CB8C8936EB0FA7E26708B5981BBAD9DA2D224BD689FCC5C'
$scope=@($replacement,'r6/scripts/PTFR_Restrictions_R2/BodyPolicy.reds','r6/scripts/PTFR_Restrictions_R2/BodyCatalogue.reds','r6/scripts/PTFR_Restrictions_R2/DevelopmentHooks.reds')
$testsPath=Join-Path $sourceAudit 'tests.json'
$tests=Get-Content -LiteralPath $testsPath -Raw | ConvertFrom-Json
if($tests.status -ne 'PASS_RESTRICTIONS_BODY_R2_OFFLINE_LIVE_PENDING' -or -not $tests.source_audit -or -not $tests.equipmentex_full_compile){throw 'R2 offline source/full dependency compile checks missing'}
if(-not @($tests.checked_sources.PSObject.Properties).Count){throw 'Checked source hashes missing'}
foreach($checked in $tests.checked_sources.PSObject.Properties){
 if([IO.Path]::IsPathRooted($checked.Name)){throw 'Checked source must be workspace-relative'}
 R5Match (R5Within (Join-Path $workspace $checked.Name) $workspace) $checked.Value
}
$files=@($tests.files)
if($files.Count -ne 4 -or @(Compare-Object $scope @($files.relative)).Count -or @($files.relative|Select-Object -Unique).Count -ne 4){throw 'Unexpected R2 install scope'}
foreach($file in $files){
 if($file.source -ne $file.relative.Replace('r6/scripts/','redscript/')){throw 'Unexpected R2 source mapping'}
 if($file.relative -eq $replacement){if($file.before_sha256 -ne $beforeHash){throw 'Unexpected replacement predecessor'}}
 elseif($file.before_sha256){throw 'New R2 files must be additions'}
 R5Match (R5Within (Join-Path $workspace $file.source) $workspace) $file.sha256
}
R5Match (Join-Path $game 'r6/cache/final.redscripts') $tests.base_sha256
$receiptPath=Join-Path $audit 'install_receipt.json'
$rollbackPath=Join-Path $audit 'rollback_receipt.json'
$backupRoot=''
if($rollback){
 $receipt=Get-Content -LiteralPath $receiptPath -Raw | ConvertFrom-Json
 if($receipt.status -ne 'INSTALLED_RESTRICTIONS_BODY_R2_LIVE_PENDING' -or $receipt.game_root -ne $game){throw 'Receipt/root mismatch'}
 if(@($receipt.files).Count -ne 4 -or @(Compare-Object $scope @($receipt.files.relative)).Count -or @($receipt.files.relative|Select-Object -Unique).Count -ne 4){throw 'Receipt scope mismatch'}
 if($receipt.tests_sha256 -ne (R5Hash $testsPath) -or $receipt.installer_sha256 -ne (R5Hash $PSCommandPath)){throw 'Receipt build/tool mismatch'}
 $backupRoot=R5Within $receipt.backup_root $audit
 if(-not (Split-Path -Leaf $backupRoot).StartsWith('backup_')){throw 'Unexpected backup root'}
 foreach($file in $files){
  $entry=@($receipt.files|Where-Object relative -eq $file.relative)[0]
  if($entry.sha256 -ne $file.sha256 -or $entry.before_sha256 -ne $file.before_sha256){throw 'Receipt hash mismatch'}
  R5Match (R5Within (Join-Path $game $file.relative) $game) $file.sha256
  if($file.relative -eq $replacement){
   $expectedBackup=R5Within (Join-Path $backupRoot $replacement) $backupRoot
   if($entry.backup -ne $expectedBackup){throw 'Receipt backup path mismatch'}
   R5Match $expectedBackup $beforeHash
  }elseif($entry.backup){throw 'An addition must not have a predecessor backup'}
 }
 if(Test-Path -LiteralPath $rollbackPath){throw 'Already rolled back'}
}else{
 R5Match (R5Within (Join-Path $game $replacement) $game) $beforeHash
 foreach($file in $files|Where-Object relative -ne $replacement){
  if(Test-Path -LiteralPath (R5Within (Join-Path $game $file.relative) $game)){throw 'Addition target exists; refusing overwrite'}
 }
 if(Test-Path -LiteralPath $receiptPath){throw 'Install receipt already exists'}
}
$dependencySnapshot=[ordered]@{}
if(-not $fixture){
 $r1=Get-Content -LiteralPath (Join-Path $workspace 'research/restriction_profiles/implementation_r1/install_receipt.json') -Raw|ConvertFrom-Json
 foreach($file in $r1.files|Where-Object relative -ne $replacement){R5Match (R5Within (Join-Path $game $file.relative) $game) $file.sha256}
 $r11=Get-Content -LiteralPath (Join-Path $workspace 'research/afterlife_world/interactions_r11/install_receipt.json') -Raw|ConvertFrom-Json
 foreach($file in $r11.files){R5Match (R5Within (Join-Path $game $file.relative) $game) $file.sha256}
 if(-not @($tests.dependency_hashes.PSObject.Properties).Count -or -not @($tests.dependency_roots).Count){throw 'Dependency hashes/roots missing'}
 foreach($dep in $tests.dependency_hashes.PSObject.Properties){
  $path=R5Within $dep.Name $actual
  if($path -notin @($scope|ForEach-Object {R5Within (Join-Path $game $_) $game})){
   R5Match $path $dep.Value; $dependencySnapshot[$path]=$dep.Value
  }
 }
 # The staged candidate replaces these exact sources; every other enabled
 # source must still be part of the tested dependency inventory.
 $candidateTargets=@($scope|ForEach-Object {R5Within (Join-Path $game $_) $game})
 $candidateTargets+=@(Join-Path $game 'r6/scripts/PTFR_Restrictions_R1/EquipmentHooks.reds';Join-Path $game 'r6/scripts/PTFR_Restrictions_R1/RipperdocHooks.reds')
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
 if($deployment.status -ne 'PASS_RESTRICTIONS_BODY_R2_INSTALL_ROLLBACK_FIXTURE'){throw 'R2 workspace deployment fixture pass missing'}
 R5Match $PSCommandPath $deployment.installer_sha256
 R5Match $testsPath $deployment.tests_sha256
 R5Match (Join-Path $PSScriptRoot 'test_restrictions_body_r2_deployment.ps1') $deployment.fixture_sha256
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
 $result=@{status=('RESTRICTIONS_BODY_R2_'+$Mode.ToUpper());game_root=$game;replacements=1;additions=$(if($rollback){0}else{3});removals=$(if($rollback){3}else{0});protected_files=$protected.Count;cache_files=$cacheHashes.Count;game_unchanged=$true;progression_rollback=$false}
 R5Json (Join-Path $audit ($Mode+'.json')) $result
 $result|ConvertTo-Json;return
}
$tag=[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')+'_'+[guid]::NewGuid().ToString('N').Substring(0,8)
$recovery=R5Within (Join-Path $audit ('recoverable_'+$tag)) $audit
if(-not $rollback){
 $backupRoot=R5Within (Join-Path $audit ('backup_'+$tag)) $audit
 $backup=R5Within (Join-Path $backupRoot $replacement) $backupRoot
 New-Item -ItemType Directory -Force (Split-Path -Parent $backup)|Out-Null
 R5Closed;R5Match (Join-Path $game $replacement) $beforeHash
 [IO.File]::Copy((Join-Path $game $replacement),$backup,$false);R5Match $backup $beforeHash
}
$attempted=[Collections.Generic.List[object]]::new()
$receiptFiles=[Collections.Generic.List[object]]::new()
try{
 foreach($file in $files){
  R5Closed
  $target=R5Within (Join-Path $game $file.relative) $game
  $source=R5Within (Join-Path $workspace $file.source) $workspace
  $saved=R5Within (Join-Path $recovery $file.relative) $recovery
  $backup=if($file.relative -eq $replacement){R5Within (Join-Path $backupRoot $file.relative) $backupRoot}else{''}
  R5Match $source $file.sha256
  if($rollback){
   R5Match $target $file.sha256
   New-Item -ItemType Directory -Force (Split-Path -Parent $saved)|Out-Null
   if($backup){
    R5Match $backup $beforeHash
    [IO.File]::Copy($target,$saved,$false);R5Match $saved $file.sha256
    $attempted.Add($file)
    [IO.File]::Copy($backup,$target,$true);R5Match $target $beforeHash
   }else{
    $attempted.Add($file)
    Move-Item -LiteralPath $target -Destination $saved
    R5Match $saved $file.sha256
   }
  }else{
   if($backup){R5Match $target $beforeHash;R5Match $backup $beforeHash}
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
 $result=[ordered]@{status=$(if($rollback){'ROLLED_BACK_RESTRICTIONS_BODY_R2_FILES_ONLY'}else{'INSTALLED_RESTRICTIONS_BODY_R2_LIVE_PENDING'});utc=[DateTime]::UtcNow.ToString('o');game_root=$game;files=@($receiptFiles);replacements=1;additions=$(if($rollback){0}else{3});removals=$(if($rollback){3}else{0});protected_files=$protected.Count;protected_hashes=$protected;cache_hashes=$cacheHashes;dependency_hashes=$dependencySnapshot;backup_root=$backupRoot;recovery=$recovery;game_closed=$true;live_tested=$false;save_writes=0;story_writes=0;progression_rollback=$false;warning='File rollback does not reverse saved Body/perk refunds or restore spent progression. Use an untouched pre-test save for full recovery.';tests_sha256=(R5Hash $testsPath);installer_sha256=(R5Hash $PSCommandPath)}
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
     if($file.relative -ne $replacement -or (R5Hash $target) -ne $beforeHash){throw 'Unknown target changed during rollback; refusing overwrite'}
    }
    R5Match $saved $file.sha256
    [IO.File]::Copy($saved,$target,($file.relative -eq $replacement));R5Match $target $file.sha256
   }elseif($file.relative -eq $replacement){
    if((R5Hash $target) -eq $beforeHash){continue}
    R5Match $target $file.sha256
    $backup=R5Within (Join-Path $backupRoot $file.relative) $backupRoot
    R5Match $backup $beforeHash
    [IO.File]::Copy($backup,$target,$true);R5Match $target $beforeHash
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
