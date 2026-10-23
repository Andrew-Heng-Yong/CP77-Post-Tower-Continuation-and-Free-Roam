param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
. (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1')
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\')
$audit=Join-Path $workspace 'research\afterlife_world\interactions_r11'
$fixture=R5Within (Join-Path $audit ('fixture_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))) $workspace
$game=Join-Path $fixture 'game';$report=Join-Path $fixture 'audit'
$actual='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$expected=[ordered]@{}
foreach($name in @('install_receipt.json','population_r2\install_receipt.json','idles_r3\install_receipt.json','faces_r5\install_receipt.json','booth_r6\install_receipt.json','emmerick_r7\install_receipt.json','interactions_r8\install_receipt.json','interactions_r9\install_receipt.json','interactions_r10\install_receipt.json')){
 $r=Get-Content -LiteralPath (Join-Path $workspace ('research\afterlife_world\'+$name)) -Raw|ConvertFrom-Json
 foreach($file in $r.files){$expected[$file.relative.Replace('\','/')]=$file.sha256}
}
foreach($p in $expected.Keys){
 $from=R5Within (Join-Path $actual $p) $actual;R5Match $from $expected[$p]
 $to=R5Within (Join-Path $game $p) $game;New-Item -ItemType Directory -Force (Split-Path $to)|Out-Null;Copy-Item -LiteralPath $from -Destination $to
}
New-Item -ItemType Directory -Force (Join-Path $game 'r6\cache')|Out-Null
New-Item -ItemType File (Join-Path $game 'r6\cache\final.redscripts')|Out-Null
$deploy=Join-Path $PSScriptRoot 'deploy_afterlife_interactions_r11.ps1'
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
$r=$receiptText|ConvertFrom-Json;$r.safe_rollback[0].sha256='0'*64
R5Json $receiptPath $r
$fallbackRefused=$false
try{& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $report -Mode ValidateRollback}catch{$fallbackRefused=$true}
[IO.File]::WriteAllText($receiptPath,$receiptText,[Text.UTF8Encoding]::new($false))
if(-not $fallbackRefused){throw 'Invalid fallback hash not rejected'}
& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $report -Mode Rollback
# Verify all13 predecessor receipt paths with only the three installs and two
# safe substitutions applied; face shim, diagnostics/XL/catalog remain intact.
$baseline=[ordered]@{};foreach($p in $expected.Keys){$baseline[$p]=$expected[$p]}
foreach($file in $tests.files){$baseline[$file.relative]=$file.sha256}
foreach($file in $tests.safe_rollback){$baseline[$file.relative]=$file.sha256}
foreach($p in $baseline.Keys){R5Match (Join-Path $game $p) $baseline[$p];R5Match (Join-Path $actual $p) $expected[$p]}
$faces='r6/scripts/PTFR_Afterlife_Faces_R5/AfterlifeFacesR5.reds'
$face=@($tests.files|Where-Object relative -eq $faces)[0]
R5Match (Join-Path $game $faces) $face.sha256
if($face.sha256 -eq $expected[$faces]){throw 'Retired face shim was not changed'}
$rolled=Get-Content -LiteralPath (Join-Path $report 'rollback_receipt.json') -Raw|ConvertFrom-Json
if(@($rolled.files).Count -ne 2 -or @($rolled.files|Where-Object relative -eq $faces).Count){throw 'Safe fallback changed the face shim'}
if(-not $rolled.retirements_preserved -or $rolled.additions -ne 0 -or $rolled.removals -ne 0){throw 'Unexpected rollback scope'}
foreach($file in $rolled.files){R5Match $file.backup $file.before_sha256}
$rollbackRefused=$false
try{& $deploy -WorkspaceRoot $workspace -GameRoot $game -AuditDirectory $report -Mode Rollback}catch{$rollbackRefused=$true}
if(-not $rollbackRefused){throw 'Repeated rollback not rejected'}
$result=@{status='PASS_R11_WORKSPACE_INSTALL_SAFE_ROLLBACK';fixture=$fixture;replacements=3;additions=0;removals=0;repeat_install_rejected=$refused;repeat_rollback_rejected=$rollbackRefused;scope_corruption_rejected=$scopeRefused;hash_corruption_rejected=$hashRefused;fallback_corruption_rejected=$fallbackRefused;safe_rollback_replacements=2;retirements_preserved=$true;verified_post_rollback_present_files=$baseline.Count;unsafe_r8_r9_not_restored=$true;actual_game_writes=0;deployment_sha256=(R5Hash $deploy);fixture_sha256=(R5Hash $PSCommandPath);helpers_sha256=(R5Hash (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1'));tests_sha256=(R5Hash (Join-Path $audit 'tests.json'))}
R5Json (Join-Path $audit 'deployment_tests.json') $result;$result|ConvertTo-Json
