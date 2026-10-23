param(
  [string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),
  [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
  [switch]$PreflightOnly,
  [switch]$Fixture,
  [ValidateSet('OrdinaryBars','CPZFood02','Claire','SpecialServices','StoryZane','StoryServices','StoryEight')][string]$CohortKind='OrdinaryBars'
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$scope='b0_ordinary_bars';$package='B0_OrdinaryBars';$module='PTFR_B0_OrdinaryBars';$driver='OrdinaryBarDriver';$owners=4;$protectedCount=71
if($CohortKind -eq 'CPZFood02'){$scope='b0_cpz_food02';$package='B0_CPZFood02';$module='PTFR_B0_CPZFood02';$driver='CPZFood02Driver';$owners=1;$protectedCount=75}
if($CohortKind -eq 'Claire'){$scope='b0_claire';$package='B0_Claire';$module='PTFR_B0_Claire';$driver='ClaireDriver';$owners=1;$protectedCount=79}
if($CohortKind -eq 'SpecialServices'){$scope='b0_special_services';$package='B0_SpecialServices';$module='PTFR_B0_SpecialServices';$driver='SpecialServiceDriver';$owners=19;$protectedCount=83}
if($CohortKind -eq 'StoryZane'){$scope='b0_story_zane';$package='B0_StoryZane';$module='PTFR_B0_StoryZane';$driver='ZaneDriver';$owners=1;$protectedCount=87}
if($CohortKind -eq 'StoryServices'){$scope='b0_story_services';$package='B0_StoryServices';$module='PTFR_B0_StoryServices';$driver='StoryServiceDriver';$owners=4;$protectedCount=91}
if($CohortKind -eq 'StoryEight'){$scope='b0_story_eight';$package='B0_StoryEight';$module='PTFR_B0_StoryEight';$driver='StoryEightDriver';$owners=8;$protectedCount=95}
$game=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
$realGame='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
if($Fixture){
  $fixtureRoot=[IO.Path]::GetFullPath((Join-Path $WorkspaceRoot "build\$package\fixtures"))+'\'
  if(-not $game.StartsWith($fixtureRoot,[StringComparison]::OrdinalIgnoreCase)){throw 'Fixture path outside bounded workspace fixture directory'}
}elseif($game -ne $realGame){throw 'Unexpected real game target'}
if(@(Get-Process -Name Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Close Cyberpunk before installing'}
$val=Join-Path $WorkspaceRoot "research\$scope\validation"
$tests=Get-Content -LiteralPath (Join-Path $val 'tests.json') -Raw | ConvertFrom-Json
$manifest=Get-Content -LiteralPath (Join-Path $val 'build_manifest.json') -Raw | ConvertFrom-Json
$baseline=Get-Content -LiteralPath (Join-Path $WorkspaceRoot 'build\RestorationBaseline_R1\manifest.json') -Raw | ConvertFrom-Json
if($CohortKind -in @('CPZFood02','Claire','SpecialServices','StoryZane','StoryServices','StoryEight')){
  $barsReceipt=Get-Content -LiteralPath (Join-Path $WorkspaceRoot 'research\b0_ordinary_bars\validation\install_receipt.json') -Raw | ConvertFrom-Json
  if($barsReceipt.files.Count -ne 4){throw 'Unexpected bar protection inventory'}
  $baseline.files=@($baseline.files)+@($barsReceipt.files)
}
if($CohortKind -in @('Claire','SpecialServices','StoryZane','StoryServices','StoryEight')){
  $foodReceipt=Get-Content -LiteralPath (Join-Path $WorkspaceRoot 'research\b0_cpz_food02\validation\install_receipt.json') -Raw | ConvertFrom-Json
  if($foodReceipt.files.Count -ne 4){throw 'Unexpected food02 protection inventory'}
  $baseline.files=@($baseline.files)+@($foodReceipt.files)
}
if($CohortKind -in @('SpecialServices','StoryZane','StoryServices','StoryEight')){
  $claireReceipt=Get-Content -LiteralPath (Join-Path $WorkspaceRoot 'research\b0_claire\validation\install_receipt.json') -Raw | ConvertFrom-Json
  if($claireReceipt.files.Count -ne 4){throw 'Unexpected Claire protection inventory'}
  $baseline.files=@($baseline.files)+@($claireReceipt.files)
}
if($CohortKind -in @('StoryZane','StoryServices','StoryEight')){
  $special=Get-Content -LiteralPath (Join-Path $WorkspaceRoot 'research\b0_special_services\validation\install_receipt.json') -Raw | ConvertFrom-Json
  if($special.files.Count -ne 4){throw 'Unexpected S1 protection inventory'}
  $baseline.files=@($baseline.files)+@($special.files)
}
if($CohortKind -in @('StoryServices','StoryEight')){
  $zane=Get-Content -LiteralPath (Join-Path $WorkspaceRoot 'research\b0_story_zane\validation\install_receipt.json') -Raw|ConvertFrom-Json
  if($zane.files.Count -ne 4){throw 'Unexpected S2 protection inventory'}
  $baseline.files=@($baseline.files)+@($zane.files)
}
if($CohortKind -eq 'StoryZane'){$resourceCount=2;$archiveHash=$manifest.archive_sha256}
elseif($CohortKind -eq 'StoryServices'){$resourceCount=6;$archiveHash=$manifest.sha256}
elseif($CohortKind -eq 'StoryEight'){
  $s3=Get-Content -LiteralPath (Join-Path $WorkspaceRoot 'research\b0_story_services\validation\install_receipt.json') -Raw|ConvertFrom-Json
  if($s3.files.Count -ne 4){throw 'Unexpected S3 protection inventory'}
  $baseline.files=@($baseline.files)+@($s3.files)
  $resourceCount=16;$archiveHash=$manifest.sha256
}
else{$resourceCount=$owners;$archiveHash=$manifest.sha256}
if($tests.status -ne 'PASS' -or $tests.owners -ne $owners -or $manifest.resources.Count -ne $resourceCount -or $tests.archive_sha256 -ne $archiveHash){throw 'Validation mismatch'}
if(-not $Fixture -and -not $PreflightOnly){
  $it=Get-Content -LiteralPath (Join-Path $val 'installer_tests.json') -Raw | ConvertFrom-Json
  if($it.status -ne 'PASS' -or $it.installer_sha256 -ne (Get-FileHash -LiteralPath $PSCommandPath).Hash){throw 'Installer fixture tests missing/stale'}
}
function Check-Baseline {
  if($baseline.files.Count -ne $protectedCount){throw 'Unexpected baseline inventory'}
  foreach($f in $baseline.files){
    $path=[IO.Path]::GetFullPath((Join-Path $game $f.path))
    if(-not $path.StartsWith($game+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Unsafe baseline path'}
    if(-not (Test-Path -LiteralPath $path) -or (Get-FileHash -LiteralPath $path).Hash -ne $f.sha256){throw "Baseline file missing or changed: $($f.path)"}
  }
}
Check-Baseline
$items=@(
  [pscustomobject]@{source="build\$package\TowerContinued_$package.archive";path="archive\pc\mod\TowerContinued_$package.archive";sha256=$tests.archive_sha256},
  [pscustomobject]@{source="archive\$scope\TowerContinued_$package.archive.xl";path="archive\pc\mod\TowerContinued_$package.archive.xl";sha256=$tests.xl_sha256},
  [pscustomobject]@{source="redscript\$module\$driver.reds";path="r6\scripts\$module\$driver.reds";sha256=$tests.driver_sha256},
  [pscustomobject]@{source="diagnostics\$module\init.lua";path="bin\x64\plugins\cyber_engine_tweaks\mods\$module\init.lua";sha256=$tests.controller_sha256}
)
foreach($i in $items){
  $target=[IO.Path]::GetFullPath((Join-Path $game $i.path))
  if(-not $target.StartsWith($game+'\',[StringComparison]::OrdinalIgnoreCase) -or (Test-Path -LiteralPath $target)){throw "Existing or unsafe target: $target"}
  $i.source=Join-Path $WorkspaceRoot $i.source
  if((Get-FileHash -LiteralPath $i.source).Hash -ne $i.sha256){throw 'Source changed since tests'}
  $i|Add-Member -NotePropertyName target -NotePropertyValue $target
}
$xl=Get-Content -LiteralPath $items[1].source -Raw
if([regex]::Matches($xl,'- path:').Count -ne $owners -or [regex]::Matches($xl,'parent: ep1\\quest\\ep1.quest').Count -ne $owners){throw 'Registration scope changed'}
foreach($p in $manifest.resources){
  $sceneException=$CohortKind -eq 'StoryZane' -and $p -eq 'towercontinued\b0_story_zane\zane_service.scene'
  if($CohortKind -eq 'StoryServices' -and $p -in @('towercontinued\b0_story_services\fred.scene','towercontinued\b0_story_services\charles.scene')){$sceneException=$true}
  if($CohortKind -eq 'StoryEight' -and $p -match '^towercontinued\\b0_story_eight\\(nix|yoko|mateo|fingers|viktor|karim|ronald|bill)\.scene$'){$sceneException=$true}
  if(-not $p.StartsWith('towercontinued\'+$scope+'\') -or (-not $xl.Contains($p) -and -not $sceneException)){throw 'Unexpected resource'}
}
if($PreflightOnly){"PREFLIGHT_OK: four new files; $protectedCount protected hashes match";return}
if(@(Get-Process -Name Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Game started during preflight'}
$copied=[Collections.Generic.List[string]]::new()
try{
  foreach($i in $items){
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $i.target)|Out-Null
    # CreateNew refuses a file appearing after preflight; never overwrite.
    $inputStream=[IO.File]::OpenRead($i.source)
    try{
      $outputStream=[IO.File]::Open($i.target,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write)
      $copied.Add($i.target)
      try{$inputStream.CopyTo($outputStream)}finally{$outputStream.Dispose()}
    }finally{$inputStream.Dispose()}
    if((Get-FileHash -LiteralPath $i.target).Hash -ne $i.sha256){throw 'Installed hash mismatch'}
  }
  Check-Baseline
}catch{
  foreach($p in $copied){
    if(([IO.Path]::GetFullPath($p)).StartsWith($game+'\',[StringComparison]::OrdinalIgnoreCase)){Remove-Item -LiteralPath $p}
  }
  throw
}
$receipt=[ordered]@{status="INSTALLED_AUTOMATIC_$CohortKind";owners=$owners;utc=(Get-Date).ToUniversalTime().ToString('o');baselineFilesUnchanged=$protectedCount;overwrites=0;files=$items;savesModified=$false;storyFactsForced=$false;live='NOT_TESTED'}
$receiptPath=if($Fixture){Join-Path $game 'fixture_receipt.json'}else{Join-Path $val 'install_receipt.json'}
[IO.File]::WriteAllText($receiptPath,($receipt|ConvertTo-Json -Depth 6))
"INSTALLED: four additive files; $protectedCount previous files unchanged; live test pending"
