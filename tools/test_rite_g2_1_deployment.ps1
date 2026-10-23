Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1')
$root=Join-Path $workspace 'research\gig_restoration\rite_g2_1'
$fixture=Join-Path $root ('fixture_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))
$game=Join-Path $fixture 'game';$audit=Join-Path $fixture 'audit'
$tests=Get-Content (Join-Path $root 'tests.json') -Raw|ConvertFrom-Json
$prior=@((Join-Path $workspace 'build\RiteG2\TowerContinued_RiteG2.archive'),(Join-Path $root 'predecessor\RiteG2.reds'),(Join-Path $root 'predecessor\GigPilotR1.reds'))
for($i=0;$i -lt 3;$i++){
 $target=Join-Path $game $tests.files[$i].relative
 New-Item -ItemType Directory -Force (Split-Path -Parent $target)|Out-Null
 Copy-Item -LiteralPath $prior[$i] -Destination $target;R5Match $target $tests.files[$i].predecessor
}
$sentinel=Join-Path $game 'r6\scripts\PTFR_TestSentinel\sentinel.reds'
New-Item -ItemType Directory -Force (Split-Path -Parent $sentinel)|Out-Null
[IO.File]::WriteAllText($sentinel,'protected fixture sentinel')
$sentinelHash=R5Hash $sentinel
$installer=Join-Path $PSScriptRoot 'deploy_rite_g2_1.ps1';$params=@{WorkspaceRoot=$workspace;GameRoot=$game;AuditDirectory=$audit}
$script:refusals=0
function MustRefuse($p){$refused=$false;try{& $installer @p|Out-Null}catch{$refused=$true};if(-not $refused){throw 'Expected refusal'};$script:refusals++}
for($i=0;$i -lt 3;$i++){
 $old=Join-Path $game $tests.files[$i].relative
 [IO.File]::AppendAllText($old,'mutation');MustRefuse ($params+@{Mode='ValidateInstall'})
 Copy-Item -LiteralPath $prior[$i] -Destination $old
}
& $installer @params -Mode ValidateInstall|Out-Null
& $installer @params -Mode Install|Out-Null
R5Match $sentinel $sentinelHash
MustRefuse ($params+@{Mode='Install'})
& $installer @params -Mode ValidateRollback|Out-Null
for($i=0;$i -lt 3;$i++){
 $changed=Join-Path $game $tests.files[$i].relative
 [IO.File]::AppendAllText($changed,'mutation');MustRefuse ($params+@{Mode='ValidateRollback'})
 Copy-Item -LiteralPath (Join-Path $workspace $tests.files[$i].source) -Destination $changed
 $backup=Join-Path $audit ('backup\'+$tests.files[$i].relative)
 [IO.File]::AppendAllText($backup,'mutation');MustRefuse ($params+@{Mode='ValidateRollback'})
 Copy-Item -LiteralPath $prior[$i] -Destination $backup
}
& $installer @params -Mode Rollback|Out-Null
for($i=0;$i -lt 3;$i++){R5Match (Join-Path $game $tests.files[$i].relative) $tests.files[$i].predecessor}
R5Match $sentinel $sentinelHash
MustRefuse ($params+@{Mode='Rollback'})
MustRefuse @{WorkspaceRoot=$workspace;GameRoot=$workspace;Mode='Install'}
MustRefuse @{WorkspaceRoot=$workspace;GameRoot=$game;AuditDirectory=(Join-Path $root 'wrong_fixture');Mode='Install'}
$result=[ordered]@{status='PASS_G21_THREE_REPLACEMENT_FIXTURE';additions=0;replacements=3;refusals=$script:refusals;recoverable_rollback=$true;predecessor_restored=$true;sentinel_unchanged=$true;fixture=$fixture;installer_sha256=R5Hash $installer;tests_sha256=R5Hash (Join-Path $root 'tests.json')}
R5Json (Join-Path $root 'deployment_tests.json') $result
$result|ConvertTo-Json
