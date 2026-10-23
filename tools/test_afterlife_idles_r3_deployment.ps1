param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
# Exercise real deployment scripts only in an isolated workspace fake game.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$audit=Join-Path $WorkspaceRoot 'research\afterlife_world\idles_r3'
$fixture=Join-Path $WorkspaceRoot ('build\AfterlifeIdlesR3\deployment_fixture_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))
$fake=Join-Path $fixture 'game';$ws=Join-Path $fixture 'workspace'
function CopyFile([string]$from,[string]$to){New-Item -ItemType Directory -Force (Split-Path $to)|Out-Null;Copy-Item -LiteralPath $from -Destination $to}
function WriteJson([string]$p,$v){New-Item -ItemType Directory -Force (Split-Path $p)|Out-Null;[IO.File]::WriteAllText($p,($v|ConvertTo-Json -Depth 50),[Text.UTF8Encoding]::new($false))}
$m=Get-Content (Join-Path $audit 'manifest.json') -Raw|ConvertFrom-Json -Depth 40
$t=Get-Content (Join-Path $audit 'tests.json') -Raw|ConvertFrom-Json
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$expected=[ordered]@{}
foreach($relative in @('research\afterlife_world\install_receipt.json','research\afterlife_world\population_r2\install_receipt.json')){
 CopyFile (Join-Path $WorkspaceRoot $relative) (Join-Path $ws $relative)
 $r=Get-Content (Join-Path $WorkspaceRoot $relative) -Raw|ConvertFrom-Json
 foreach($f in $r.files){$expected[$f.relative]=$f.sha256}
}
foreach($p in $expected.Keys){CopyFile (Join-Path $game $p) (Join-Path $fake $p)}
CopyFile (Join-Path $game 'r6\cache\final.redscripts') (Join-Path $fake 'r6\cache\final.redscripts')
New-Item -ItemType Directory -Force (Join-Path $fake 'r6\tweaks')|Out-Null
foreach($p in @('tools\build_afterlife_idles_r3.ps1','tools\test_afterlife_idles_r3.py','redscript\PTFR_Afterlife_Idles_R3\AfterlifeIdlesR3.reds','diagnostics\PTFR_Afterlife_Behavior_Audit\init.lua')){CopyFile (Join-Path $WorkspaceRoot $p) (Join-Path $ws $p)}
$newArchive=Join-Path $ws 'candidate\TowerContinued_AfterlifeIdlesR3.archive'
CopyFile $m.archive $newArchive;CopyFile ($m.archive+'.xl') ($newArchive+'.xl');$m.archive=$newArchive
$ma=Join-Path $ws 'research\afterlife_world\idles_r3\manifest.json';WriteJson $ma $m
$t.manifest_sha256=(Get-FileHash $ma).Hash
WriteJson (Join-Path $ws 'research\afterlife_world\idles_r3\tests.json') $t
$installer=Join-Path $WorkspaceRoot 'tools\install_afterlife_idles_r3.ps1';$rollback=Join-Path $WorkspaceRoot 'tools\rollback_afterlife_idles_r3.ps1'
& $installer -WorkspaceRoot $ws -GameRoot $fake -ValidateOnly|Out-Null
$target=Join-Path $fake 'archive\pc\mod\TowerContinued_AfterlifeIdlesR3.archive'
if(Test-Path -LiteralPath $target){throw 'Preflight wrote a file'}
& $installer -WorkspaceRoot $ws -GameRoot $fake -Install|Out-Null
& $rollback -WorkspaceRoot $ws -ValidateOnly|Out-Null
if((Get-FileHash $target).Hash -ne $m.sha256){throw 'Fixture install hash mismatch'}
$blocked=$false;try{& $installer -WorkspaceRoot $ws -GameRoot $fake -Install|Out-Null}catch{$blocked=$true};if(-not $blocked){throw 'Duplicate install accepted'}
& $rollback -WorkspaceRoot $ws -Restore|Out-Null
if(Test-Path -LiteralPath $target){throw 'Fixture rollback left archive'}
foreach($p in $expected.Keys){if((Get-FileHash (Join-Path $fake $p)).Hash -ne $expected[$p]){throw 'Fixture changed accepted file'}}
$result=@{status='PASS_R3_WORKSPACE_FIXTURE_ONLY_NO_REAL_GAME_WRITES';fixture=$fixture;additions=4;replacements=0;protected_baseline_files=$expected.Count;default_preflight_no_writes=$true;duplicate_install_rejected=$true;recoverable_rollback=$true;installer_sha256=(Get-FileHash $installer).Hash;rollback_sha256=(Get-FileHash $rollback).Hash}
WriteJson (Join-Path $audit 'deployment_tests.json') $result;$result|ConvertTo-Json
