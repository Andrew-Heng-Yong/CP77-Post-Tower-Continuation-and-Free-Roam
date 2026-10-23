param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
. (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1')
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\')
$audit=Join-Path $workspace 'research\afterlife_world\faces_r5'
$fixture=R5Within (Join-Path $audit ('fixture_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))) $workspace
$game=Join-Path $fixture 'game';$report=Join-Path $fixture 'audit'
$actual='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$expected=[ordered]@{}
foreach($name in @('install_receipt.json','population_r2\install_receipt.json','idles_r3\install_receipt.json')){
 $receipt=Get-Content -LiteralPath (Join-Path $workspace ('research\afterlife_world\'+$name)) -Raw|ConvertFrom-Json
 foreach($file in $receipt.files){$expected[$file.relative]=$file.sha256}
}
foreach($path in $expected.Keys){
 $source=R5Within (Join-Path $actual $path) $actual;R5Match $source $expected[$path]
 $target=R5Within (Join-Path $game $path) $game
 New-Item -ItemType Directory -Force (Split-Path $target)|Out-Null
 Copy-Item -LiteralPath $source -Destination $target
}
New-Item -ItemType Directory -Force (Join-Path $game 'r6\cache')|Out-Null
New-Item -ItemType File (Join-Path $game 'r6\cache\final.redscripts')|Out-Null
& (Join-Path $PSScriptRoot 'install_afterlife_faces_r5.ps1') -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $report -ValidateOnly
foreach($path in R5Scope){if(Test-Path -LiteralPath (Join-Path $game $path)){throw 'Validation wrote a file'}}
& (Join-Path $PSScriptRoot 'install_afterlife_faces_r5.ps1') -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $report -Install
& (Join-Path $PSScriptRoot 'rollback_afterlife_faces_r5.ps1') -WorkspaceRoot $workspace -AuditDirectory $report -ValidateOnly
# Modified destination blocks rollback rather than deleting another version.
$first=Join-Path $game (R5Scope)[0]
$bytes=[IO.File]::ReadAllBytes($first)
try{
 [IO.File]::AppendAllText($first,"`n// fixture mutation")
 $rejected=$false
 try{& (Join-Path $PSScriptRoot 'rollback_afterlife_faces_r5.ps1') -WorkspaceRoot $workspace -AuditDirectory $report -ValidateOnly}catch{$rejected=$true}
 if(-not $rejected){throw 'Changed-file rollback not rejected'}
}finally{[IO.File]::WriteAllBytes($first,$bytes)}
& (Join-Path $PSScriptRoot 'rollback_afterlife_faces_r5.ps1') -WorkspaceRoot $workspace -AuditDirectory $report -Rollback
foreach($path in R5Scope){if(Test-Path -LiteralPath (Join-Path $game $path)){throw 'Rollback left a payload'}}
foreach($path in $expected.Keys){R5Match (Join-Path $game $path) $expected[$path];R5Match (Join-Path $actual $path) $expected[$path]}
$result=@{status='PASS_R5_WORKSPACE_INSTALL_ROLLBACK';fixture=$fixture;additions=2;replacements=0;prior_files_unchanged=$expected.Count;modified_file_refused=$true;actual_game_writes=0;tests_sha256=(R5Hash (Join-Path $audit 'tests.json'));installer_sha256=(R5Hash (Join-Path $PSScriptRoot 'install_afterlife_faces_r5.ps1'));rollback_sha256=(R5Hash (Join-Path $PSScriptRoot 'rollback_afterlife_faces_r5.ps1'));helpers_sha256=(R5Hash (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1'))}
R5Json (Join-Path $audit 'deployment_tests.json') $result
$result|ConvertTo-Json
