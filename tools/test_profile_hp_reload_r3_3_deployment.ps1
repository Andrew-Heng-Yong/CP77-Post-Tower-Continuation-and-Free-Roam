. (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1')
$workspace=Split-Path -Parent $PSScriptRoot
$root=Join-Path $workspace 'research/restriction_profiles/profile_hp_reload_r3_3'
if(Test-Path -LiteralPath (Join-Path $root 'install_receipt.json')){throw 'Installed evidence pinned'}
$base=Join-Path $root ('fixture_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))
$game=Join-Path $base 'game';$audit=Join-Path $base 'audit'
$installer=Join-Path $PSScriptRoot 'deploy_profile_hp_reload_r3_3.ps1'
$argsMap=@{WorkspaceRoot=$workspace;GameRoot=$game;AuditDirectory=$audit}
$tp=Join-Path $root 'tests.json';$t=Get-Content -LiteralPath $tp -Raw|ConvertFrom-Json;$f=$t.file
$target=Join-Path $game $f.relative
New-Item -ItemType Directory -Force (Split-Path -Parent $target)|Out-Null
$original=Join-Path $workspace 'redscript/PTFR_Restrictions_R3/ProfilePhysical.reds'
Copy-Item -LiteralPath $original -Destination $target
$sentinel=Join-Path $game 'r6/scripts/PTFR_Test/keep.reds'
New-Item -ItemType Directory -Force (Split-Path -Parent $sentinel)|Out-Null
[IO.File]::WriteAllText($sentinel,'protected fixture sentinel');$keep=R5Hash $sentinel
function Refuse([scriptblock]$Call){$failed=$false;try{& $Call|Out-Null}catch{$failed=$true};if(-not $failed){throw 'Expected refusal missing'}}
[IO.File]::AppendAllText($target,'// wrong predecessor')
Refuse {& $installer @argsMap -Mode ValidateInstall}
Copy-Item -LiteralPath $original -Destination $target
& $installer @argsMap -Mode ValidateInstall|Out-Null
& $installer @argsMap -Mode Install|Out-Null
R5Match $target $f.sha256
& $installer @argsMap -Mode ValidateRollback|Out-Null
Refuse {& $installer @argsMap -Mode Install}
[IO.File]::AppendAllText($target,'// drift')
Refuse {& $installer @argsMap -Mode Rollback}
Copy-Item -LiteralPath (Join-Path $workspace $f.source) -Destination $target
Refuse {& $installer -WorkspaceRoot $workspace -GameRoot (Join-Path $workspace 'unrelated') -Mode Install}
$backup=Join-Path $audit 'backup/ProfilePhysical.reds'
[IO.File]::AppendAllText($backup,'// bad backup')
Refuse {& $installer @argsMap -Mode Rollback}
Copy-Item -LiteralPath $original -Destination $backup
& $installer @argsMap -Mode Rollback|Out-Null
$r=Get-Content -LiteralPath (Join-Path $audit 'rollback_receipt.json') -Raw|ConvertFrom-Json
R5Match $target $f.predecessor;R5Match $r.recoverable $f.sha256;R5Match $sentinel $keep
Refuse {& $installer @argsMap -Mode Rollback}
R5Json (Join-Path $root 'deployment_tests.json') ([ordered]@{status='PASS_HP_RELOAD_R3_3_RECOVERABLE_FIXTURE';fixture=$base;refusals=6;installer_sha256=R5Hash $installer;tests_sha256=R5Hash $tp;fixture_sha256=R5Hash $PSCommandPath;helpers_sha256=R5Hash (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1');protected_unchanged=$true;recoverable_hashes_verified=$true})
'PASS_HP_RELOAD_R3_3_RECOVERABLE_FIXTURE'
