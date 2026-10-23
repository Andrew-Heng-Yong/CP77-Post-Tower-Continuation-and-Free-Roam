param(
 [string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),
 [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
 [string]$AuditDirectory='',
 [ValidateSet('ValidateInstall','Install','ValidateRollback','Rollback')][string]$Mode='ValidateInstall'
)
. (Join-Path $PSScriptRoot 'gig_family_b7_1_xl.ps1')
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\')
$root=Join-Path $workspace 'research\gig_restoration\family_b7_1'
$game=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
$actual='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$fixture=$game.StartsWith($root+'\fixture_',[StringComparison]::OrdinalIgnoreCase)
if($game -ne $actual -and -not $fixture){throw 'Unsupported game root'}
$audit=if($AuditDirectory){R5Within $AuditDirectory $workspace}else{$root}
if($fixture -and (-not $AuditDirectory -or -not $audit.StartsWith((Split-Path -Parent $game)+'\',[StringComparison]::OrdinalIgnoreCase))){throw 'Fixture audit mismatch'}
if(-not $fixture -and $AuditDirectory){throw 'Actual audit must be canonical'}
R5Closed
$testPath=Join-Path $root 'tests.json'
$t=Get-Content -LiteralPath $testPath -Raw|ConvertFrom-Json
if($t.status -ne 'PASS_B7_1_YAML_REGRESSION_ENGINE_PENDING' -or -not $t.configuration_only -or -not $t.legacy_parser_rejected -or @($t.files).Count -ne 1 -or @($t.other_b7_files).Count -ne 5 -or @($t.refused_mutants).Count -ne 11){throw 'B7.1 checks missing'}
$f=$t.files[0]
if($f.source -ne 'build/GigFamilyB7_1/TowerContinued_FamilyB7.archive.xl' -or $f.relative -ne 'archive/pc/mod/TowerContinued_FamilyB7.archive.xl' -or $f.predecessor -ne '58DC55116DD316975EC1EE48C56F80FAA55B2D7268327F39775EFDAF0A26259F'){throw 'Mapping mismatch'}
$target=R5Within (Join-Path $game $f.relative) $game
$source=R5Within (Join-Path $workspace $f.source) $workspace
R5Match $source $f.sha256
foreach($p in @($t.tools.PSObject.Properties)+@($t.pinned_predecessor_evidence.PSObject.Properties)){R5Match (R5Within (Join-Path $workspace $p.Name) $workspace) $p.Value}
$parser=B71Parser
if($parser -ne $t.parser_path){throw 'Parser path mismatch'}
R5Match $parser $t.parser_sha256
$manifest=B71Manifest $workspace
B71Validate (Get-Content -LiteralPath $source -Raw) $manifest|Out-Null
$protected=R5Snapshot $game @($target)
if(-not $fixture){
 $d=Get-Content -LiteralPath (Join-Path $root 'deployment_tests.json') -Raw|ConvertFrom-Json
 if($d.status -ne 'PASS_B7_1_RECOVERABLE_FIXTURE' -or -not $d.recoverable_rollback -or $d.tests_sha256 -ne (R5Hash $testPath) -or $d.installer_sha256 -ne (R5Hash $PSCommandPath)){throw 'Current fixture missing'}
 foreach($unchanged in $t.other_b7_files){
  $p=R5Within (Join-Path $game $unchanged.relative) $game
  R5Match $p $unchanged.sha256;$protected[$p]=$unchanged.sha256
 }
 foreach($folder in @('archive/pc/mod','red4ext/plugins','r6/scripts','r6/cache')){
  foreach($p in Get-ChildItem -LiteralPath (Join-Path $game $folder) -Recurse -File){if($p.FullName -ne $target -and ($folder -eq 'r6/cache' -or $p.Extension -in @('.archive','.xl','.reds','.dll'))){$protected[$p.FullName]=R5Hash $p.FullName}}
 }
}
$receiptPath=Join-Path $audit 'install_receipt.json'
$backup=R5Within (Join-Path (Join-Path $audit 'backup') $f.relative) $audit
if($Mode -in @('ValidateRollback','Rollback')){
 $r=Get-Content -LiteralPath $receiptPath -Raw|ConvertFrom-Json
 if($r.status -ne 'INSTALLED_B7_1_YAML_FIX_ENGINE_PENDING' -or $r.game_root -ne $game -or $r.tests_sha256 -ne (R5Hash $testPath) -or $r.installer_sha256 -ne (R5Hash $PSCommandPath) -or @($r.files).Count -ne 1){throw 'Receipt mismatch'}
 $rf=$r.files[0]
 if($rf.source -ne $f.source -or $rf.relative -ne $f.relative -or $rf.sha256 -ne $f.sha256 -or $rf.predecessor -ne $f.predecessor){throw 'Receipt mapping mismatch'}
 R5Match $target $f.sha256;R5Match $backup $f.predecessor
 if(Test-Path -LiteralPath (Join-Path $audit 'rollback_receipt.json')){throw 'Already recovered'}
}else{
 if(Test-Path -LiteralPath $receiptPath){throw 'Existing receipt; refuse reinstall'}
 R5Match $target $f.predecessor
}
R5Closed
if($Mode.StartsWith('Validate')){[ordered]@{status='VALIDATED';mode=$Mode;replacements=1;protected_files=$protected.Count;parsed_phases=76}|ConvertTo-Json;return}
New-Item -ItemType Directory -Force $audit|Out-Null;R5Closed
if($Mode -eq 'Install'){
 if(Test-Path -LiteralPath $backup){throw 'Backup exists'}
 New-Item -ItemType Directory -Force (Split-Path -Parent $backup)|Out-Null
 Copy-Item -LiteralPath $target -Destination $backup;R5Match $backup $f.predecessor
 R5Closed;R5Match $target $f.predecessor;R5Match $source $f.sha256
 Copy-Item -LiteralPath $source -Destination $target;R5Match $target $f.sha256
 B71Validate (Get-Content -LiteralPath $target -Raw) $manifest|Out-Null
 R5Unchanged $protected
 $result=[ordered]@{status='INSTALLED_B7_1_YAML_FIX_ENGINE_PENDING';utc=[DateTime]::UtcNow.ToString('o');game_root=$game;files=@($f);protected=$protected;tests_sha256=R5Hash $testPath;installer_sha256=R5Hash $PSCommandPath;replacements=1;additions=0;cache_writes=0;direct_save_writes=0;parsed_phases=76;engine_proof=$false}
 R5Json $receiptPath $result
}else{
 $recoverable=R5Within (Join-Path $audit ('recoverable_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))) $audit
 $dest=R5Within (Join-Path $recoverable $f.relative) $recoverable
 New-Item -ItemType Directory -Force (Split-Path -Parent $dest)|Out-Null
 R5Closed;R5Match $target $f.sha256;Move-Item -LiteralPath $target -Destination $dest;R5Match $dest $f.sha256
 Copy-Item -LiteralPath $backup -Destination $target;R5Match $target $f.predecessor
 R5Unchanged $protected
 $result=[ordered]@{status='B7_1_FILE_RECOVERED';game_root=$game;recoverable=$recoverable;files=@($f);warning='Restores the known malformed B7 predecessor for exact file recovery, not a working startup configuration. Does not rewind runtime or saved world.'}
 R5Json (Join-Path $audit 'rollback_receipt.json') $result
}
$result.status
