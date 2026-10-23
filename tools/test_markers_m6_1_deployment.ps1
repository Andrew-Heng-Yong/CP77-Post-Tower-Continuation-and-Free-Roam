Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1')
$root=Join-Path $workspace 'research\gig_restoration\markers_m6_1'
if(Test-Path (Join-Path $root 'install_receipt.json')){throw 'Installed evidence pinned'}
$fixture=Join-Path $root ('fixture_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))
$game=Join-Path $fixture 'game';$audit=Join-Path $fixture 'audit'
$t=Get-Content (Join-Path $root 'tests.json') -Raw|ConvertFrom-Json;$f=$t.files[0]
$target=Join-Path $game $f.relative
New-Item -ItemType Directory -Force (Split-Path -Parent $target)|Out-Null
$predecessor=Join-Path $root 'predecessor\GigMarkersM6.reds'
Copy-Item -LiteralPath $predecessor -Destination $target
$sentinel=Join-Path $game 'r6\scripts\PTFR_TestSentinel\sentinel.reds'
New-Item -ItemType Directory -Force (Split-Path -Parent $sentinel)|Out-Null
Copy-Item -LiteralPath $predecessor -Destination $sentinel;$h=R5Hash $sentinel
$installer=Join-Path $PSScriptRoot 'deploy_markers_m6_1.ps1'
$params=@{WorkspaceRoot=$workspace;GameRoot=$game;AuditDirectory=$audit};$script:refusals=0
function MustRefuse($p){$refused=$false;try{& $installer @p|Out-Null}catch{$refused=$true};if(-not $refused){throw 'Expected refusal'};$script:refusals+=1}
Copy-Item -LiteralPath (Join-Path $workspace $f.source) -Destination $target;MustRefuse ($params+@{Mode='ValidateInstall'})
Copy-Item -LiteralPath $predecessor -Destination $target
& $installer @params -Mode ValidateInstall|Out-Null
& $installer @params -Mode Install|Out-Null;R5Match $sentinel $h
MustRefuse ($params+@{Mode='Install'});& $installer @params -Mode ValidateRollback|Out-Null
Copy-Item -LiteralPath $predecessor -Destination $target;MustRefuse ($params+@{Mode='ValidateRollback'})
Copy-Item -LiteralPath (Join-Path $workspace $f.source) -Destination $target
$backup=Join-Path $audit ('backup\'+$f.relative)
Copy-Item -LiteralPath (Join-Path $workspace $f.source) -Destination $backup;MustRefuse ($params+@{Mode='ValidateRollback'})
Copy-Item -LiteralPath $predecessor -Destination $backup
& $installer @params -Mode Rollback|Out-Null;R5Match $target $f.predecessor;R5Match $sentinel $h
MustRefuse ($params+@{Mode='Rollback'})
MustRefuse @{WorkspaceRoot=$workspace;GameRoot=$workspace;Mode='Install'}
MustRefuse @{WorkspaceRoot=$workspace;GameRoot=$game;AuditDirectory=(Join-Path $root 'wrong_fixture');Mode='Install'}
$r=Get-Content (Join-Path $audit 'rollback_receipt.json') -Raw|ConvertFrom-Json
R5Match (Join-Path $r.recoverable $f.relative) $f.sha256
$result=[ordered]@{status='PASS_M6_1_RECOVERABLE_FIXTURE';replacements=1;refusals=$script:refusals;recoverable_rollback=$true;predecessor_restored=$true;sentinel_unchanged=$true;fixture=$fixture;installer_sha256=R5Hash $installer;tests_sha256=R5Hash (Join-Path $root 'tests.json')}
R5Json (Join-Path $root 'deployment_tests.json') $result;$result|ConvertTo-Json
