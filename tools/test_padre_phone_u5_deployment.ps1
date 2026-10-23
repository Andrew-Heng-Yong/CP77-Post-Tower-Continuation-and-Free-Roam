. (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1')
$workspace=Split-Path -Parent $PSScriptRoot;$root=Join-Path $workspace 'research/gig_restoration/padre_phone_u5'
if(Test-Path -LiteralPath (Join-Path $root 'install_receipt.json')){throw 'Installed evidence pinned'}
$base=Join-Path $root ('fixture_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))
$game=Join-Path $base 'game';$audit=Join-Path $base 'audit'
$installer=Join-Path $PSScriptRoot 'deploy_padre_phone_u5.ps1'
$argsMap=@{WorkspaceRoot=$workspace;GameRoot=$game;AuditDirectory=$audit}
$target=Join-Path $game 'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_PadrePhoneU5/init.lua'
$sentinel=Join-Path $game 'r6/scripts/PTFR_Keep/existing.reds'
New-Item -ItemType Directory -Force (Split-Path -Parent $sentinel)|Out-Null
[IO.File]::WriteAllText($sentinel,'protected fixture');$keep=R5Hash $sentinel
$refusals=0
function Refuse([scriptblock]$Call){$failed=$false;try{& $Call|Out-Null}catch{$failed=$true};if(-not $failed){throw 'Expected refusal missing'}}
& $installer @argsMap -Mode ValidateInstall|Out-Null
& $installer @argsMap -Mode Install|Out-Null
& $installer @argsMap -Mode ValidateRollback|Out-Null
Refuse {& $installer @argsMap -Mode Install};$refusals++
[IO.File]::AppendAllText($target,'-- fixture drift')
Refuse {& $installer @argsMap -Mode Rollback};$refusals++
Copy-Item -LiteralPath (Join-Path $workspace 'diagnostics/PTFR_PadrePhoneU5/init.lua') -Destination $target
Refuse {& $installer -WorkspaceRoot $workspace -GameRoot (Join-Path $workspace 'unrelated') -Mode Install};$refusals++
& $installer @argsMap -Mode Rollback|Out-Null
if(Test-Path -LiteralPath $target){throw 'Target remains'}
$r=Get-Content -LiteralPath (Join-Path $audit 'rollback_receipt.json') -Raw|ConvertFrom-Json
R5Match $r.recoverable (R5Hash (Join-Path $workspace 'diagnostics/PTFR_PadrePhoneU5/init.lua'));R5Match $sentinel $keep
Refuse {& $installer @argsMap -Mode Rollback};$refusals++
R5Json (Join-Path $root 'deployment_tests.json') ([ordered]@{status='PASS_U5_RECOVERABLE_FIXTURE';fixture=$base;refusals=$refusals;installer_sha256=R5Hash $installer;tests_sha256=R5Hash (Join-Path $root 'tests.json');protected_unchanged=$true;recoverable_hash_verified=$true})
'PASS_U5_RECOVERABLE_FIXTURE'
