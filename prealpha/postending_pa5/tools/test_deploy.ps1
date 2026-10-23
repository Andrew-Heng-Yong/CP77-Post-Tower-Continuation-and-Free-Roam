param([string]$Output='')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..')).TrimEnd('\')
$fixtureBase=Join-Path $workspace 'research/postending_pa5/fixtures'
$run=Join-Path $fixtureBase ([DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))
if(Test-Path -LiteralPath $run){throw 'Fixture run already exists'}
New-Item -ItemType Directory -Path $run -Force|Out-Null
$installer=Join-Path $PSScriptRoot 'deploy.ps1'
$pwsh=(Get-Process -Id $PID).Path
$baseline=Get-Content -LiteralPath (Join-Path $workspace 'prealpha/camera_pa4/build/pa4_02/build.json') -Raw|ConvertFrom-Json
. (Join-Path $PSScriptRoot 'scope.ps1')
$results=[Collections.Generic.List[object]]::new()
function WriteText([string]$path,[string]$content){New-Item -ItemType Directory -Force (Split-Path -Parent $path)|Out-Null;[IO.File]::WriteAllText($path,$content,[Text.UTF8Encoding]::new($false))}
function WriteJson([string]$path,$value){WriteText $path ($value|ConvertTo-Json -Depth 30)}
function Hash([string]$path){(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash}
function NewCase([string]$name){
 $caseRoot=Join-Path $run $name;New-Item -ItemType Directory -Path $caseRoot|Out-Null
 $c=@{name=$name;root=$caseRoot;game=(Join-Path $caseRoot 'game');saves=(Join-Path $caseRoot 'saves');build=(Join-Path $caseRoot 'build');recovery=(Join-Path $caseRoot 'recovery');baseline=(Join-Path $caseRoot 'baseline.json')}
 $old=@();$new=@();$changes=@()
 foreach($f in $baseline.package_files){
  $oldText='BASELINE FIXTURE '+$f.relative;$newText=if($f.relative -cin $allowed){'UPGRADE FIXTURE '+$f.relative}else{$oldText}
  $target=Join-Path $c.game $f.relative;$source=Join-Path $c.build ('package/'+$f.relative)
  WriteText $target $oldText;WriteText $source $newText
  $before=Hash $target;$after=Hash $source
  $old+=@{relative=$f.relative;sha256=$before};$new+=@{relative=$f.relative;sha256=$after}
  if($f.relative -cin $allowed){$changes+=@{relative=$f.relative;old_sha256=$before;new_sha256=$after;kind='replace'}}
 }
 foreach($rel in $addPaths){
  $source=Join-Path $c.build ('package/'+$rel);WriteText $source ('ADDITION FIXTURE '+$rel);$sha=Hash $source
  $new+=@{relative=$rel;sha256=$sha};$changes+=@{relative=$rel;old_sha256=$null;new_sha256=$sha;kind='add'}
 }
 WriteText (Join-Path $c.saves 'ManualSave-10/sav.dat') 'PROTECTED SAVE CONTENT'
 WriteText (Join-Path $c.game 'red4ext/plugins/EquipmentEx/EquipmentEx.dll') 'PROTECTED FRAMEWORK'
 WriteText (Join-Path $c.game 'archive/pc/mod/unrelated.archive') 'PROTECTED MOD'
 WriteText (Join-Path $c.game 'r6/cache/final.redscripts') 'CACHE NOT TOUCHED'
 WriteJson $c.baseline @{package_files=$old}
 WriteJson (Join-Path $c.build 'build.json') @{status='FIXTURE_BUILT';package_root=(Join-Path $c.build 'package');package_files=$new;changes=$changes}
 $buildHash=Hash (Join-Path $c.build 'build.json')
 WriteJson (Join-Path $c.build 'compile.json') @{status='PASS_COMPILE_AND_READBACK_NOT_LIVE';build_sha256=$buildHash}
 WriteJson (Join-Path $c.build 'tests.json') @{status='PASS_NOT_LIVE';build_sha256=$buildHash;compile_sha256=Hash (Join-Path $c.build 'compile.json')}
 $c.old=$old;$c.new=$new
 return $c
}
function InvokeCase($c,[string]$mode,[bool]$success,[string[]]$extra=@(),[string]$reason=''){
 $arguments=@('-NoLogo','-NoProfile','-File',$installer,'-Mode',$mode,'-Fixture','-GameRoot',$c.game,'-SaveRoot',$c.saves,'-BaselineBuild',$c.baseline,'-Build',$c.build,'-RecoveryRoot',$c.recovery)+$extra
 $output=@(& $pwsh @arguments 2>&1);$exit=$LASTEXITCODE
 $text=($output|Out-String)
 WriteText (Join-Path $c.root ($mode+'_'+$results.Count+'.log')) $text
 if(($success -and $exit -ne 0) -or (!$success -and $exit -eq 0)){throw "Unexpected result $($c.name)/${mode}: $text"}
 if(!$success -and $reason -and $text -notmatch [regex]::Escape($reason)){throw "Wrong refusal $($c.name)/${mode}: $text"}
 $results.Add(@{name=$c.name;mode=$mode;expected_success=$success;exit=$exit;result='PASS'})
}
function Unchanged($c,$files){foreach($f in $files){if((Hash (Join-Path $c.game $f.relative)) -cne $f.sha256){throw "Fixture file mismatch: $($f.relative)"}}}
function Protected($c){
 foreach($pair in @(@((Join-Path $c.saves 'ManualSave-10/sav.dat'),'PROTECTED SAVE CONTENT'),@((Join-Path $c.game 'red4ext/plugins/EquipmentEx/EquipmentEx.dll'),'PROTECTED FRAMEWORK'),@((Join-Path $c.game 'archive/pc/mod/unrelated.archive'),'PROTECTED MOD'),@((Join-Path $c.game 'r6/cache/final.redscripts'),'CACHE NOT TOUCHED'))){if((Get-Content -LiteralPath $pair[0] -Raw) -cne $pair[1]){throw 'Protected fixture modified'}}
}
function MutateReport($c,[scriptblock]$change){$m=Get-Content -LiteralPath (Join-Path $c.build 'build.json') -Raw|ConvertFrom-Json;& $change $m;WriteJson (Join-Path $c.build 'build.json') $m;$hash=Hash (Join-Path $c.build 'build.json');foreach($name in @('compile.json','tests.json')){$r=Get-Content -LiteralPath (Join-Path $c.build $name) -Raw|ConvertFrom-Json;$r.build_sha256=$hash;if($name -ceq 'tests.json'){$r.compile_sha256=Hash (Join-Path $c.build 'compile.json')};WriteJson (Join-Path $c.build $name) $r}}

$c=NewCase 'normal_upgrade_rollback'
InvokeCase $c Validate $true
InvokeCase $c Install $true
Unchanged $c $c.new;Protected $c
InvokeCase $c ValidateRollback $true
InvokeCase $c Rollback $true
Unchanged $c $c.old;Protected $c
InvokeCase $c Rollback $false @() 'already been rolled back'

$c=NewCase 'addition_collision'
WriteText (Join-Path $c.game $addPaths[0]) 'USER ARCHIVE'
InvokeCase $c Validate $false @() 'Addition target already exists'

$c=NewCase 'baseline_target_drift'
WriteText (Join-Path $c.game $allowed[0]) 'USER EDIT'
InvokeCase $c Validate $false @() 'File drift'

$c=NewCase 'unchanged_baseline_drift'
$f=@($c.old|Where-Object {$_.relative -cnotin $allowed})[0]
WriteText (Join-Path $c.game $f.relative) 'USER EDIT'
InvokeCase $c Validate $false @() 'File drift'

$c=NewCase 'package_source_drift'
WriteText (Join-Path $c.build ('package/'+$allowed[0])) 'BAD SOURCE'
InvokeCase $c Validate $false @() 'File drift'

$c=NewCase 'compile_required'
WriteJson (Join-Path $c.build 'compile.json') @{status='PENDING'}
InvokeCase $c Validate $false @() 'PASS reports required'

$c=NewCase 'tests_required'
WriteJson (Join-Path $c.build 'tests.json') @{status='PENDING'}
InvokeCase $c Validate $false @() 'PASS reports required'

$c=NewCase 'compile_build_binding'
WriteJson (Join-Path $c.build 'compile.json') @{status='PASS_COMPILE_AND_READBACK_NOT_LIVE';build_sha256=('A'*64)}
InvokeCase $c Validate $false @() 'Verification reports do not match build'

$c=NewCase 'tests_build_binding'
WriteJson (Join-Path $c.build 'tests.json') @{status='PASS_NOT_LIVE';build_sha256=('A'*64)}
InvokeCase $c Validate $false @() 'Verification reports do not match build'

$c=NewCase 'archive_change_refused'
MutateReport $c {param($m);$m.changes[0].relative='archive/pc/mod/TowerContinued_PreAlpha.archive'}
InvokeCase $c Validate $false @() 'outside approved scope'

$c=NewCase 'compile_report_changed_after_tests'
WriteJson (Join-Path $c.build 'compile.json') @{status='PASS_COMPILE_AND_READBACK_NOT_LIVE';build_sha256=Hash (Join-Path $c.build 'build.json');changed='report'}
InvokeCase $c Validate $false @() 'Tests do not match compile report'

$c=NewCase 'out_of_scope_change'
MutateReport $c {param($m);$m.changes[0].relative='r6/cache/final.redscripts'}
InvokeCase $c Validate $false @() 'outside approved scope'

$c=NewCase 'duplicate_change'
MutateReport $c {param($m);$m.changes[1]=$m.changes[0]}
InvokeCase $c Validate $false @() 'duplicate'

$c=NewCase 'old_hash_mismatch'
MutateReport $c {param($m);$m.changes[0].old_sha256=('A'*64)}
InvokeCase $c Validate $false @() 'Change hash mismatch'

$c=NewCase 'package_path_traversal'
MutateReport $c {param($m);$m.package_files[0].relative='../escape.archive'}
InvokeCase $c Validate $false @() 'Invalid path segment'

$c=NewCase 'package_duplicate'
MutateReport $c {param($m);$m.package_files[1]=$m.package_files[0]}
InvokeCase $c Validate $false @() 'Duplicate package path'

$c=NewCase 'package_extra_file'
WriteText (Join-Path $c.build 'package/unlisted.txt') 'EXTRA'
InvokeCase $c Validate $false @() 'unexpected files'

$c=NewCase 'change_count'
MutateReport $c {param($m);$m.changes=@($m.changes|Select-Object -First 1)}
InvokeCase $c Validate $false @() 'Exactly nine'

$c=NewCase 'unchanged_source_modified'
MutateReport $c {param($m);$f=@($m.package_files|Where-Object {$_.relative -cnotin $allowed})[0];$f.sha256=('A'*64)}
InvokeCase $c Validate $false @() 'Out-of-scope package modification'

$c=NewCase 'recovery_conflict'
New-Item -ItemType Directory -Path $c.recovery|Out-Null
InvokeCase $c Install $false @() 'already exists'
Unchanged $c $c.old;Protected $c

$c=NewCase 'fixture_root_escape'
$original=$c.game;$c.game=Join-Path $workspace 'prealpha'
InvokeCase $c Validate $false @() 'Path outside scope'
$c.game=$original

$c=NewCase 'package_root_escape'
MutateReport $c {param($m);$m.package_root=Join-Path $c.root 'other_package'}
InvokeCase $c Validate $false @() 'Path outside scope'

$c=NewCase 'target_reparse'
$original=Join-Path $c.game 'r6/scripts/PTFR_PreAlpha/PA1'
$held=Join-Path $c.root 'held_original_PA1'
[IO.Directory]::Move($original,$held)
New-Item -ItemType Junction -Path $original -Target $held|Out-Null
InvokeCase $c Validate $false @() 'Reparse path refused'

$c=NewCase 'protected_reparse'
$external=Join-Path $c.root 'outside_framework';New-Item -ItemType Directory -Path $external|Out-Null
New-Item -ItemType Junction -Path (Join-Path $c.game 'red4ext/plugins/linked') -Target $external|Out-Null
InvokeCase $c Validate $false @() 'Reparse path refused'

$c=NewCase 'save_root_reparse'
$saveHeld=Join-Path $c.root 'held_saves';[IO.Directory]::Move($c.saves,$saveHeld)
New-Item -ItemType Junction -Path $c.saves -Target $saveHeld|Out-Null
InvokeCase $c Validate $false @() 'Reparse path refused'

$c=NewCase 'legitimate_framework_log_link'
$logDir=Join-Path $c.game 'red4ext/plugins/EquipmentEx'
WriteText (Join-Path $logDir 'EquipmentEx-2026.log') 'PROTECTED ROLLING LOG'
New-Item -ItemType SymbolicLink -Path (Join-Path $logDir 'EquipmentEx.log') -Target 'EquipmentEx-2026.log'|Out-Null
InvokeCase $c Validate $true
InvokeCase $c Install $true
InvokeCase $c Rollback $true
if((Get-Item -LiteralPath (Join-Path $logDir 'EquipmentEx.log')).LinkTarget -cne 'EquipmentEx-2026.log'){throw 'Framework log link was modified'}
if((Get-Content -LiteralPath (Join-Path $logDir 'EquipmentEx-2026.log') -Raw) -cne 'PROTECTED ROLLING LOG'){throw 'Framework log target was modified'}
Unchanged $c $c.old;Protected $c

$c=NewCase 'escaping_framework_log_link'
$logDir=Join-Path $c.game 'red4ext/plugins/EquipmentEx'
WriteText (Join-Path $c.game 'red4ext/plugins/outside.log') 'OUTSIDE LOG'
New-Item -ItemType SymbolicLink -Path (Join-Path $logDir 'EquipmentEx.log') -Target '../outside.log'|Out-Null
InvokeCase $c Validate $false @() 'Invalid relative path'

$c=NewCase 'absolute_framework_log_link'
$logDir=Join-Path $c.game 'red4ext/plugins/EquipmentEx'
$outsideLog=Join-Path $c.root 'outside.log';WriteText $outsideLog 'OUTSIDE LOG'
New-Item -ItemType SymbolicLink -Path (Join-Path $logDir 'EquipmentEx.log') -Target $outsideLog|Out-Null
InvokeCase $c Validate $false @() 'Invalid relative path'

$c=NewCase 'framework_link_to_link'
$logDir=Join-Path $c.game 'red4ext/plugins/EquipmentEx'
WriteText (Join-Path $logDir 'regular.log') 'LOG'
New-Item -ItemType SymbolicLink -Path (Join-Path $logDir 'indirect.log') -Target 'regular.log'|Out-Null
New-Item -ItemType SymbolicLink -Path (Join-Path $logDir 'EquipmentEx.log') -Target 'indirect.log'|Out-Null
InvokeCase $c Validate $false @() 'Reparse path refused'

$c=NewCase 'non_log_framework_link'
$logDir=Join-Path $c.game 'red4ext/plugins/EquipmentEx'
WriteText (Join-Path $logDir 'regular.txt') 'TEXT'
New-Item -ItemType SymbolicLink -Path (Join-Path $logDir 'indirect.txt') -Target 'regular.txt'|Out-Null
InvokeCase $c Validate $false @() 'Reparse path refused'

$c=NewCase 'cache_reparse_refused'
$heldCache=Join-Path $c.root 'held_cache';[IO.Directory]::Move((Join-Path $c.game 'r6/cache'),$heldCache)
New-Item -ItemType Junction -Path (Join-Path $c.game 'r6/cache') -Target $heldCache|Out-Null
InvokeCase $c Validate $false @() 'Reparse path refused'

foreach($n in 1..4){
 $c=NewCase ('backup_failure_'+$n)
 InvokeCase $c Install $false @('-FailAfterBackup',[string]$n) 'Injected fixture backup failure'
 Unchanged $c $c.old;Protected $c
 InvokeCase $c ValidateRollback $true
 InvokeCase $c Rollback $true
 Unchanged $c $c.old;Protected $c
}
foreach($n in 1..9){
 $c=NewCase ('replacement_failure_'+$n)
 InvokeCase $c Install $false @('-FailAfterReplace',[string]$n) 'Injected fixture replacement failure'
 Protected $c
 InvokeCase $c ValidateRollback $true
 InvokeCase $c Rollback $true
 Unchanged $c $c.old;Protected $c
}

$c=NewCase 'missing_target_interrupted_move'
InvokeCase $c Install $false @('-FailAfterReplace','1') 'Injected fixture replacement failure'
$target=Join-Path $c.game $allowed[1];$moved=Join-Path $c.recovery ('displaced/'+$allowed[1]);New-Item -ItemType Directory -Force (Split-Path -Parent $moved)|Out-Null;[IO.File]::Move($target,$moved,$false)
InvokeCase $c ValidateRollback $true
InvokeCase $c Rollback $true
Unchanged $c $c.old;Protected $c

$c=NewCase 'rollback_added_file_drift'
InvokeCase $c Install $true
WriteText (Join-Path $c.game $addPaths[0]) 'USER POSTINSTALL EDIT'
InvokeCase $c ValidateRollback $false @() 'File drift'

$c=NewCase 'rollback_interrupted_partial_copy'
InvokeCase $c Install $true
$partial=Join-Path $c.recovery ('restoring/'+$replacePaths[0]+'.pa5-copying')
WriteText $partial 'INTERRUPTED PARTIAL BYTES'
InvokeCase $c ValidateRollback $true
InvokeCase $c Rollback $true
Unchanged $c $c.old;Protected $c
$held=@(Get-ChildItem -LiteralPath (Split-Path -Parent $partial) -Filter '*.pa5-copying.interrupted-*' -File)
if($held.Count -ne 1 -or (Get-Content -LiteralPath $held[0].FullName -Raw) -cne 'INTERRUPTED PARTIAL BYTES'){throw 'Interrupted copy not recoverably retained'}

$c=NewCase 'backup_interrupted_partial_copy'
InvokeCase $c Install $false @('-FailAfterBackup','1') 'Injected fixture backup failure'
$partial=Join-Path $c.recovery ('original/'+$replacePaths[1]+'.pa5-copying')
WriteText $partial 'PARTIAL BACKUP'
InvokeCase $c ValidateRollback $true
InvokeCase $c Rollback $true
Unchanged $c $c.old;Protected $c
if((Get-Content -LiteralPath $partial -Raw) -cne 'PARTIAL BACKUP'){throw 'Partial backup was not preserved'}

$c=NewCase 'rollback_verified_stage_before_atomic_move'
InvokeCase $c Install $true
$rel=$replacePaths[0];$target=Join-Path $c.game $rel;$removed=Join-Path $c.recovery ('rolled_back/'+$rel)
New-Item -ItemType Directory -Force (Split-Path -Parent $removed)|Out-Null
[IO.File]::Move($target,$removed,$false)
$stage=Join-Path $c.recovery ('restoring/'+$rel)
New-Item -ItemType Directory -Force (Split-Path -Parent $stage)|Out-Null
[IO.File]::Copy((Join-Path $c.recovery ('original/'+$rel)),$stage,$false)
InvokeCase $c ValidateRollback $true
InvokeCase $c Rollback $true
Unchanged $c $c.old;Protected $c

$c=NewCase 'rollback_installed_drift'
InvokeCase $c Install $true
WriteText (Join-Path $c.game $allowed[0]) 'USER POSTINSTALL EDIT'
InvokeCase $c ValidateRollback $false @() 'Installed target drift'

$c=NewCase 'rollback_backup_drift'
InvokeCase $c Install $true
WriteText (Join-Path $c.recovery ('original/'+$allowed[0])) 'BACKUP EDIT'
InvokeCase $c ValidateRollback $false @() 'File drift'

$c=NewCase 'rollback_transaction_drift'
InvokeCase $c Install $true
WriteText (Join-Path $c.recovery 'transaction.json') '{}'
InvokeCase $c ValidateRollback $false @() 'File drift'

$c=NewCase 'rollback_new_save_preserved'
InvokeCase $c Install $true
WriteText (Join-Path $c.saves 'ManualSave-11/sav.dat') 'NEW USER SAVE'
InvokeCase $c Rollback $true
if((Get-Content -LiteralPath (Join-Path $c.saves 'ManualSave-11/sav.dat') -Raw) -cne 'NEW USER SAVE'){throw 'New save was not preserved'}
Unchanged $c $c.old;Protected $c

$report=@{status='PASS_DEPLOYMENT_FIXTURES_NOT_LIVE';utc=[DateTime]::UtcNow.ToString('o');fixture_root=$run;installer_sha256=Hash $installer;checks=$results.Count;cases=@(Get-ChildItem -LiteralPath $run -Directory).Count;results=@($results.ToArray());live_install_performed=$false;fixture_junctions_retained=$true}
WriteJson (Join-Path $run 'deployment_tests.json') $report
if($Output){
 $resolved=[IO.Path]::GetFullPath($Output)
 if(!$resolved.StartsWith((Join-Path $workspace 'research/postending_pa5')+'\',[StringComparison]::OrdinalIgnoreCase) -and !$resolved.StartsWith((Join-Path $workspace 'prealpha/postending_pa5/build')+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Output outside scoped report directories'}
 $cursor=$resolved
 while($cursor){if(Test-Path -LiteralPath $cursor){if(((Get-Item -LiteralPath $cursor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw 'Reparse report output refused'}};$next=Split-Path -Parent $cursor;if($next -eq $cursor){break};$cursor=$next}
 WriteJson $resolved $report
}
@{status=$report.status;checks=$report.checks;cases=$report.cases;report=(Join-Path $run 'deployment_tests.json')}|ConvertTo-Json
