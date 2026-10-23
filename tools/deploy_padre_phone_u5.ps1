param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),[string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',[string]$AuditDirectory='',[ValidateSet('ValidateInstall','Install','ValidateRollback','Rollback')][string]$Mode='ValidateInstall')
. (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1')
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\');$root=Join-Path $workspace 'research/gig_restoration/padre_phone_u5';$game=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
$actual='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$fixture=$game.StartsWith($root+'\fixture_',[StringComparison]::OrdinalIgnoreCase)
if($game -ne $actual -and -not $fixture){throw 'Unsupported game root'}
$audit=if($AuditDirectory){R5Within $AuditDirectory $workspace}else{$root}
if($fixture -and (-not $AuditDirectory -or -not $audit.StartsWith((Split-Path -Parent $game)+'\',[StringComparison]::OrdinalIgnoreCase))){throw 'Fixture audit mismatch'}
if(-not $fixture -and $AuditDirectory){throw 'Actual audit must be canonical'}
R5Closed
$source=Join-Path $workspace 'diagnostics/PTFR_PadrePhoneU5/init.lua'
$relative='bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_PadrePhoneU5/init.lua'
$target=R5Within (Join-Path $game $relative) $game
$tp=Join-Path $root 'tests.json';$tests=Get-Content -LiteralPath $tp -Raw|ConvertFrom-Json
if($tests.status -ne 'PASS_U5_READ_ONLY_LUAJIT_NOT_ENGINE_PROOF'){throw 'Tests missing'}
R5Match $source $tests.source_sha256
R5Match (Join-Path $workspace 'tools/test_padre_phone_u5.py') $tests.test_sha256
if(-not $fixture){
 $d=Get-Content -LiteralPath (Join-Path $root 'deployment_tests.json') -Raw|ConvertFrom-Json
 if($d.status -ne 'PASS_U5_RECOVERABLE_FIXTURE' -or $d.installer_sha256 -ne (R5Hash $PSCommandPath) -or $d.tests_sha256 -ne (R5Hash $tp)){throw 'Fixture tests stale'}
 # Runtime dependencies must match for installation; removing this logger does not depend on them.
 if($Mode -in @('ValidateInstall','Install')){
  $u4=Get-Content -LiteralPath (Join-Path $workspace 'research/gig_restoration/native_jeopardy_u4/install_receipt.json') -Raw|ConvertFrom-Json
  foreach($f in $u4.files){R5Match (Join-Path $game $f.relative) $f.sha256}
 }
}
$protected=R5Snapshot $game @($target)
if(-not $fixture){foreach($folder in @('archive/pc/mod','red4ext/plugins','r6/scripts','r6/cache')){foreach($p in Get-ChildItem -LiteralPath (Join-Path $game $folder) -Recurse -File){if($p.FullName -ne $target -and ($folder -eq 'r6/cache' -or $p.Extension -in @('.archive','.xl','.reds','.dll'))){$protected[$p.FullName]=R5Hash $p.FullName}}}}
$receipt=Join-Path $audit 'install_receipt.json'
if($Mode -in @('ValidateRollback','Rollback')){
 $r=Get-Content -LiteralPath $receipt -Raw|ConvertFrom-Json
 if($r.status -ne 'INSTALLED_U5_GETTER_ONLY' -or $r.game_root -ne $game -or $r.relative -ne $relative -or $r.installer_sha256 -ne (R5Hash $PSCommandPath) -or $r.tests_sha256 -ne (R5Hash $tp)){throw 'Receipt mismatch'}
 R5Match $target $tests.source_sha256
 if(Test-Path -LiteralPath (Join-Path $audit 'rollback_receipt.json')){throw 'Already recovered'}
}else{
 if((Test-Path -LiteralPath $receipt) -or (Test-Path -LiteralPath $target)){throw 'Existing receipt or addition; refuse overwrite'}
}
R5Closed
if($Mode.StartsWith('Validate')){[ordered]@{status='VALIDATED';mode=$Mode;additions=1;replacements=0;protected_files=$protected.Count}|ConvertTo-Json;return}
New-Item -ItemType Directory -Force $audit|Out-Null
if($Mode -eq 'Install'){
 R5Match $source $tests.source_sha256
 if(Test-Path -LiteralPath $target){throw 'Addition appeared'}
 New-Item -ItemType Directory -Force (Split-Path -Parent $target)|Out-Null
 Copy-Item -LiteralPath $source -Destination $target
 R5Match $target $tests.source_sha256;R5Unchanged $protected
 R5Json $receipt ([ordered]@{status='INSTALLED_U5_GETTER_ONLY';utc=[DateTime]::UtcNow.ToString('o');game_root=$game;relative=$relative;sha256=$tests.source_sha256;tests_sha256=R5Hash $tp;installer_sha256=R5Hash $PSCommandPath;protected=$protected;additions=1;replacements=0;cache_writes=0;direct_save_writes=0;gameplay_changes=0})
 'INSTALLED_U5_GETTER_ONLY'
}else{
 $dest=R5Within (Join-Path $audit ('recoverable_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')+'/init.lua')) $audit
 New-Item -ItemType Directory -Force (Split-Path -Parent $dest)|Out-Null
 Move-Item -LiteralPath $target -Destination $dest
 R5Match $dest $tests.source_sha256;R5Unchanged $protected
 R5Json (Join-Path $audit 'rollback_receipt.json') ([ordered]@{status='U5_LOGGER_RECOVERED';recoverable=$dest;logs_preserved=$true;gameplay_changes=0})
 'U5_LOGGER_RECOVERED'
}
