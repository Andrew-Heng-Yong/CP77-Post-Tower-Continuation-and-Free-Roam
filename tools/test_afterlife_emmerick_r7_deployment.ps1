param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
. (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1')
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\')
$audit=Join-Path $workspace 'research\afterlife_world\emmerick_r7'
$fixture=R5Within (Join-Path $audit ('fixture_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))) $workspace
$game=Join-Path $fixture 'game';$report=Join-Path $fixture 'audit'
$actual='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$expected=[ordered]@{}
foreach($name in @('install_receipt.json','population_r2\install_receipt.json','idles_r3\install_receipt.json','faces_r5\install_receipt.json','booth_r6\install_receipt.json')){
 $r=Get-Content -LiteralPath (Join-Path $workspace ('research\afterlife_world\'+$name)) -Raw|ConvertFrom-Json
 foreach($file in $r.files){$expected[$file.relative.Replace('\','/')]=$file.sha256}
}
foreach($p in $expected.Keys){
 $from=R5Within (Join-Path $actual $p) $actual;R5Match $from $expected[$p]
 $to=R5Within (Join-Path $game $p) $game;New-Item -ItemType Directory -Force (Split-Path $to)|Out-Null;Copy-Item -LiteralPath $from -Destination $to
}
New-Item -ItemType Directory -Force (Join-Path $game 'r6\cache')|Out-Null
New-Item -ItemType File (Join-Path $game 'r6\cache\final.redscripts')|Out-Null
$deploy=Join-Path $PSScriptRoot 'deploy_afterlife_emmerick_r7.ps1'
& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $report -Mode ValidateInstall
foreach($p in $expected.Keys){R5Match (Join-Path $game $p) $expected[$p]}
& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $report -Mode Install
# Repeated install must fail before any mutation.
$refused=$false
try{& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $report -Mode Install}catch{$refused=$true}
if(-not $refused){throw 'Repeated install not rejected'}
& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $report -Mode ValidateRollback
& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $report -Mode Rollback
foreach($p in $expected.Keys){R5Match (Join-Path $game $p) $expected[$p];R5Match (Join-Path $actual $p) $expected[$p]}
$result=@{status='PASS_R7_WORKSPACE_REPLACEMENT_ROLLBACK';fixture=$fixture;replacements=1;additions=0;repeat_install_rejected=$refused;restored_baseline_files=$expected.Count;actual_game_writes=0;deployment_sha256=(R5Hash $deploy);helpers_sha256=(R5Hash (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1'));tests_sha256=(R5Hash (Join-Path $audit 'tests.json'))}
R5Json (Join-Path $audit 'deployment_tests.json') $result;$result|ConvertTo-Json
