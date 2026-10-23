param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),[ValidateSet('OrdinaryBars','CPZFood02','Claire','SpecialServices','StoryZane','StoryServices','StoryEight')][string]$CohortKind='OrdinaryBars')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$scope='b0_ordinary_bars';$package='B0_OrdinaryBars';$count=71
if($CohortKind -eq 'CPZFood02'){$scope='b0_cpz_food02';$package='B0_CPZFood02';$count=75}
if($CohortKind -eq 'Claire'){$scope='b0_claire';$package='B0_Claire';$count=79}
if($CohortKind -eq 'SpecialServices'){$scope='b0_special_services';$package='B0_SpecialServices';$count=83}
if($CohortKind -eq 'StoryZane'){$scope='b0_story_zane';$package='B0_StoryZane';$count=87}
if($CohortKind -eq 'StoryServices'){$scope='b0_story_services';$package='B0_StoryServices';$count=91}
if($CohortKind -eq 'StoryEight'){$scope='b0_story_eight';$package='B0_StoryEight';$count=95}
$dir=Join-Path $WorkspaceRoot ("build\$package\fixtures\"+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $dir -Force | Out-Null
$script=Join-Path $PSScriptRoot 'install_b0_ordinary_bars.ps1'
$baseline=Get-Content -LiteralPath (Join-Path $WorkspaceRoot 'build\RestorationBaseline_R1\manifest.json') -Raw|ConvertFrom-Json
$rejected=$false
try{& $script -GameRoot $dir -Fixture -PreflightOnly -CohortKind $CohortKind}catch{$rejected=$_.Exception.Message -like 'Baseline file missing*'}
if(-not $rejected){throw 'Missing baseline was not rejected'}
foreach($f in $baseline.files){
  $target=Join-Path $dir $f.path
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target)|Out-Null
  Copy-Item -LiteralPath (Join-Path (Join-Path $WorkspaceRoot 'build\RestorationBaseline_R1\game') $f.path) -Destination $target
}
if($CohortKind -in @('CPZFood02','Claire','SpecialServices','StoryZane','StoryServices','StoryEight')){
  $bars=Get-Content -LiteralPath (Join-Path $WorkspaceRoot 'research\b0_ordinary_bars\validation\install_receipt.json') -Raw|ConvertFrom-Json
  foreach($f in $bars.files){
    $target=Join-Path $dir $f.path
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target)|Out-Null
    Copy-Item -LiteralPath $f.source -Destination $target
  }
  $baseline.files=@($baseline.files)+@($bars.files)
}
if($CohortKind -in @('Claire','SpecialServices','StoryZane','StoryServices','StoryEight')){
  $food=Get-Content -LiteralPath (Join-Path $WorkspaceRoot 'research\b0_cpz_food02\validation\install_receipt.json') -Raw|ConvertFrom-Json
  foreach($f in $food.files){
    $target=Join-Path $dir $f.path
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target)|Out-Null
    Copy-Item -LiteralPath $f.source -Destination $target
  }
  $baseline.files=@($baseline.files)+@($food.files)
}
if($CohortKind -in @('SpecialServices','StoryZane','StoryServices','StoryEight')){
  $claire=Get-Content -LiteralPath (Join-Path $WorkspaceRoot 'research\b0_claire\validation\install_receipt.json') -Raw|ConvertFrom-Json
  foreach($f in $claire.files){
    $target=Join-Path $dir $f.path
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target)|Out-Null
    Copy-Item -LiteralPath $f.source -Destination $target
  }
  $baseline.files=@($baseline.files)+@($claire.files)
}
if($CohortKind -in @('StoryZane','StoryServices','StoryEight')){
  $special=Get-Content -LiteralPath (Join-Path $WorkspaceRoot 'research\b0_special_services\validation\install_receipt.json') -Raw|ConvertFrom-Json
  foreach($f in $special.files){
    $target=Join-Path $dir $f.path
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target)|Out-Null
    Copy-Item -LiteralPath $f.source -Destination $target
  }
  $baseline.files=@($baseline.files)+@($special.files)
}
if($CohortKind -in @('StoryServices','StoryEight')){
  $zane=Get-Content -LiteralPath (Join-Path $WorkspaceRoot 'research\b0_story_zane\validation\install_receipt.json') -Raw|ConvertFrom-Json
  foreach($f in $zane.files){
    $target=Join-Path $dir $f.path
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target)|Out-Null
    Copy-Item -LiteralPath $f.source -Destination $target
  }
  $baseline.files=@($baseline.files)+@($zane.files)
}
if($CohortKind -eq 'StoryEight'){
  $s3=Get-Content -LiteralPath (Join-Path $WorkspaceRoot 'research\b0_story_services\validation\install_receipt.json') -Raw|ConvertFrom-Json
  foreach($f in $s3.files){
    $target=Join-Path $dir $f.path
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target)|Out-Null
    Copy-Item -LiteralPath $f.source -Destination $target
  }
  $baseline.files=@($baseline.files)+@($s3.files)
}
& $script -GameRoot $dir -Fixture -PreflightOnly -CohortKind $CohortKind
& $script -GameRoot $dir -Fixture -CohortKind $CohortKind
$receipt=Get-Content -LiteralPath (Join-Path $dir 'fixture_receipt.json') -Raw|ConvertFrom-Json
if($receipt.files.Count -ne 4 -or $receipt.baselineFilesUnchanged -ne $count){throw 'Fixture receipt mismatch'}
foreach($f in $receipt.files){if((Get-FileHash -LiteralPath $f.target).Hash -ne $f.sha256){throw 'Fixture hash mismatch'}}
$rejected=$false
try{& $script -GameRoot $dir -Fixture -PreflightOnly -CohortKind $CohortKind}catch{$rejected=$_.Exception.Message -like 'Existing or unsafe target*'}
if(-not $rejected){throw 'Existing target was not rejected'}
foreach($f in $baseline.files){if((Get-FileHash -LiteralPath (Join-Path $dir $f.path)).Hash -ne $f.sha256){throw 'Baseline changed'}}
$report=[ordered]@{status='PASS';installer_sha256=(Get-FileHash -LiteralPath $script).Hash;fixture=$dir;protectedFiles=$count;checks=@('missing baseline refused','protected hashes checked','four new files installed','existing target refused','protected hashes unchanged');live=$false}
[IO.File]::WriteAllText((Join-Path $WorkspaceRoot "research\$scope\validation\installer_tests.json"),($report|ConvertTo-Json -Depth 4))
'PASS: isolated additive installation fixture; no game files touched'
