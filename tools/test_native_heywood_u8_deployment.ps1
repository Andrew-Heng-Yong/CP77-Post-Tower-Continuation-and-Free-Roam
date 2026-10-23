. (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1')
$workspace=Split-Path -Parent $PSScriptRoot;$root=Join-Path $workspace 'research/gig_restoration/native_heywood_u8'
if(Test-Path (Join-Path $root 'install_receipt.json')){throw 'Installed evidence pinned'}
$base=Join-Path $root ('fixture_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'));$game=Join-Path $base 'game';$audit=Join-Path $base 'audit'
$installer=Join-Path $PSScriptRoot 'deploy_native_heywood_u8.ps1';$argsMap=@{WorkspaceRoot=$workspace;GameRoot=$game;AuditDirectory=$audit}
$m=Get-Content (Join-Path $root 'manifest.json') -Raw|ConvertFrom-Json
$target=Join-Path $game $m.files[3].relative;New-Item -ItemType Directory -Force (Split-Path -Parent $target)|Out-Null
$predecessor=Join-Path $workspace 'build/NativeJeopardyU4/GigFamilyB7.reds';Copy-Item -LiteralPath $predecessor -Destination $target
$sentinel=Join-Path $game 'r6/scripts/PTFR_Test/keep.reds';New-Item -ItemType Directory -Force (Split-Path -Parent $sentinel)|Out-Null;[IO.File]::WriteAllText($sentinel,'protected');$keep=R5Hash $sentinel
function Refuse([scriptblock]$Call){$failed=$false;try{& $Call|Out-Null}catch{$failed=$true};if(-not $failed){throw 'Expected refusal missing'}}
[IO.File]::AppendAllText($target,'// wrong predecessor');Refuse {& $installer @argsMap -Mode ValidateInstall}
Copy-Item -LiteralPath $predecessor -Destination $target
$extra=Join-Path $game $m.files[2].relative;New-Item -ItemType Directory -Force (Split-Path -Parent $extra)|Out-Null;[IO.File]::WriteAllText($extra,'unrecognized');Refuse {& $installer @argsMap -Mode ValidateInstall}
$saved=R5Within (Join-Path $base 'unknown.reds') $base;Move-Item -LiteralPath $extra -Destination $saved
& $installer @argsMap -Mode ValidateInstall|Out-Null
& $installer @argsMap -Mode Install|Out-Null
& $installer @argsMap -Mode ValidateRollback|Out-Null
Refuse {& $installer @argsMap -Mode Install}
[IO.File]::AppendAllText($target,'// drift');Refuse {& $installer @argsMap -Mode Rollback}
Copy-Item -LiteralPath (Join-Path $workspace $m.files[3].source) -Destination $target
$backup=Join-Path $audit 'backup/GigFamilyB7.reds';[IO.File]::AppendAllText($backup,'// drift');Refuse {& $installer @argsMap -Mode Rollback};Copy-Item -LiteralPath $predecessor -Destination $backup
Refuse {& $installer -WorkspaceRoot $workspace -GameRoot (Join-Path $workspace 'unrelated') -Mode Install}
& $installer @argsMap -Mode Rollback|Out-Null
$r=Get-Content (Join-Path $audit 'rollback_receipt.json') -Raw|ConvertFrom-Json
foreach($f in $m.files){R5Match (Join-Path $r.recoverable $f.relative) $f.sha256;if($f.predecessor){R5Match (Join-Path $game $f.relative) $f.predecessor}elseif(Test-Path (Join-Path $game $f.relative)){throw 'Addition remains'}};R5Match $sentinel $keep
Refuse {& $installer @argsMap -Mode Rollback}
R5Json (Join-Path $root 'deployment_tests.json') ([ordered]@{status='PASS_U8_RECOVERABLE_FIXTURE';fixture=$base;refusals=7;installer_sha256=R5Hash $installer;tests_sha256=R5Hash (Join-Path $root 'tests.json');protected_unchanged=$true;recoverable_hashes_verified=$true})
'PASS_U8_RECOVERABLE_FIXTURE'
