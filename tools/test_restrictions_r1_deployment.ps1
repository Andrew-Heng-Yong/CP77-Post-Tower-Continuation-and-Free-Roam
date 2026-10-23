param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
. (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1')
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\')
$out=Join-Path $workspace 'research/restriction_profiles/implementation_r1'
$fixture=R5Within (Join-Path $out ('fixture_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))) $workspace
$game=Join-Path $fixture 'game'; $audit=Join-Path $fixture 'audit'
New-Item -ItemType Directory -Force (Join-Path $game 'r6/cache'),(Join-Path $game 'r6/scripts/PTFR_Protected'),$audit | Out-Null
Copy-Item -LiteralPath 'C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077/r6/cache/final.redscripts' -Destination (Join-Path $game 'r6/cache/final.redscripts')
Copy-Item -LiteralPath (Join-Path $workspace 'redscript/PTFR_Afterlife_Faces_R5/AfterlifeFacesR5.reds') -Destination (Join-Path $game 'r6/scripts/PTFR_Protected/sentinel.reds')
$before=R5Snapshot $game
$deploy=Join-Path $PSScriptRoot 'deploy_restrictions_r1.ps1'
foreach($mode in @('ValidateInstall','Install','ValidateRollback','Rollback')){
 & $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $audit -Mode $mode
 if(-not $?){throw "Fixture failed: $mode"}
 R5Unchanged $before
}
$tests=Get-Content -LiteralPath (Join-Path $out 'tests.json') -Raw | ConvertFrom-Json
foreach($f in $tests.files){if(Test-Path -LiteralPath (Join-Path $game $f.relative)){throw 'Rollback retained installed addition'}}
$rollback=Get-Content -LiteralPath (Join-Path $audit 'rollback_receipt.json') -Raw | ConvertFrom-Json
foreach($f in $tests.files){R5Match (R5Within (Join-Path $rollback.recovery $f.relative) $rollback.recovery) $f.sha256}
$result=@{status='PASS_RESTRICTIONS_R1_INSTALL_ROLLBACK_FIXTURE';fixture=$fixture;installer_sha256=(R5Hash $deploy);fixture_sha256=(R5Hash $PSCommandPath);helpers_sha256=(R5Hash (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1'));tests_sha256=(R5Hash (Join-Path $out 'tests.json'));protected_unchanged=$true;recoverable_rollback=$true;game_writes=0}
R5Json (Join-Path $out 'deployment_tests.json') $result
$result | ConvertTo-Json
