Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1')
$root=Join-Path $workspace 'research\gig_restoration\fresh_b5_1'
if(Test-Path -LiteralPath (Join-Path $root 'install_receipt.json')){throw 'Installed evidence pinned'}
$fixture=Join-Path $root ('fixture_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))
$game=Join-Path $fixture 'game';$audit=Join-Path $fixture 'audit'
$t=Get-Content -LiteralPath (Join-Path $root 'tests.json') -Raw|ConvertFrom-Json
$oldNames=@('FreshGigsB5.reds','ActivityStateR3.reds','init.lua')
$i=0
foreach($f in $t.files){
 $target=Join-Path $game $f.relative
 New-Item -ItemType Directory -Force (Split-Path -Parent $target)|Out-Null
 Copy-Item -LiteralPath (Join-Path (Join-Path $root 'predecessor') $oldNames[$i]) -Destination $target
 R5Match $target $f.predecessor
 $i+=1
}
$sentinel=Join-Path $game 'r6\scripts\PTFR_TestSentinel\sentinel.reds'
New-Item -ItemType Directory -Force (Split-Path -Parent $sentinel)|Out-Null
Copy-Item -LiteralPath (Join-Path $root 'predecessor\FreshGigsB5.reds') -Destination $sentinel
$h=R5Hash $sentinel
$installer=Join-Path $PSScriptRoot 'deploy_fresh_gigs_b5_1.ps1'
$params=@{WorkspaceRoot=$workspace;GameRoot=$game;AuditDirectory=$audit}
$script:refusals=0
function MustRefuse($p){$refused=$false;try{& $installer @p|Out-Null}catch{$refused=$true};if(-not $refused){throw 'Expected refusal'};$script:refusals+=1}
$changed=Join-Path $game $t.files[0].relative
Copy-Item -LiteralPath (Join-Path $root 'predecessor\init.lua') -Destination $changed
MustRefuse ($params+@{Mode='ValidateInstall'})
Copy-Item -LiteralPath (Join-Path $root 'predecessor\FreshGigsB5.reds') -Destination $changed
& $installer @params -Mode ValidateInstall|Out-Null
& $installer @params -Mode Install|Out-Null
R5Match $sentinel $h
MustRefuse ($params+@{Mode='Install'})
& $installer @params -Mode ValidateRollback|Out-Null
Copy-Item -LiteralPath (Join-Path $root 'predecessor\FreshGigsB5.reds') -Destination $changed
MustRefuse ($params+@{Mode='ValidateRollback'})
Copy-Item -LiteralPath (Join-Path $workspace $t.files[0].source) -Destination $changed
$backup=Join-Path $audit ('backup\'+$t.files[0].relative)
Copy-Item -LiteralPath (Join-Path $root 'predecessor\init.lua') -Destination $backup
MustRefuse ($params+@{Mode='ValidateRollback'})
Copy-Item -LiteralPath (Join-Path $root 'predecessor\FreshGigsB5.reds') -Destination $backup
& $installer @params -Mode Rollback|Out-Null
foreach($f in $t.files){R5Match (Join-Path $game $f.relative) $f.predecessor}
R5Match $sentinel $h
MustRefuse ($params+@{Mode='Rollback'})
MustRefuse @{WorkspaceRoot=$workspace;GameRoot=$workspace;Mode='Install'}
MustRefuse @{WorkspaceRoot=$workspace;GameRoot=$game;AuditDirectory=(Join-Path $root 'wrong_fixture');Mode='Install'}
$r=Get-Content -LiteralPath (Join-Path $audit 'rollback_receipt.json') -Raw|ConvertFrom-Json
foreach($f in $t.files){R5Match (Join-Path $r.recoverable $f.relative) $f.sha256}
$result=[ordered]@{status='PASS_B5_1_THREE_REPLACEMENT_FIXTURE';additions=0;replacements=3;refusals=$script:refusals;recoverable_rollback=$true;predecessors_restored=$true;sentinel_unchanged=$true;fixture=$fixture;installer_sha256=R5Hash $installer;tests_sha256=R5Hash (Join-Path $root 'tests.json')}
R5Json (Join-Path $root 'deployment_tests.json') $result
$result|ConvertTo-Json
