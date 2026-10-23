param()
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$fixtureRoot=Join-Path $workspace ('research/pre_alpha_clean/deploy_fixtures/run_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))
$installer=Join-Path $PSScriptRoot 'deploy.ps1'
$results=[Collections.Generic.List[object]]::new()
function WriteFixture([string]$path,[string]$text){New-Item -ItemType Directory -Force (Split-Path -Parent $path)|Out-Null;[IO.File]::WriteAllText($path,$text,[Text.UTF8Encoding]::new($false))}
function Hash([string]$path){(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash}
function SaveManifest($c){[IO.File]::WriteAllText($c.manifest,($c.data|ConvertTo-Json -Depth 20),[Text.UTF8Encoding]::new($false))}
function FilesOf([string]$base){@(Get-ChildItem -LiteralPath $base -File -Recurse -Force | ForEach-Object {[ordered]@{path=[IO.Path]::GetRelativePath($base,$_.FullName).Replace('\','/');sha256=Hash $_.FullName}})}
function Snapshot($c){$a=@();foreach($part in @('game','saves')){$p=$c[$part];foreach($f in Get-ChildItem -LiteralPath $p -Recurse -File -Force){$a+=($part+'/'+[IO.Path]::GetRelativePath($p,$f.FullName).Replace('\','/')+'='+(Hash $f.FullName))}};return (($a|Sort-Object)-join"`n")}
function Assert([bool]$value,[string]$why){if(!$value){throw $why}}
function NewCase([string]$name){
 $root=Join-Path $fixtureRoot $name;$game=Join-Path $root 'game';$saves=Join-Path $root 'saves';$package=Join-Path $root 'package'
 $c=@{name=$name;root=$root;game=$game;saves=$saves;package=$package;manifest=(Join-Path $root 'manifest.json');recovery=(Join-Path $root 'recovery')}
 foreach($x in @('archive/pc/mod/TowerContinued_Old.archive','r6/scripts/PTFR_Old/old.reds','bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_Old/init.lua','r6/tweaks/TowerContinued_Old.yaml','r6/scripts/EquipmentEx/preserve.reds')){WriteFixture (Join-Path $game $x) ('original '+$x)}
 foreach($x in @('ManualSave-10','ManualSave-17','AutoSave-1')){WriteFixture (Join-Path $saves ($x+'/sav.dat')) ('original save '+$x);WriteFixture (Join-Path $saves ($x+'/metadata.9.json')) ('meta '+$x)}
 $paths=@('archive/pc/mod/TowerContinued_PreAlpha.archive','archive/pc/mod/TowerContinued_PreAlpha.archive.xl','r6/scripts/PTFR_PreAlpha/main.reds','r6/tweaks/TowerContinued_PreAlpha.yaml','bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_PreAlpha/init.lua')
 $packageRows=@();foreach($x in $paths){WriteFixture (Join-Path $package $x) ('package '+$x);$packageRows+=@{relative=$x;sha256=Hash (Join-Path $package $x)}}
 $units=@();foreach($x in @('archive/pc/mod/TowerContinued_Old.archive','r6/scripts/PTFR_Old','bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_Old','r6/tweaks/TowerContinued_Old.yaml')){$p=Join-Path $game $x;$files=if(Test-Path -LiteralPath $p -PathType Leaf){,@{path='.';sha256=Hash $p}}else{@(FilesOf $p)};$units+=@{kind='game';relative=$x;files=@($files)}}
 foreach($x in @('ManualSave-17','AutoSave-1')){$units+=@{kind='save';relative=$x;files=@(FilesOf (Join-Path $saves $x))}}
 $protected=@(@{kind='game';relative='r6/scripts/EquipmentEx/preserve.reds';sha256=Hash (Join-Path $game 'r6/scripts/EquipmentEx/preserve.reds')})
 foreach($f in FilesOf (Join-Path $saves 'ManualSave-10')){$protected+=@{kind='save';relative=('ManualSave-10/'+$f.path);sha256=$f.sha256}}
 $c.data=@{status='PREALPHA_PACKAGE_VERIFIED';package_root=$package;keep_save='ManualSave-10';package=$packageRows;units=$units;protected=$protected};SaveManifest $c;$c.before=Snapshot $c;return $c
}
function RunInstaller($c,[string]$mode='Install',[int]$failMove=0,[int]$failPackage=0){
 & $installer -ManifestPath $c.manifest -Mode $mode -GameRoot $c.game -SaveRoot $c.saves -RecoveryRoot $c.recovery -Fixture -FailAfterMove $failMove -FailAfterPackage $failPackage | Out-Null
}
function ExpectRefusal($c,[string]$mode='Install',[string]$pattern='',[bool]$unchanged=$true){
 $before=Snapshot $c;$caught=$null
 try{RunInstaller $c $mode}catch{$caught=$_.Exception.Message}
 Assert ($null -ne $caught) ($c.name+' unexpectedly accepted')
 if($pattern){Assert ($caught -match $pattern) ($c.name+' wrong refusal: '+$caught)}
 if($unchanged){Assert ((Snapshot $c) -ceq $before) ($c.name+' modified files on refused operation')}
 return $caught
}
function Record([string]$name,[scriptblock]$body){
 try{$detail=& $body;$results.Add(@{name=$name;status='PASS';detail=$detail})}
 catch{$results.Add(@{name=$name;status='FAIL';error=$_.Exception.Message});throw}
}
try{
 Record 'normal_install_restore' {
  $c=NewCase 'normal';RunInstaller $c 'Validate';Assert ((Snapshot $c) -ceq $c.before) 'Validate mutated original files';RunInstaller $c
  Assert (Test-Path -LiteralPath (Join-Path $c.recovery 'retained_source/ManualSave-10/sav.dat')) 'retained source backup absent'
  Assert (!(Test-Path -LiteralPath (Join-Path $c.saves 'ManualSave-17'))) 'old save remained active'
  Assert ((Hash (Join-Path $c.saves 'ManualSave-10/sav.dat')) -ceq (Hash (Join-Path $c.recovery 'retained_source/ManualSave-10/sav.dat'))) 'kept save changed'
  RunInstaller $c 'Restore';Assert ((Snapshot $c) -ceq $c.before) 'normal restore did not restore original files';'All original game/save file hashes restored; selected save backup identical.'
 }
 Record 'partial_cleanup_restore' {
  $c=NewCase 'partial_cleanup';$caught=$null;try{RunInstaller $c 'Install' 2}catch{$caught=$_.Exception.Message};Assert ($caught -match 'Injected fixture failure') 'No cleanup injection';RunInstaller $c 'Restore';Assert ((Snapshot $c) -ceq $c.before) 'partial cleanup restore mismatch';'Restored after two moved units.'
 }
 Record 'partial_package_restore' {
  $c=NewCase 'partial_package';$caught=$null;try{RunInstaller $c 'Install' 0 2}catch{$caught=$_.Exception.Message};Assert ($caught -match 'Injected fixture package failure') 'No package injection';RunInstaller $c 'Restore';Assert ((Snapshot $c) -ceq $c.before) 'partial package restore mismatch';'Restored after all old units moved and two package files installed.'
 }
 Record 'cleanup_hash_drift' {$c=NewCase 'cleanup_drift';WriteFixture (Join-Path $c.game 'r6/scripts/PTFR_Old/old.reds') 'changed user original';ExpectRefusal $c 'Install' 'File drift'}
 Record 'package_source_hash_drift' {$c=NewCase 'package_drift';WriteFixture (Join-Path $c.package $c.data.package[0].relative) 'bad package';ExpectRefusal $c 'Install' 'File drift'}
 Record 'protected_hash_drift' {$c=NewCase 'protected_drift';WriteFixture (Join-Path $c.game 'r6/scripts/EquipmentEx/preserve.reds') 'changed external mod';ExpectRefusal $c 'Install' 'File drift'}
 Record 'package_target_exists' {$c=NewCase 'target_exists';WriteFixture (Join-Path $c.game $c.data.package[0].relative) 'unrelated existing file';ExpectRefusal $c 'Install' 'Package already exists'}
 Record 'package_dot_segment_escape' {$c=NewCase 'package_escape';$c.data.package[2].relative='r6/scripts/PTFR_PreAlpha/../EquipmentEx/preserve.reds';SaveManifest $c;ExpectRefusal $c 'Install' 'Invalid path segment'}
 Record 'cleanup_path_escape' {$c=NewCase 'cleanup_escape';$c.data.units[0].relative='../outside.archive';SaveManifest $c;ExpectRefusal $c 'Install' 'Invalid path segment'}
 Record 'unrelated_cleanup_scope' {$c=NewCase 'unrelated_cleanup';$c.data.units[1].relative='r6/scripts/EquipmentEx';SaveManifest $c;ExpectRefusal $c 'Install' 'Cleanup outside project files'}
 Record 'retained_save_cleanup_forbidden' {$c=NewCase 'retained_save';$c.data.units[4].relative='ManualSave-10';SaveManifest $c;ExpectRefusal $c 'Install' 'Invalid save cleanup target'}
 Record 'duplicate_package_target' {$c=NewCase 'package_duplicate';$c.data.package+=@($c.data.package[0]);SaveManifest $c;ExpectRefusal $c 'Install' 'Duplicate package target'}
 Record 'duplicate_unit_file' {$c=NewCase 'duplicate_unit';$p=Join-Path $c.game 'r6/scripts/PTFR_Old/second.reds';WriteFixture $p 'second';$c.data.units[1].files+=@($c.data.units[1].files[0]);SaveManifest $c;ExpectRefusal $c 'Install' 'Duplicate unit file'}
 Record 'unplanned_save_refusal' {$c=NewCase 'unplanned_save';WriteFixture (Join-Path $c.saves 'ManualSave-88/sav.dat') 'user new save';ExpectRefusal $c 'Install' 'Active save set differs'}
 Record 'restore_changed_package_refusal' {$c=NewCase 'restore_package_drift';RunInstaller $c;WriteFixture (Join-Path $c.game $c.data.package[0].relative) 'user edited package';ExpectRefusal $c 'Restore' 'File drift'}
 Record 'restore_new_save_conflict' {$c=NewCase 'restore_save_conflict';RunInstaller $c;WriteFixture (Join-Path $c.saves 'ManualSave-17/sav.dat') 'NEW USER SAVE DO NOT OVERWRITE';ExpectRefusal $c 'Restore' 'Recovery conflict'}
 Record 'restore_changed_backup_refusal' {$c=NewCase 'restore_backup_drift';RunInstaller $c;WriteFixture (Join-Path $c.recovery 'save/ManualSave-17/sav.dat') 'changed backup';ExpectRefusal $c 'Restore' 'File drift'}
 Record 'restore_extra_backup_file_refusal' {$c=NewCase 'restore_backup_extra';RunInstaller $c;WriteFixture (Join-Path $c.recovery 'save/ManualSave-17/extra.txt') 'unexpected';ExpectRefusal $c 'Restore' 'Unit contents changed'}
 Record 'restore_package_destination_conflict' {$c=NewCase 'restore_removed_conflict';RunInstaller $c;WriteFixture (Join-Path $c.recovery ('removed_package/'+$c.data.package[0].relative)) 'existing recovery file';ExpectRefusal $c 'Restore' 'Recovery package destination conflict'}
 Record 'restore_tampered_transaction_refusal' {$c=NewCase 'restore_txn';RunInstaller $c;[IO.File]::AppendAllText((Join-Path $c.recovery 'transaction.json'),' ');ExpectRefusal $c 'Restore' 'File drift'}
 Record 'nested_cleanup_reparse_refusal' {
  $c=NewCase 'cleanup_junction';$external=Join-Path $c.root 'external';New-Item -ItemType Directory $external|Out-Null;WriteFixture (Join-Path $external 'precious.txt') 'preserve outside tree'
  New-Item -ItemType Junction -Path (Join-Path $c.game 'r6/scripts/PTFR_Old/link') -Target $external|Out-Null
  ExpectRefusal $c 'Install' 'Nested reparse'
 }
 Record 'nested_retained_save_reparse_refusal' {
  $c=NewCase 'save_junction';$external=Join-Path $c.root 'external';New-Item -ItemType Directory $external|Out-Null
  New-Item -ItemType Junction -Path (Join-Path $c.saves 'ManualSave-10/link') -Target $external|Out-Null
  ExpectRefusal $c 'Install' 'Nested reparse'
 }
 Record 'recovery_reparse_refusal' {
  $c=NewCase 'recovery_junction';$external=Join-Path $c.root 'external';New-Item -ItemType Directory $external|Out-Null
  New-Item -ItemType Junction -Path $c.recovery -Target $external|Out-Null
  ExpectRefusal $c 'Install' 'Reparse path'
 }
 Record 'restore_preserves_new_unrelated_save' {
  $c=NewCase 'new_unrelated_save';RunInstaller $c;WriteFixture (Join-Path $c.saves 'ManualSave-77/sav.dat') 'new user save';$newHash=Hash (Join-Path $c.saves 'ManualSave-77/sav.dat');RunInstaller $c 'Restore';Assert ((Hash (Join-Path $c.saves 'ManualSave-77/sav.dat')) -ceq $newHash) 'new unrelated save overwritten';'New save with different slot survives recovery.'
 }
}finally{
 $report=@{status=if(@($results|Where-Object {$_.status -eq 'FAIL'}).Count){'FAIL'}else{'PASS'};utc=[DateTime]::UtcNow.ToString('o');installer_sha256=Hash $installer;fixture_root=$fixtureRoot;tests=$results.ToArray();game_save_writes=$false;fixture_only=$true}
 $p=Join-Path $workspace 'research/pre_alpha_clean/deploy_fixtures/tests.json';WriteFixture $p ($report|ConvertTo-Json -Depth 10)
 $report|Select-Object status,installer_sha256,fixture_root,@{n='tests';e={$_.tests.Count}}|ConvertTo-Json
}
