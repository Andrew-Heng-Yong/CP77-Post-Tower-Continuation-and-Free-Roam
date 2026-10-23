Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1')
$audit=Join-Path $workspace 'research\gig_restoration\rollout_r2'
$root=Join-Path $audit ('fixture_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))
$game=Join-Path $root 'game';$receipt=Join-Path $root 'audit'
$sentinel=Join-Path $game 'r6\scripts\PTFR_TestSentinel\file.reds'
New-Item -ItemType Directory -Force (Split-Path -Parent $sentinel)|Out-Null
[IO.File]::WriteAllText($sentinel,'protected fixture sentinel')
$hash=R5Hash $sentinel
$p=@{WorkspaceRoot=$workspace;GameRoot=$game;AuditDirectory=$receipt}
$installer=Join-Path $PSScriptRoot 'deploy_gig_audit_r2.ps1'
function Refuse($argsMap){$failed=$false;try{& $installer @argsMap|Out-Null}catch{$failed=$true};if(-not $failed){throw 'Expected refusal'}}
& $installer @p -Mode ValidateInstall|Out-Null
& $installer @p -Mode Install|Out-Null
Refuse ($p+@{Mode='Install'})
& $installer @p -Mode ValidateRollback|Out-Null
$target=Join-Path $game 'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_GigAuditR2/init.lua'
[IO.File]::AppendAllText($target,'mutation')
Refuse ($p+@{Mode='Rollback'})
Copy-Item -LiteralPath (Join-Path $workspace 'diagnostics/PTFR_GigAuditR2/init.lua') -Destination $target
& $installer @p -Mode Rollback|Out-Null
R5Match $sentinel $hash
Refuse ($p+@{Mode='Rollback'})
Refuse @{WorkspaceRoot=$workspace;GameRoot=$workspace;Mode='Install'}
$result=[ordered]@{status='PASS_TWO_FILE_AUDIT_FIXTURE';tests_sha256=R5Hash (Join-Path $audit 'tests.json');installer_sha256=R5Hash $installer;additions=2;replacements=0;refusals=4;sentinel_unchanged=$true;recoverable_rollback=$true;fixture=$root}
R5Json (Join-Path $audit 'deployment_tests.json') $result
$result|ConvertTo-Json
