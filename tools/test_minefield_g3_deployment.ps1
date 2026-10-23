Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1')
$root=Join-Path $workspace 'research\gig_restoration\minefield_g3'
$fixture=Join-Path $root ('fixture_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))
$game=Join-Path $fixture 'game';$audit=Join-Path $fixture 'audit'
$old=Join-Path $game 'r6\scripts\PTFR_ActivityStateR3\ActivityStateR3.reds'
New-Item -ItemType Directory -Force (Split-Path -Parent $old)|Out-Null
Copy-Item -LiteralPath (Join-Path $root 'predecessor\ActivityStateR3.reds') -Destination $old
$sentinel=Join-Path $game 'r6\scripts\PTFR_TestSentinel\sentinel.reds'
New-Item -ItemType Directory -Force (Split-Path -Parent $sentinel)|Out-Null
[IO.File]::WriteAllText($sentinel,'protected fixture sentinel')
$sentinelHash=R5Hash $sentinel;$oldHash=R5Hash $old
$installer=Join-Path $PSScriptRoot 'deploy_minefield_g3.ps1';$params=@{WorkspaceRoot=$workspace;GameRoot=$game;AuditDirectory=$audit}
function MustRefuse($p){$refused=$false;try{& $installer @p|Out-Null}catch{$refused=$true};if(-not $refused){throw 'Expected refusal'}}
# Wrong predecessor is refused before any addition or backup.
[IO.File]::AppendAllText($old,'mutation');MustRefuse ($params+@{Mode='ValidateInstall'})
Copy-Item -LiteralPath (Join-Path $root 'predecessor\ActivityStateR3.reds') -Destination $old
& $installer @params -Mode ValidateInstall|Out-Null
& $installer @params -Mode Install|Out-Null
R5Match $sentinel $sentinelHash
MustRefuse ($params+@{Mode='Install'})
& $installer @params -Mode ValidateRollback|Out-Null
$tests=Get-Content (Join-Path $root 'tests.json') -Raw|ConvertFrom-Json
$changed=Join-Path $game $tests.files[2].relative
[IO.File]::AppendAllText($changed,'mutation');MustRefuse ($params+@{Mode='ValidateRollback'})
Copy-Item -LiteralPath (Join-Path $workspace $tests.files[2].source) -Destination $changed
$backup=Join-Path $audit ('backup\'+$tests.files[4].relative)
[IO.File]::AppendAllText($backup,'mutation');MustRefuse ($params+@{Mode='ValidateRollback'})
Copy-Item -LiteralPath (Join-Path $root 'predecessor\ActivityStateR3.reds') -Destination $backup
& $installer @params -Mode Rollback|Out-Null
R5Match $old $oldHash;R5Match $sentinel $sentinelHash
foreach($f in $tests.files){if(-not $f.predecessor -and (Test-Path (Join-Path $game $f.relative))){throw 'Addition remains'}}
MustRefuse ($params+@{Mode='Rollback'})
MustRefuse @{WorkspaceRoot=$workspace;GameRoot=$workspace;Mode='Install'}
MustRefuse @{WorkspaceRoot=$workspace;GameRoot=$game;AuditDirectory=(Join-Path $root 'wrong_fixture');Mode='Install'}
$result=[ordered]@{status='PASS_G3_MIXED_DEPLOYMENT_FIXTURE';additions=4;replacements=1;refusals=7;recoverable_rollback=$true;predecessor_restored=$true;sentinel_unchanged=$true;fixture=$fixture;installer_sha256=R5Hash $installer;tests_sha256=R5Hash (Join-Path $root 'tests.json')}
R5Json (Join-Path $root 'deployment_tests.json') $result
$result|ConvertTo-Json
