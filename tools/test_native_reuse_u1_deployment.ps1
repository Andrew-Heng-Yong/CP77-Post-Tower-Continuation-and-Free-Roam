param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
. (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1')
$root=Join-Path $WorkspaceRoot 'research/gig_restoration/native_reuse_u1'
if(Test-Path (Join-Path $root 'install_receipt.json')){throw 'Installed evidence pinned'}
$case=Join-Path $root ('fixture_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'));$game=Join-Path $case 'game';$audit=Join-Path $case 'audit'
$target=Join-Path $game 'r6/scripts/PTFR_GigFamilyB7/GigFamilyB7.reds';New-Item -ItemType Directory -Force (Split-Path -Parent $target)|Out-Null
Copy-Item (Join-Path $WorkspaceRoot 'redscript/PTFR_GigFamilyB7/GigFamilyB7.reds') $target
$deploy=Join-Path $PSScriptRoot 'deploy_native_reuse_u1.ps1'
& $deploy -GameRoot $game -AuditDirectory $audit -Mode ValidateInstall
& $deploy -GameRoot $game -AuditDirectory $audit -Mode Install
& $deploy -GameRoot $game -AuditDirectory $audit -Mode ValidateRollback
$refused=0
try{& $deploy -GameRoot $game -AuditDirectory $audit -Mode Install;throw 'ACCEPTED_MUTANT'}catch{if($_ -match 'ACCEPTED_MUTANT'){throw};$refused++}
try{& $deploy -GameRoot (Join-Path $WorkspaceRoot 'unsafe_u1_target') -Mode ValidateInstall;throw 'ACCEPTED_MUTANT'}catch{if($_ -match 'ACCEPTED_MUTANT'){throw};$refused++}
try{& $deploy -GameRoot $game -AuditDirectory (Join-Path $WorkspaceRoot 'wrong_audit') -Mode ValidateRollback;throw 'ACCEPTED_MUTANT'}catch{if($_ -match 'ACCEPTED_MUTANT'){throw};$refused++}
# Fixture-only changed target must refuse rollback; restore it from tested source.
Copy-Item (Join-Path $WorkspaceRoot 'redscript/PTFR_GigFamilyB7/GigFamilyB7.reds') $target -Force
try{& $deploy -GameRoot $game -AuditDirectory $audit -Mode ValidateRollback;throw 'ACCEPTED_MUTANT'}catch{if($_ -match 'ACCEPTED_MUTANT'){throw};$refused++}
Copy-Item (Join-Path $WorkspaceRoot 'build/NativeReuseU1/GigFamilyB7.reds') $target -Force
& $deploy -GameRoot $game -AuditDirectory $audit -Mode Rollback
R5Match $target '9BC70799B64D4A6EB8B605CCC51ECB1FB9C6D378F060B10EF79E2B7C6A92CD51'
$m=Get-Content (Join-Path $root 'manifest.json') -Raw|ConvertFrom-Json
foreach($f in $m.files[0..2]){if(Test-Path (Join-Path $game $f.relative)){throw 'Addition left behind'}}
try{& $deploy -GameRoot $game -AuditDirectory $audit -Mode Rollback;throw 'ACCEPTED_MUTANT'}catch{if($_ -match 'ACCEPTED_MUTANT'){throw};$refused++}
R5Json (Join-Path $root 'deployment_tests.json') ([ordered]@{status='PASS_U1_RECOVERABLE_FIXTURE';fixture=$case;recoverable_rollback=$true;refused_cases=$refused;tests_sha256=R5Hash (Join-Path $root 'tests.json');installer_sha256=R5Hash $deploy})
'PASS_U1_RECOVERABLE_FIXTURE'
