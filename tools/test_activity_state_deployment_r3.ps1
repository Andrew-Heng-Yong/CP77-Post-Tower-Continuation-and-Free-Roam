Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1')
$audit=Join-Path $workspace 'research\activity_state_r3'
$fixture=Join-Path $audit ('fixture_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))
$game=Join-Path $fixture 'game';$receipt=Join-Path $fixture 'audit'
$sentinel=Join-Path $game 'r6\scripts\PTFR_TestSentinel\sentinel.reds'
New-Item -ItemType Directory -Force (Split-Path -Parent $sentinel)|Out-Null
[IO.File]::WriteAllText($sentinel,'protected fixture sentinel')
$hash=R5Hash $sentinel;$args=@{WorkspaceRoot=$workspace;GameRoot=$game;AuditDirectory=$receipt}
$installer=Join-Path $PSScriptRoot 'deploy_activity_state_r3.ps1'
function MustRefuse($params){$refused=$false;try{& $installer @params|Out-Null}catch{$refused=$true};if(-not $refused){throw 'Expected refusal'}}
& $installer @args -Mode ValidateInstall|Out-Null
& $installer @args -Mode Install|Out-Null
R5Match $sentinel $hash;MustRefuse ($args+@{Mode='Install'})
& $installer @args -Mode ValidateRollback|Out-Null
$tests=Get-Content (Join-Path $audit 'tests.json') -Raw|ConvertFrom-Json;$f=$tests.files[0];$path=Join-Path $game $f.relative
[IO.File]::AppendAllText($path,'mutation');MustRefuse ($args+@{Mode='ValidateRollback'})
Copy-Item -LiteralPath (Join-Path $workspace $f.source) -Destination $path
& $installer @args -Mode Rollback|Out-Null
R5Match $sentinel $hash
foreach($f in $tests.files){if(Test-Path (Join-Path $game $f.relative)){throw 'History file remains'}}
MustRefuse ($args+@{Mode='Rollback'});MustRefuse @{WorkspaceRoot=$workspace;GameRoot=$workspace;Mode='Install'}
$result=[ordered]@{status='PASS_THREE_FILE_HISTORY_FIXTURE';additions=3;replacements=0;recoverable_rollback=$true;refusals=4;sentinel_unchanged=$true;fixture=$fixture;installer_sha256=R5Hash $installer;tests_sha256=R5Hash (Join-Path $audit 'tests.json')}
R5Json (Join-Path $audit 'deployment_tests.json') $result
$result|ConvertTo-Json
