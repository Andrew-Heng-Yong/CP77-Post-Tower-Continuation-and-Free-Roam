Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1')
$root=Join-Path $workspace 'research\johnny_voice_jv1'
$fixture=Join-Path $root ('fixture_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))
$game=Join-Path $fixture 'game';$audit=Join-Path $fixture 'audit'
$sentinel=Join-Path $game 'r6\scripts\PTFR_TestSentinel\sentinel.reds'
New-Item -ItemType Directory -Force (Split-Path -Parent $sentinel)|Out-Null
[IO.File]::WriteAllText($sentinel,'protected fixture sentinel');$sentinelHash=R5Hash $sentinel
$installer=Join-Path $PSScriptRoot 'deploy_johnny_voice_jv1.ps1';$params=@{WorkspaceRoot=$workspace;GameRoot=$game;AuditDirectory=$audit}
function MustRefuse($p){$refused=$false;try{& $installer @p|Out-Null}catch{$refused=$true};if(-not $refused){throw 'Expected refusal'}}
& $installer @params -Mode ValidateInstall|Out-Null
& $installer @params -Mode Install|Out-Null
R5Match $sentinel $sentinelHash
MustRefuse ($params+@{Mode='Install'})
& $installer @params -Mode ValidateRollback|Out-Null
$tests=Get-Content (Join-Path $root 'tests.json') -Raw|ConvertFrom-Json
$target=Join-Path $game $tests.files[0].relative
[IO.File]::AppendAllText($target,'mutation');MustRefuse ($params+@{Mode='ValidateRollback'})
Copy-Item -LiteralPath (Join-Path $workspace $tests.files[0].source) -Destination $target
& $installer @params -Mode Rollback|Out-Null
R5Match $sentinel $sentinelHash
if(Test-Path $target){throw 'Addition remains'}
$rr=Get-Content (Join-Path $audit 'rollback_receipt.json') -Raw|ConvertFrom-Json
R5Match (Join-Path $rr.recoverable $tests.files[0].relative) $tests.files[0].sha256
MustRefuse ($params+@{Mode='Rollback'})
MustRefuse @{WorkspaceRoot=$workspace;GameRoot=$workspace;Mode='Install'}
MustRefuse @{WorkspaceRoot=$workspace;GameRoot=$game;AuditDirectory=(Join-Path $root 'wrong_fixture');Mode='Install'}
$result=[ordered]@{status='PASS_JV1_DEPLOYMENT_FIXTURE';additions=1;replacements=0;refusals=5;recoverable_rollback=$true;sentinel_unchanged=$true;fixture=$fixture;installer_sha256=R5Hash $installer;tests_sha256=R5Hash (Join-Path $root 'tests.json')}
R5Json (Join-Path $root 'deployment_tests.json') $result
$result|ConvertTo-Json
