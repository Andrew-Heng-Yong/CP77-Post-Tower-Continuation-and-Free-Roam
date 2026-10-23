Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1')
$root=Join-Path $workspace 'research\gig_restoration\family_b7'
if(Test-Path (Join-Path $root 'install_receipt.json')){throw 'Installed evidence pinned'}
$fixture=Join-Path $root ('fixture_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'));$game=Join-Path $fixture 'game';$audit=Join-Path $fixture 'audit'
$t=Get-Content (Join-Path $root 'tests.json') -Raw|ConvertFrom-Json
foreach($f in $t.files){if($f.predecessor){$target=Join-Path $game $f.relative;New-Item -ItemType Directory -Force (Split-Path -Parent $target)|Out-Null;Copy-Item -LiteralPath (Join-Path (Join-Path $root 'predecessor') (Split-Path -Leaf $f.source)) -Destination $target;R5Match $target $f.predecessor}}
$sentinel=Join-Path $game 'r6\scripts\PTFR_TestSentinel\sentinel.reds';New-Item -ItemType Directory -Force (Split-Path -Parent $sentinel)|Out-Null
Copy-Item -LiteralPath (Join-Path $root 'predecessor\ActivityStateR3.reds') -Destination $sentinel;$h=R5Hash $sentinel
$installer=Join-Path $PSScriptRoot 'deploy_gig_family_b7.ps1';$params=@{WorkspaceRoot=$workspace;GameRoot=$game;AuditDirectory=$audit};$script:refusals=0
function MustRefuse($p){$refused=$false;try{& $installer @p|Out-Null}catch{$refused=$true};if(-not $refused){throw 'Expected refusal'};$script:refusals+=1}
$change=Join-Path $game $t.files[5].relative
Copy-Item -LiteralPath (Join-Path $workspace $t.files[2].source) -Destination $change;MustRefuse ($params+@{Mode='ValidateInstall'})
Copy-Item -LiteralPath (Join-Path $root 'predecessor\ActivityStateR3.reds') -Destination $change
& $installer @params -Mode ValidateInstall|Out-Null;& $installer @params -Mode Install|Out-Null;R5Match $sentinel $h
MustRefuse ($params+@{Mode='Install'});& $installer @params -Mode ValidateRollback|Out-Null
Copy-Item -LiteralPath (Join-Path $root 'predecessor\ActivityStateR3.reds') -Destination $change;MustRefuse ($params+@{Mode='ValidateRollback'})
Copy-Item -LiteralPath (Join-Path $workspace $t.files[5].source) -Destination $change
$backup=Join-Path $audit ('backup\'+$t.files[5].relative)
Copy-Item -LiteralPath (Join-Path $workspace $t.files[2].source) -Destination $backup;MustRefuse ($params+@{Mode='ValidateRollback'})
Copy-Item -LiteralPath (Join-Path $root 'predecessor\ActivityStateR3.reds') -Destination $backup
& $installer @params -Mode Rollback|Out-Null
foreach($f in $t.files){$target=Join-Path $game $f.relative;if($f.predecessor){R5Match $target $f.predecessor}elseif(Test-Path $target){throw 'Addition not moved to recovery'}}
R5Match $sentinel $h;MustRefuse ($params+@{Mode='Rollback'})
MustRefuse @{WorkspaceRoot=$workspace;GameRoot=$workspace;Mode='Install'}
MustRefuse @{WorkspaceRoot=$workspace;GameRoot=$game;AuditDirectory=(Join-Path $root 'wrong_fixture');Mode='Install'}
$r=Get-Content (Join-Path $audit 'rollback_receipt.json') -Raw|ConvertFrom-Json;foreach($f in $t.files){R5Match (Join-Path $r.recoverable $f.relative) $f.sha256}
$result=[ordered]@{status='PASS_B7_RECOVERABLE_FIXTURE';additions=5;replacements=1;refusals=$script:refusals;recoverable_rollback=$true;predecessors_restored=$true;sentinel_unchanged=$true;fixture=$fixture;installer_sha256=R5Hash $installer;tests_sha256=R5Hash (Join-Path $root 'tests.json')}
R5Json (Join-Path $root 'deployment_tests.json') $result;$result|ConvertTo-Json
