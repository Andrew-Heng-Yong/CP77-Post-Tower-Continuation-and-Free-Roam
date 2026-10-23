param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
# Exercise deployment and recovery ONLY inside a newly-created workspace fixture.
# The actual game is read/hash checked, never passed as a mutation destination.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\')
$audit=Join-Path $workspace 'research\afterlife_world\population_r2'
$r1=Get-Content (Join-Path $workspace 'research\afterlife_world\install_receipt.json') -Raw|ConvertFrom-Json
$m=Get-Content (Join-Path $audit 'manifest.json') -Raw|ConvertFrom-Json -Depth 50
$t=Get-Content (Join-Path $audit 'tests.json') -Raw|ConvertFrom-Json
function Hash([string]$p){return (Get-FileHash -LiteralPath $p).Hash}
function Within([string]$p,[string]$root){$p=[IO.Path]::GetFullPath($p);if(-not $p.StartsWith($root+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Fixture escaped workspace'};return $p}
function CopyFixture([string]$from,[string]$to){$to=Within $to $script:fixture;New-Item -ItemType Directory -Force (Split-Path $to)|Out-Null;Copy-Item -LiteralPath $from -Destination $to}
function JsonFixture([string]$path,$value){$path=Within $path $script:fixture;New-Item -ItemType Directory -Force (Split-Path $path)|Out-Null;[IO.File]::WriteAllText($path,($value|ConvertTo-Json -Depth 60),[Text.UTF8Encoding]::new($false))}
$fixture=Within (Join-Path $workspace ('build\AfterlifePopulationR2\deployment_fixture_'+[Guid]::NewGuid().ToString('N'))) $workspace
New-Item -ItemType Directory -Path $fixture|Out-Null
$fakeGame=Within (Join-Path $fixture 'game') $fixture
$fakeWork=Within (Join-Path $fixture 'workspace') $fixture
$fakeAudit=Join-Path $fakeWork 'research\afterlife_world\population_r2'
$actualHashes=[ordered]@{}
foreach($p in $r1.files){$from=Join-Path $r1.game_root $p.relative;$actualHashes[$from]=Hash $from;if($actualHashes[$from] -ne $p.sha256){throw 'Installed R1 drifted'};CopyFixture $from (Join-Path $fakeGame $p.relative)}
foreach($rel in @('r6\cache','r6\tweaks')){New-Item -ItemType Directory -Force (Join-Path $fakeGame $rel)|Out-Null}
[IO.File]::WriteAllText((Within (Join-Path $fakeGame 'r6\cache\final.redscripts') $fixture),'Fixture marker, not executable game data.')
$candidate=Join-Path $fakeWork 'candidate\TowerContinued_AfterlifeR1.archive'
CopyFixture $m.archive $candidate;CopyFixture ($m.archive+'.xl') ($candidate+'.xl')
foreach($name in @('build_afterlife_population_r2.ps1','test_afterlife_population_r2.py')){CopyFixture (Join-Path $workspace ('tools\'+$name)) (Join-Path $fakeWork ('tools\'+$name))}
$m.archive=$candidate
JsonFixture (Join-Path $fakeAudit 'manifest.json') $m
$t.manifest_sha256=Hash (Join-Path $fakeAudit 'manifest.json')
JsonFixture (Join-Path $fakeAudit 'tests.json') $t
JsonFixture (Join-Path $fakeWork 'research\afterlife_world\install_receipt.json') $r1
$installer=Join-Path $PSScriptRoot 'install_afterlife_population_r2.ps1'
$rollback=Join-Path $PSScriptRoot 'rollback_afterlife_population_r2.ps1'
$pre=& $installer -WorkspaceRoot $fakeWork -GameRoot $fakeGame -ValidateOnly|ConvertFrom-Json
if($pre.status -ne 'R2_PREFLIGHT_ONLY_GAME_UNCHANGED' -or $pre.protected_files -ne 4){throw 'Fixture preflight failed'}
foreach($p in $r1.files){if((Hash (Join-Path $fakeGame $p.relative)) -ne $p.sha256){throw 'Preflight modified fixture game'}}
$installed=& $installer -WorkspaceRoot $fakeWork -GameRoot $fakeGame -Install|ConvertFrom-Json
if($installed.replacements -ne 2 -or $installed.additions -ne 0 -or $installed.protected_files -ne 4){throw 'Fixture install scope failed'}
$check=& $rollback -WorkspaceRoot $fakeWork -ValidateOnly|ConvertFrom-Json
if($check.status -ne 'R2_ROLLBACK_PREFLIGHT_PASS'){throw 'Fixture rollback preflight failed'}
$restored=& $rollback -WorkspaceRoot $fakeWork -Restore|ConvertFrom-Json
if($restored.restored -ne 2){throw 'Fixture restore failed'}
foreach($p in $r1.files){if((Hash (Join-Path $fakeGame $p.relative)) -ne $p.sha256){throw 'Fixture did not return to exact R1 bytes'}}
foreach($p in $actualHashes.Keys){if((Hash $p) -ne $actualHashes[$p]){throw 'Actual game changed during fixture test'}}
if(Test-Path -LiteralPath (Join-Path $audit 'install_receipt.json')){throw 'Unexpected actual R2 receipt; stop and reconcile'}
$report=@{status='PASS_DEPLOYMENT_WORKSPACE_FIXTURE_ONLY';fixture=$fixture;fixture_replacements=2;fixture_protected=4;fixture_rollback_restored=2;actual_game_writes=0;actual_six_r1_hashes_unchanged=$true;installer_sha256=(Hash $installer);rollback_sha256=(Hash $rollback);archive_sha256=$m.sha256;xl_sha256=$m.xl_sha256}
[IO.File]::WriteAllText((Join-Path $audit 'deployment_tests.json'),($report|ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false));$report|ConvertTo-Json -Depth 6
