Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1')
$root=Join-Path $workspace 'research\side_job_cleanup_s1_1'
$fixture=Join-Path $root ('fixture_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'));$game=Join-Path $fixture 'game';$audit=Join-Path $fixture 'audit'
$tests=Get-Content (Join-Path $root 'tests.json') -Raw|ConvertFrom-Json
foreach($f in $tests.files){$old=Join-Path $game $f.relative;New-Item -ItemType Directory -Force (Split-Path -Parent $old)|Out-Null;Copy-Item -LiteralPath (Join-Path (Join-Path $root 'predecessor') ([IO.Path]::GetFileName($f.relative))) -Destination $old;R5Match $old $f.predecessor}
$sentinel=Join-Path $game 'r6\scripts\PTFR_TestSentinel\sentinel.reds';New-Item -ItemType Directory -Force (Split-Path -Parent $sentinel)|Out-Null
[IO.File]::WriteAllText($sentinel,'protected fixture sentinel');$sentinelHash=R5Hash $sentinel
$installer=Join-Path $PSScriptRoot 'deploy_side_cleanup_s1_1.ps1';$params=@{WorkspaceRoot=$workspace;GameRoot=$game;AuditDirectory=$audit}
function MustRefuse($p){$refused=$false;try{& $installer @p|Out-Null}catch{$refused=$true};if(-not $refused){throw 'Expected refusal'}}
$old=Join-Path $game $tests.files[1].relative;[IO.File]::AppendAllText($old,'mutation');MustRefuse ($params+@{Mode='ValidateInstall'})
Copy-Item -LiteralPath (Join-Path $root 'predecessor/SideJobPilotS1.reds') -Destination $old
& $installer @params -Mode ValidateInstall|Out-Null
& $installer @params -Mode Install|Out-Null;R5Match $sentinel $sentinelHash
MustRefuse ($params+@{Mode='Install'})
& $installer @params -Mode ValidateRollback|Out-Null
[IO.File]::AppendAllText($old,'mutation');MustRefuse ($params+@{Mode='ValidateRollback'})
Copy-Item -LiteralPath (Join-Path $workspace $tests.files[1].source) -Destination $old
$backup=Join-Path $audit ('backup/'+$tests.files[1].relative);[IO.File]::AppendAllText($backup,'mutation');MustRefuse ($params+@{Mode='ValidateRollback'})
Copy-Item -LiteralPath (Join-Path $root 'predecessor/SideJobPilotS1.reds') -Destination $backup
& $installer @params -Mode Rollback|Out-Null;R5Match $sentinel $sentinelHash
foreach($f in $tests.files){R5Match (Join-Path $game $f.relative) $f.predecessor}
MustRefuse ($params+@{Mode='Rollback'})
MustRefuse @{WorkspaceRoot=$workspace;GameRoot=$workspace;Mode='Install'}
MustRefuse @{WorkspaceRoot=$workspace;GameRoot=$game;AuditDirectory=(Join-Path $root 'wrong_fixture');Mode='Install'}
$result=[ordered]@{status='PASS_S1_1_REPLACEMENT_DEPLOYMENT_FIXTURE';additions=0;replacements=3;refusals=7;recoverable_rollback=$true;predecessors_restored=$true;sentinel_unchanged=$true;fixture=$fixture;installer_sha256=R5Hash $installer;tests_sha256=R5Hash (Join-Path $root 'tests.json')}
R5Json (Join-Path $root 'deployment_tests.json') $result;$result|ConvertTo-Json
