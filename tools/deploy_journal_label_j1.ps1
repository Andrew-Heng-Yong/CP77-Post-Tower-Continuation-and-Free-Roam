param(
 [string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),
 [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
 [string]$AuditDirectory='',
 [ValidateSet('ValidateInstall','Install','ValidateRollback','Rollback')][string]$Mode='ValidateInstall'
)
. (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1')
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\');$root=Join-Path $workspace 'research\journal_label_j1'
$game=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\');$actual='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$fixture=$game.StartsWith($root+'\fixture_',[StringComparison]::OrdinalIgnoreCase)
if($game -ne $actual -and -not $fixture){throw 'Unsupported game root'}
$audit=if($AuditDirectory){R5Within $AuditDirectory $workspace}else{$root}
if($fixture -and (-not $AuditDirectory -or -not $audit.StartsWith((Split-Path -Parent $game)+'\',[StringComparison]::OrdinalIgnoreCase))){throw 'Fixture audit path mismatch'}
if(-not $fixture -and $AuditDirectory){throw 'Actual audit path must be canonical'}
$testsPath=Join-Path $root 'tests.json';$tests=Get-Content $testsPath -Raw|ConvertFrom-Json
if($tests.status -ne 'PASS_J1_UI_ONLY_OFFLINE_LIVE_PENDING' -or -not $tests.native_setup_preserved -or -not $tests.equipmentex_full_compile -or $tests.fact_writes -ne 0 -or $tests.journal_writes -ne 0 -or $tests.save_fields -ne 0){throw 'Current checks missing'}
$source='redscript/PTFR_JournalLabelJ1/JournalLabelJ1.reds';$relative='r6/scripts/PTFR_JournalLabelJ1/JournalLabelJ1.reds'
if(@($tests.files).Count -ne 1 -or $tests.files[0].source -ne $source -or $tests.files[0].relative -ne $relative){throw 'Wrong scope'}
$file=$tests.files[0];$sourcePath=R5Within (Join-Path $workspace $source) $workspace;$target=R5Within (Join-Path $game $relative) $game
R5Match $sourcePath $file.sha256
foreach($p in $tests.tools.PSObject.Properties){R5Match (R5Within (Join-Path $workspace $p.Name) $workspace) $p.Value}
$compilePath=Join-Path $root 'compile_result.json';R5Match $compilePath $tests.compile_sha256
if(-not $fixture){
 $dt=Get-Content (Join-Path $root 'deployment_tests.json') -Raw|ConvertFrom-Json
 if($dt.status -ne 'PASS_J1_DEPLOYMENT_FIXTURE' -or -not $dt.recoverable_rollback -or $dt.tests_sha256 -ne (R5Hash $testsPath) -or $dt.installer_sha256 -ne (R5Hash $PSCommandPath)){throw 'Current fixture checks missing'}
}
$protected=R5Snapshot $game @($target)
if(-not $fixture){
 $compile=Get-Content $compilePath -Raw|ConvertFrom-Json
 foreach($p in @($compile.protected.PSObject.Properties)+@($compile.dependencies.PSObject.Properties)){
  $path=R5Within $p.Name $game;R5Match $path $p.Value;$protected[$path]=$p.Value
 }
 foreach($folder in @('archive/pc/mod','red4ext/plugins','r6/scripts')){
  foreach($p in Get-ChildItem -LiteralPath (Join-Path $game $folder) -Recurse -File){if($p.FullName -ne $target -and $p.Extension -in @('.archive','.xl','.reds','.dll')){$protected[$p.FullName]=R5Hash $p.FullName}}
 }
}
$receiptPath=Join-Path $audit 'install_receipt.json'
if($Mode -in @('ValidateRollback','Rollback')){
 $receipt=Get-Content $receiptPath -Raw|ConvertFrom-Json
 if($receipt.status -ne 'INSTALLED_J1_UI_LABEL_LIVE_PENDING' -or $receipt.game_root -ne $game -or $receipt.tests_sha256 -ne (R5Hash $testsPath) -or $receipt.installer_sha256 -ne (R5Hash $PSCommandPath) -or @($receipt.files).Count -ne 1 -or $receipt.files[0].relative -ne $relative -or $receipt.files[0].sha256 -ne $file.sha256){throw 'Receipt mismatch'}
 R5Match $target $file.sha256
 if(Test-Path (Join-Path $audit 'rollback_receipt.json')){throw 'Already recovered'}
}else{
 if(Test-Path $receiptPath){throw 'Existing receipt; refuse reinstall'}
 if(Test-Path $target){throw 'Addition exists; refuse overwrite'}
}
R5Closed
if($Mode.StartsWith('Validate')){[ordered]@{status='VALIDATED';mode=$Mode;additions=1;replacements=0;protected_files=$protected.Count}|ConvertTo-Json;return}
New-Item -ItemType Directory -Force $audit|Out-Null
R5Closed
if($Mode -eq 'Install'){
 if(Test-Path $target){throw 'Addition appeared during preflight'}
 New-Item -ItemType Directory -Force (Split-Path -Parent $target)|Out-Null
 Copy-Item -LiteralPath $sourcePath -Destination $target;R5Match $target $file.sha256;R5Unchanged $protected
 $result=[ordered]@{status='INSTALLED_J1_UI_LABEL_LIVE_PENDING';utc=[DateTime]::UtcNow.ToString('o');game_root=$game;files=@($file);tests_sha256=R5Hash $testsPath;installer_sha256=R5Hash $PSCommandPath;protected=$protected;additions=1;replacements=0;save_writes=0;quest_writes=0;cache_writes=0}
 R5Json $receiptPath $result
}else{
 $recoverable=R5Within (Join-Path $audit ('recoverable_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))) $audit
 $dest=R5Within (Join-Path $recoverable $relative) $recoverable
 New-Item -ItemType Directory -Force (Split-Path -Parent $dest)|Out-Null
 Move-Item -LiteralPath $target -Destination $dest;R5Match $dest $file.sha256;R5Unchanged $protected
 $result=[ordered]@{status='J1_FILE_RECOVERED';game_root=$game;recoverable=$recoverable;files=@($file)}
 R5Json (Join-Path $audit 'rollback_receipt.json') $result
}
Write-Output $result.status
