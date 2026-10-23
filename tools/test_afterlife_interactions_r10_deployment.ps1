param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
. (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1')
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\')
$audit=Join-Path $workspace 'research\afterlife_world\interactions_r10'
$fixture=R5Within (Join-Path $audit ('fixture_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))) $workspace
$game=Join-Path $fixture 'game';$report=Join-Path $fixture 'audit'
$actual='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$expected=[ordered]@{}
foreach($name in @('install_receipt.json','population_r2\install_receipt.json','idles_r3\install_receipt.json','faces_r5\install_receipt.json','booth_r6\install_receipt.json','emmerick_r7\install_receipt.json','interactions_r8\install_receipt.json','interactions_r9\install_receipt.json')){
 $r=Get-Content -LiteralPath (Join-Path $workspace ('research\afterlife_world\'+$name)) -Raw|ConvertFrom-Json
 foreach($file in $r.files){$expected[$file.relative.Replace('\','/')]=$file.sha256}
}
foreach($p in $expected.Keys){
 $from=R5Within (Join-Path $actual $p) $actual;R5Match $from $expected[$p]
 $to=R5Within (Join-Path $game $p) $game;New-Item -ItemType Directory -Force (Split-Path $to)|Out-Null;Copy-Item -LiteralPath $from -Destination $to
}
New-Item -ItemType Directory -Force (Join-Path $game 'r6\cache')|Out-Null
New-Item -ItemType File (Join-Path $game 'r6\cache\final.redscripts')|Out-Null
$deploy=Join-Path $PSScriptRoot 'deploy_afterlife_interactions_r10.ps1'
$tests=Get-Content -LiteralPath (Join-Path $audit 'tests.json') -Raw|ConvertFrom-Json
& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $report -Mode ValidateInstall
foreach($p in $expected.Keys){R5Match (Join-Path $game $p) $expected[$p]}
& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $report -Mode Install
foreach($file in $tests.files){R5Match (Join-Path $game $file.relative) $file.sha256}
$refused=$false
try{& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $report -Mode Install}catch{$refused=$true}
if(-not $refused){throw 'Repeated install not rejected'}
& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $report -Mode ValidateRollback
$receiptPath=Join-Path $report 'install_receipt.json';$receiptText=[IO.File]::ReadAllText($receiptPath)
$r=$receiptText|ConvertFrom-Json;$r.files[0].relative='archive/pc/mod/NotInScope.archive'
R5Json $receiptPath $r
$scopeRefused=$false
try{& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $report -Mode ValidateRollback}catch{$scopeRefused=$true}
[IO.File]::WriteAllText($receiptPath,$receiptText,[Text.UTF8Encoding]::new($false))
if(-not $scopeRefused){throw 'Invalid scope not rejected'}
$r=$receiptText|ConvertFrom-Json;$r.files[0].sha256='0'*64
R5Json $receiptPath $r
$hashRefused=$false
try{& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $report -Mode ValidateRollback}catch{$hashRefused=$true}
[IO.File]::WriteAllText($receiptPath,$receiptText,[Text.UTF8Encoding]::new($false))
if(-not $hashRefused){throw 'Invalid receipt hash not rejected'}
& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $report -Mode Rollback
# Begin from the four-file installed state, then apply only the three safe
# interaction rollback targets. Diagnostics and face suspension remain R10.
$baseline=[ordered]@{};foreach($p in $expected.Keys){$baseline[$p]=$expected[$p]}
foreach($file in $tests.files){$baseline[$file.relative]=$file.sha256}
foreach($file in $tests.safe_rollback){$baseline[$file.relative]=$file.sha256}
foreach($p in $baseline.Keys){
 if($baseline[$p]){R5Match (Join-Path $game $p) $baseline[$p]}
 elseif(Test-Path -LiteralPath (Join-Path $game $p)){throw 'Interaction driver still exists'}
 R5Match (Join-Path $actual $p) $expected[$p]
}
$retained=@('bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_Afterlife_Behavior_Audit/init.lua','r6/scripts/PTFR_Afterlife_Faces_R5/AfterlifeFacesR5.reds')
foreach($p in $retained){
 $file=@($tests.files|Where-Object relative -eq $p)[0]
 R5Match (Join-Path $game $p) $file.sha256
 if($file.sha256 -eq $expected[$p]){throw 'Safety replacement was not changed'}
}
$rolled=Get-Content -LiteralPath (Join-Path $report 'rollback_receipt.json') -Raw|ConvertFrom-Json
if(@($rolled.files).Count -ne 3 -or @($rolled.files|Where-Object {$_.relative -in $retained}).Count){throw 'Safe rollback unexpectedly included safety replacements'}
$removed=@($rolled.files|Where-Object recovered)
if($removed.Count -ne 1){throw 'Expected exactly one recoverable runtime removal'}
R5Match $removed[0].recovered $removed[0].before_sha256
$rollbackRefused=$false
try{& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $report -Mode Rollback}catch{$rollbackRefused=$true}
if(-not $rollbackRefused){throw 'Repeated rollback not rejected'}
$result=@{status='PASS_R10_WORKSPACE_INSTALL_SAFE_ROLLBACK';fixture=$fixture;replacements=4;additions=0;repeat_install_rejected=$refused;repeat_rollback_rejected=$rollbackRefused;scope_corruption_rejected=$scopeRefused;hash_corruption_rejected=$hashRefused;runtime_recoverable=$true;safe_rollback_replacements=2;safe_rollback_removals=1;safety_replacements_retained=$true;retained_safety_paths=$retained;verified_post_rollback_present_files=12;unsafe_r8_r9_not_restored=$true;actual_game_writes=0;deployment_sha256=(R5Hash $deploy);fixture_sha256=(R5Hash $PSCommandPath);helpers_sha256=(R5Hash (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1'));tests_sha256=(R5Hash (Join-Path $audit 'tests.json'))}
R5Json (Join-Path $audit 'deployment_tests.json') $result;$result|ConvertTo-Json
