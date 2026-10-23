param(
 [string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),
 [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
 [string]$AuditDirectory='',
 [ValidateSet('ValidateInstall','Install','ValidateRollback','Rollback')][string]$Mode='ValidateInstall',
 [ValidateRange(0,12)][int]$FixtureFailAfterCopies=0,
 [ValidateRange(0,12)][int]$FixtureFailAfterMoves=0
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\')
$root=Join-Path $workspace 'research/gig_restoration/gig_batch_u9'
$game=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
$actual='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$fixture=$game.StartsWith($root+'\fixture_',[StringComparison]::OrdinalIgnoreCase)
if($game -ne $actual -and -not $fixture){throw 'Unsupported game root'}
if(-not $fixture -and ($FixtureFailAfterCopies -or $FixtureFailAfterMoves)){throw 'Failure injection is fixture-only'}
$helperNames=@('shark_b7_2_helpers.ps1','gig_family_b7_1_xl.ps1','afterlife_faces_r5_deployment.ps1')
$helperPins=[ordered]@{}
foreach($name in $helperNames){$helperPins['tools/'+$name]=(Get-FileHash -LiteralPath (Join-Path $PSScriptRoot $name) -Algorithm SHA256).Hash}
# Verify the entire imported helper chain BEFORE executing it.
if(-not $fixture){
 $d=Get-Content -LiteralPath (Join-Path $root 'deployment_tests.json') -Raw|ConvertFrom-Json
 if($d.status -ne 'PASS_U9_ADDITIVE_RECOVERABLE_FIXTURE' -or $d.installer_sha256 -ne (Get-FileHash -LiteralPath $PSCommandPath).Hash){throw 'Fixture tests stale'}
 if(@($d.helper_pins.PSObject.Properties).Count -ne $helperNames.Count){throw 'Missing helper pins'}
 foreach($p in $helperPins.Keys){if($d.helper_pins.$p -ne $helperPins[$p]){throw "Deployment helper changed: $p"}}
 if($d.test_sha256 -ne (Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'test_gig_batch_u9_deployment.ps1')).Hash){throw 'Deployment fixture changed'}
}
. (Join-Path $PSScriptRoot 'shark_b7_2_helpers.ps1')
function NoReparseU9([string]$Path){
 $cursor=[IO.Path]::GetFullPath($Path)
 while($cursor){
  if(Test-Path -LiteralPath $cursor){$item=Get-Item -LiteralPath $cursor -Force;if(($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw "Reparse path not supported: $cursor"}}
  $parent=Split-Path -Parent $cursor;if(-not $parent -or $parent -eq $cursor){break};$cursor=$parent
 }
}
function BoundU9([string]$Path,[string]$Root){$p=R5Within $Path $Root;NoReparseU9 $p;return $p}
$audit=if($AuditDirectory){BoundU9 $AuditDirectory $workspace}else{$root}
NoReparseU9 $game;NoReparseU9 $audit
if($fixture -and (-not $AuditDirectory -or (Split-Path -Leaf $game) -cne 'game' -or $audit -cne (Join-Path (Split-Path -Parent $game) 'audit'))){throw 'Fixture game/audit must be paired game and audit directories'}
if(-not $fixture -and $AuditDirectory){throw 'Actual audit must be canonical'}
R5Closed
$mp=Join-Path $root 'manifest.json';$tp=Join-Path $root 'tests.json'
$m=Get-Content -LiteralPath $mp -Raw|ConvertFrom-Json
$t=Get-Content -LiteralPath $tp -Raw|ConvertFrom-Json
if($m.status -ne 'BUILT_U9_GIG_ONLY_BATCH_LIVE_PENDING' -or $m.replacements -ne 0){throw 'Wrong package'}
if($t.status -ne 'PASS_U9_COMBINED_OFFLINE_LIVE_PENDING' -or $t.manifest_sha256 -ne (R5Hash $mp) -or -not $t.full_scc -or -not $t.compiled_readback -or -not $t.cross_package_collisions){throw 'Tests stale'}
R5Match (Join-Path $workspace 'tools/validate_gig_batch_u9.py') $t.validator_sha256
foreach($p in $m.source_pins.PSObject.Properties){R5Match (BoundU9 (Join-Path $workspace $p.Name) $workspace) $p.Value}
$files=@($m.files);$targets=@();$relSeen=@{}
foreach($f in $files){
 if($f.predecessor){throw 'U9 deployment must be additive'}
 if($f.relative -cnotmatch '^(archive/pc/mod/TowerContinued_(GigPhoneU9|NativeGigsU9|SpecialGigsU9)\.archive(\.xl)?|r6/scripts/PTFR_(GigPhoneU9|NativeGigsU9|GigBatchU9)/[A-Za-z0-9_.]+\.reds|bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_GigBatchU9/init\.lua)$'){throw 'Target outside U9 additive scope'}
 if($relSeen.ContainsKey($f.relative.ToLowerInvariant())){throw 'Duplicate target'};$relSeen[$f.relative.ToLowerInvariant()]=$true
 if($f.source -cnotmatch '^(build/(GigPhoneU9|NativeGigsU9|SpecialGigsU9)/TowerContinued_(GigPhoneU9|NativeGigsU9|SpecialGigsU9)\.archive(\.xl)?|redscript/PTFR_(GigPhoneU9|NativeGigsU9|GigBatchU9)/[A-Za-z0-9_.]+\.reds|diagnostics/PTFR_GigBatchU9/init\.lua)$'){throw 'Source outside U9 scope'}
 R5Match (BoundU9 (Join-Path $workspace $f.source) $workspace) $f.sha256
 $targets+=BoundU9 (Join-Path $game $f.relative) $game
}
if($files.Count -ne $m.additions -or $files.Count -ne 12 -or $m.gig_count -ne 72){throw 'Incomplete package'}
B71Parser|Out-Null
$declared=@()
foreach($f in $files|Where-Object relative -like '*.xl'){
 $y=B71Parse (Get-Content -LiteralPath (Join-Path $workspace $f.source) -Raw)
 $ph=B71Child (B71Child $y 'quest') 'phases'
 foreach($e in $ph.Children){
  if((B71Child $e 'parent').Value -cne 'ep1\quest\ep1.quest'){throw 'Wrong quest parent'}
  $nodes=B71Child (B71Child $e 'input') 'node'
  if($nodes.Children.Count -ne 1 -or $nodes.Children[0].Value -cne '1'){throw 'Wrong quest input'}
  $declared+=(B71Child $e 'path').Value
 }
}
if((($declared|Sort-Object) -join '|') -cne (($m.boots|Sort-Object) -join '|')){throw 'Registration manifest mismatch'}
$rp=Join-Path $audit 'install_receipt.json';$transactionPath=Join-Path $audit 'install_transaction.json'
$progressPath=Join-Path $audit 'rollback_progress.json';$rollbackPath=Join-Path $audit 'rollback_receipt.json'
$rollback=$Mode -in @('ValidateRollback','Rollback');$recoverable=$null;$recoveryFiles=@();$partialInstall=$false
function ReceiptU9($r,[string]$ExpectedStatus){
 if($r.status -cne $ExpectedStatus -or $r.game_root -cne $game -or $r.manifest_sha256 -cne (R5Hash $mp) -or $r.installer_sha256 -cne (R5Hash $PSCommandPath)){throw 'Receipt mismatch'}
 if(@($r.helper_pins.PSObject.Properties).Count -ne $helperNames.Count){throw 'Receipt missing helper pins'}
 foreach($p in $helperPins.Keys){if($r.helper_pins.$p -cne $helperPins[$p]){throw 'Receipt helper drift'}}
}
if($rollback){
 if(Test-Path -LiteralPath $rollbackPath){throw 'Already recovered'}
 if(Test-Path -LiteralPath $rp){$r=Get-Content -LiteralPath $rp -Raw|ConvertFrom-Json;ReceiptU9 $r 'INSTALLED_U9_GIG_BATCH_LIVE_PENDING'}
 elseif(Test-Path -LiteralPath $transactionPath){$r=Get-Content -LiteralPath $transactionPath -Raw|ConvertFrom-Json;ReceiptU9 $r 'U9_INSTALL_TRANSACTION';$partialInstall=$true}
 else{throw 'No verified install or partial-install transaction'}
 if(Test-Path -LiteralPath $progressPath){
  $progress=Get-Content -LiteralPath $progressPath -Raw|ConvertFrom-Json;ReceiptU9 $progress 'U9_ROLLBACK_IN_PROGRESS'
  $recoverable=BoundU9 $progress.recoverable $audit
  if((Split-Path -Parent $recoverable) -cne $audit -or (Split-Path -Leaf $recoverable) -cnotmatch '^recoverable_[0-9TZ]+$'){throw 'Recovery directory scope mismatch'}
  $rel=@($progress.files|ForEach-Object {$_.relative});if(@($rel|Select-Object -Unique).Count -ne $rel.Count){throw 'Duplicate recovery file'}
  foreach($f in $progress.files){
   $expected=@($files|Where-Object relative -ceq $f.relative)
   if($expected.Count -ne 1 -or $f.sha256 -cne $expected[0].sha256){throw 'Recovery file not in manifest'}
  }
  if(-not $partialInstall -and $rel.Count -ne $files.Count){throw 'Full recovery scope incomplete'}
  $recoveryFiles=@($progress.files)
  foreach($f in $files){
   $target=BoundU9 (Join-Path $game $f.relative) $game;$dest=BoundU9 (Join-Path $recoverable $f.relative) $recoverable
   $atTarget=Test-Path -LiteralPath $target;$atDest=Test-Path -LiteralPath $dest
   if($f.relative -cin $rel){
    if($atTarget -eq $atDest){throw 'Recovery file must exist at exactly one verified location'}
    R5Match $(if($atTarget){$target}else{$dest}) $f.sha256
   }elseif($atTarget -or $atDest){throw 'Unexpected file outside partial recovery plan'}
  }
 }else{
  foreach($f in $files){
   $target=BoundU9 (Join-Path $game $f.relative) $game
   if(Test-Path -LiteralPath $target){R5Match $target $f.sha256;$recoveryFiles+=,$f}
   elseif(-not $partialInstall){throw 'Installed file missing without recovery progress'}
  }
 }
}else{
 foreach($p in @($rp,$transactionPath,$progressPath,$rollbackPath)){if(Test-Path -LiteralPath $p){throw 'Existing install/recovery evidence; do not rerun installation'}}
 foreach($p in $targets){if(Test-Path -LiteralPath $p){throw "Addition exists: $p"}}
}
# Never hide a foreign XL that happens to register the same depot. During
# rollback omit ONLY our exact-file/hash-verified registrations.
$ownXlNames=@()
if($rollback){foreach($f in $recoveryFiles|Where-Object relative -like '*.xl'){
 $target=BoundU9 (Join-Path $game $f.relative) $game
 if(Test-Path -LiteralPath $target){R5Match $target $f.sha256;$ownXlNames+=Split-Path -Leaf $target}
}}
$inventory=@();$modRoot=Join-Path $game 'archive/pc/mod'
if(Test-Path -LiteralPath $modRoot){$inventory=@(B72Inventory $game|Where-Object {$_.source -cnotin $ownXlNames})}
foreach($depot in $m.boots){
 $id=B72Id ($depot+':1');$expected=@($m.collisions|Where-Object depot -ceq $depot)
 if($expected.Count -ne 1 -or $id -ne $expected[0].node_id -or $id -in @($inventory|ForEach-Object {$_.id})){throw 'Registration collision drift'}
 if(-not $fixture){B72CollisionCheck $inventory $workspace $depot|Out-Null}
 $inventory+=@{path=$depot;id=$id;source='U9_batch'}
}
if(-not $fixture){
 if($d.tests_sha256 -ne (R5Hash $tp)){throw 'Fixture tests stale'}
 foreach($p in $t.dependencies.PSObject.Properties){R5Match $p.Name $p.Value}
}
$protected=R5Snapshot $game $targets
if(-not $fixture){
 foreach($folder in @('archive/pc/mod','red4ext/plugins','r6/scripts','r6/cache')){
  foreach($p in Get-ChildItem -LiteralPath (Join-Path $game $folder) -Recurse -File){
   if($p.FullName -notin $targets -and ($folder -eq 'r6/cache' -or $p.Extension -in @('.archive','.xl','.reds','.dll'))){$protected[$p.FullName]=R5Hash $p.FullName}
  }
 }
 $saveRoot='C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077'
 foreach($p in Get-ChildItem -LiteralPath $saveRoot -Recurse -File){$protected[$p.FullName]=R5Hash $p.FullName}
}
R5Closed
if($Mode.StartsWith('Validate')){[ordered]@{status='VALIDATED';mode=$Mode;additions=$files.Count;recovery_files=$recoveryFiles.Count;partial_install=$partialInstall;replacements=0;protected_files=$protected.Count}|ConvertTo-Json;return}
New-Item -ItemType Directory -Force $audit|Out-Null
if($Mode -eq 'Install'){
 # Journal before any target mutation allows exact completed copies from a
 # failed additive install to be recovered using the same Rollback operation.
 R5Json $transactionPath ([ordered]@{status='U9_INSTALL_TRANSACTION';game_root=$game;manifest_sha256=R5Hash $mp;installer_sha256=R5Hash $PSCommandPath;helper_pins=$helperPins;files=$files;all_targets_absent=$true})
 $copied=@()
 try{
  foreach($f in $files){
   R5Closed;$target=BoundU9 (Join-Path $game $f.relative) $game
   if(Test-Path -LiteralPath $target){throw 'Addition appeared during install'}
   R5Match (Join-Path $workspace $f.source) $f.sha256
   New-Item -ItemType Directory -Force (Split-Path -Parent $target)|Out-Null
   Copy-Item -LiteralPath (Join-Path $workspace $f.source) -Destination $target
   $copied+=,$f;R5Match $target $f.sha256
   if($FixtureFailAfterCopies -and $copied.Count -eq $FixtureFailAfterCopies){throw 'Injected fixture copy failure'}
  }
  R5Unchanged $protected
  R5Json $rp ([ordered]@{status='INSTALLED_U9_GIG_BATCH_LIVE_PENDING';utc=[DateTime]::UtcNow.ToString('o');game_root=$game;files=$files;manifest_sha256=R5Hash $mp;tests_sha256=R5Hash $tp;installer_sha256=R5Hash $PSCommandPath;helper_pins=$helperPins;protected=$protected;additions=$files.Count;replacements=0;direct_save_writes=0;cache_writes=0;engine_proof=$false})
 }catch{
  R5Json (Join-Path $audit 'partial_install_failure.json') ([ordered]@{error=$_.Exception.Message;copied=$copied;warning='Do not launch. Use this installer ValidateRollback/Rollback to recover exact completed copies. Corrupt/partial copies fail closed for manual review; no file is deleted.'})
  throw
 }
 'INSTALLED_U9_GIG_BATCH_LIVE_PENDING'
}else{
 if(-not $recoverable){
  $recoverable=BoundU9 (Join-Path $audit ('recoverable_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))) $audit
  R5Json $progressPath ([ordered]@{status='U9_ROLLBACK_IN_PROGRESS';game_root=$game;manifest_sha256=R5Hash $mp;installer_sha256=R5Hash $PSCommandPath;helper_pins=$helperPins;recoverable=$recoverable;files=$recoveryFiles;partial_install=$partialInstall})
 }
 $moved=0
 foreach($f in $recoveryFiles){
  R5Closed;$target=BoundU9 (Join-Path $game $f.relative) $game;$dest=BoundU9 (Join-Path $recoverable $f.relative) $recoverable
  if(Test-Path -LiteralPath $dest){if(Test-Path -LiteralPath $target){throw 'Duplicate recovery location'};R5Match $dest $f.sha256;continue}
  R5Match $target $f.sha256
  New-Item -ItemType Directory -Force (Split-Path -Parent $dest)|Out-Null
  Move-Item -LiteralPath $target -Destination $dest
  R5Match $dest $f.sha256;$moved+=1
  if($FixtureFailAfterMoves -and $moved -eq $FixtureFailAfterMoves){throw 'Injected fixture move failure; same Rollback resumes verified locations'}
 }
 R5Unchanged $protected
 R5Json $rollbackPath ([ordered]@{status='U9_FILES_RECOVERED_NOT_WORLD';recoverable=$recoverable;files=$recoveryFiles;partial_install=$partialInstall;warning='Load original pre-U9 baseline. File recovery cannot rewind native quest owners, rewards, fixer credit or a new save.'})
 'U9_FILES_RECOVERED_NOT_WORLD'
}
