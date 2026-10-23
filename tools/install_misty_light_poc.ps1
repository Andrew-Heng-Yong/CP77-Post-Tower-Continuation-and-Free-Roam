param(
 [string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),
 [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
 [switch]$ValidateOnly
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\')
$game=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
$audit=Join-Path $workspace 'research\misty_viktor_world'

function AssertGameClosed {
 if(@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Cyberpunk running; additive light POC installation deferred'}
}
function RequireWithin([string]$Path,[string]$Root){
 $resolved=[IO.Path]::GetFullPath($Path)
 if(-not $resolved.StartsWith($Root+'\',[StringComparison]::OrdinalIgnoreCase)){throw ('Path escaped intended root: '+$resolved)}
 # Reject redirection through a junction/symlink anywhere inside the selected root.
 $cursor=$resolved
 while($cursor.Length -ge $Root.Length){
  if(Test-Path -LiteralPath $cursor){
   $item=Get-Item -LiteralPath $cursor -Force
   if(($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw ('Reparse point is not an approved installer target: '+$cursor)}
  }
  if($cursor.Equals($Root,[StringComparison]::OrdinalIgnoreCase)){break}
  $cursor=[IO.Path]::GetDirectoryName($cursor)
  if([string]::IsNullOrEmpty($cursor)){throw 'Installer ancestry validation failed'}
 }
 return $resolved
}
function AssertHash([string]$Path,[string]$Expected,[string]$Reason){
 if($Expected -notmatch '^[0-9A-Fa-f]{64}$' -or -not (Test-Path -LiteralPath $Path -PathType Leaf)){throw ($Reason+': missing file/invalid digest '+$Path)}
 if((Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash -ne $Expected){throw ($Reason+': '+$Path)}
}
AssertGameClosed
$manifestPath=RequireWithin (Join-Path $audit 'light_poc_manifest.json') $workspace
$testsPath=RequireWithin (Join-Path $audit 'light_poc_tests.json') $workspace
$priorPath=RequireWithin (Join-Path $audit 'details_r7_install_receipt.json') $workspace
$manifest=Get-Content -LiteralPath $manifestPath -Raw|ConvertFrom-Json
$tests=Get-Content -LiteralPath $testsPath -Raw|ConvertFrom-Json
$prior=Get-Content -LiteralPath $priorPath -Raw|ConvertFrom-Json
if($manifest.status -ne 'BUILT_LIGHT_POC_NOT_INSTALLED_OR_LIVE' -or $tests.status -ne 'PASS_LIGHT_POC_OFFLINE_NOT_LIVE') {throw 'Light POC candidate/offline test status mismatch'}
if($tests.archive_sha256 -ne $manifest.sha256 -or $tests.xl_sha256 -ne $manifest.xl_sha256 -or $tests.probe_sha256 -ne $manifest.probe_sha256){throw 'Light POC tests have stale package/probe digests'}
if($tests.manifest_sha256 -ne (Get-FileHash -LiteralPath $manifestPath).Hash){throw 'Light POC manifest changed after independent tests'}
if($prior.status -ne 'INSTALLED_R7_DETAILS_IDLE_OPTIN_LIVE_PENDING' -or $prior.files.Count -ne 3){throw 'Required R7 preservation receipt changed'}
$expectedPrior=@(
 'archive\pc\mod\TowerContinued_MistyViktorShellOptIn.archive',
 'archive\pc\mod\TowerContinued_MistyViktorShellOptIn.archive.xl',
 'bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_MistyViktor_World\init.lua'
)
for($i=0;$i -lt 3;$i++){
 if($prior.files[$i].relative -ne $expectedPrior[$i]){throw 'Unexpected R7 receipt destination'}
 AssertHash (RequireWithin (Join-Path $game $expectedPrior[$i]) $game) $prior.files[$i].sha256 'Installed R7 differs from preserved receipt'
}
$expectedArchive=Join-Path $workspace 'build\MistyViktorLightPOC\TowerContinued_MistyViktorLightPOC.archive'
$expectedProbe=Join-Path $workspace 'diagnostics\PTFR_MistyViktor_Light_POC\init.lua'
if([IO.Path]::GetFullPath($manifest.archive) -ne $expectedArchive -or [IO.Path]::GetFullPath($manifest.probe) -ne $expectedProbe){throw 'Light POC source escaped prescribed build/probe path'}
$files=@(
 [pscustomobject]@{relative='archive\pc\mod\TowerContinued_MistyViktorLightPOC.archive';source=$expectedArchive;hash=$manifest.sha256},
 [pscustomobject]@{relative='archive\pc\mod\TowerContinued_MistyViktorLightPOC.archive.xl';source=($expectedArchive+'.xl');hash=$manifest.xl_sha256},
 [pscustomobject]@{relative='bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_MistyViktor_Light_POC\init.lua';source=$expectedProbe;hash=$manifest.probe_sha256}
)
# Test all declared source dependencies again; require the test program itself
# among the hashed inputs so changing the checker invalidates an old PASS.
if(-not $tests.PSObject.Properties['input_hashes'] -or @($tests.input_hashes.PSObject.Properties).Count -lt 4){throw 'Independent-test source freshness inventory absent'}
$inputNames=@($tests.input_hashes.PSObject.Properties.Name)
if('tools/test_misty_light_poc.py' -notin $inputNames -or 'research/misty_viktor_world/light_poc_manifest.json' -notin $inputNames){throw 'Independent test/manifest missing from freshness inventory'}
foreach($entry in $tests.input_hashes.PSObject.Properties){
 AssertHash (RequireWithin (Join-Path $workspace $entry.Name) $workspace) $entry.Value 'Light POC tested input changed'
}
foreach($file in $files){
 $target=RequireWithin (Join-Path $game $file.relative) $game
 if(Test-Path -LiteralPath $target){throw ('Additive installer refuses existing/unexplained destination: '+$target)}
 AssertHash (RequireWithin $file.source $workspace) $file.hash 'Light POC source changed'
}
$receiptPath=RequireWithin (Join-Path $audit 'light_poc_install_receipt.json') $workspace
if(Test-Path -LiteralPath $receiptPath){throw 'Prior light POC install receipt exists; resolve its lifecycle explicitly before reinstalling'}

$protected=[ordered]@{}
foreach($scope in @('archive\pc\mod','r6\scripts','r6\tweaks','bin\x64\plugins\cyber_engine_tweaks\mods')){
 $scopePath=RequireWithin (Join-Path $game $scope) $game
 if(-not (Test-Path -LiteralPath $scopePath -PathType Container)){continue}
 foreach($file in (Get-ChildItem -LiteralPath $scopePath -Recurse -File -Force)){
  $relative=[IO.Path]::GetRelativePath($game,$file.FullName)
  if(@($relative.Split('\')|Where-Object {$_ -like 'TowerContinued*' -or $_ -like 'PTFR_*'}).Count){
   $path=RequireWithin $file.FullName $game
   $protected[$path]=(Get-FileHash -LiteralPath $path).Hash
  }
 }
}
$priorReceiptHash=(Get-FileHash -LiteralPath $priorPath).Hash
function AssertProtected {
 foreach($path in $protected.Keys){AssertHash $path $protected[$path] 'Protected installed project file changed'}
 AssertHash $priorPath $priorReceiptHash 'Original R7 receipt changed'
 for($i=0;$i -lt 3;$i++){AssertHash (Join-Path $game $expectedPrior[$i]) $prior.files[$i].sha256 'Original R7 target changed'}
}
AssertProtected
AssertGameClosed
if($ValidateOnly){
 [pscustomobject]@{status='VALIDATED_ONLY_NOT_INSTALLED';additive_targets=3;protected_files=$protected.Count;original_r7_targets_unchanged=$true;original_r7_receipt_unchanged=$true;destination_writes=0;game_running=$false;archive_sha256=$manifest.sha256;probe_sha256=$manifest.probe_sha256}|ConvertTo-Json
 return
}

$token=[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')+'_'+[Guid]::NewGuid().ToString('N')
$created=[Collections.Generic.List[object]]::new()
$staged=[Collections.Generic.List[object]]::new()
$createdDirectories=[Collections.Generic.List[string]]::new()
$receiptCreated=$false
try {
 foreach($file in $files){
  AssertGameClosed
  AssertProtected
  $target=RequireWithin (Join-Path $game $file.relative) $game
  if(Test-Path -LiteralPath $target){throw ('Destination appeared during validation: '+$target)}
  AssertHash $file.source $file.hash 'POC source changed immediately before copy'
  $parent=RequireWithin (Split-Path -Parent $target) $game
  if(-not (Test-Path -LiteralPath $parent -PathType Container)){
   New-Item -ItemType Directory -Path $parent -Force|Out-Null
   $createdDirectories.Add($parent)
  }
  $temporary=RequireWithin ($target+'.'+$token+'.ptfr-new') $game
  $writer=$null;$reader=$null
  try {
   # CreateNew proves this exact staging file is ours; never overwrite a user file.
   $writer=[IO.File]::Open($temporary,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
   $staged.Add([pscustomobject]@{path=$temporary;relative=$file.relative;hash=$file.hash})
   $reader=[IO.File]::Open($file.source,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
   $reader.CopyTo($writer);$writer.Flush($true)
  }finally{if($null -ne $reader){$reader.Dispose()};if($null -ne $writer){$writer.Dispose()}}
  AssertHash $temporary $file.hash 'Staged POC copy did not verify'
  AssertGameClosed
  # Two-argument Move is atomic on the same volume and fails if target exists.
  [IO.File]::Move($temporary,$target)
  $created.Add([pscustomobject]@{path=$target;relative=$file.relative;hash=$file.hash})
  AssertHash $target $file.hash 'Installed POC addition did not verify'
 }
 AssertGameClosed
 AssertProtected
 $receipt=[ordered]@{
  status='INSTALLED_LIGHT_POC_IDLE_OPTIN_LIVE_PENDING';utc=[DateTime]::UtcNow.ToString('o')
  files=@($files|ForEach-Object {@{relative=$_.relative;sha256=$_.hash}})
  additive_only=$true;replaced_files=0;protected_files=$protected.Count
  original_r7_receipt_sha256=$priorReceiptHash;original_r7_targets_unchanged=$true
  manifest_sha256=$tests.manifest_sha256;tests_sha256=(Get-FileHash -LiteralPath $testsPath).Hash
  test_inputs=$tests.input_hashes;private_light_count=1;story_fact_writes=0;scene_starts=0;save_files_modified=$false;gameplay_commands_executed=0;live_tested=$false
  rollback='With game closed, remove only the three verified additive paths listed in files; R7 remains unchanged.'
 }
 # Receipt is also new-only; a raced-in receipt cannot be overwritten.
 $receiptStream=[IO.File]::Open($receiptPath,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
 $receiptCreated=$true
 try{$bytes=[Text.UTF8Encoding]::new($false).GetBytes(($receipt|ConvertTo-Json -Depth 10));$receiptStream.Write($bytes,0,$bytes.Length);$receiptStream.Flush($true)}finally{$receiptStream.Dispose()}
 $receipt|ConvertTo-Json -Depth 7
}catch{
 $failure=$_.Exception.Message
 $recoveryErrors=[Collections.Generic.List[string]]::new();$recovered=[Collections.Generic.List[string]]::new()
 $recovery=RequireWithin (Join-Path $audit ('light_poc_failed_'+$token)) $workspace
 $running=@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count -gt 0
 if($running){$recoveryErrors.Add('Game started during install; recovery deferred. Do not load a save until the listed new additions are recovered with game closed.')}
 else {
  # Preserve failed/partial additions recoverably. Existing R7 files are never
  # copied, overwritten, moved or deleted by this installer or its recovery.
  foreach($item in @($created)+@($staged)){
   if(-not (Test-Path -LiteralPath $item.path -PathType Leaf)){continue}
   try{
    AssertGameClosed
    $path=RequireWithin $item.path $game
    if($path -notlike '*.ptfr-new'){AssertHash $path $item.hash 'New target changed externally; refusing recovery move'}
    $relative=[IO.Path]::GetRelativePath($game,$path)
    $saved=RequireWithin (Join-Path $recovery $relative) $recovery
    New-Item -ItemType Directory -Path (Split-Path -Parent $saved) -Force|Out-Null
    Move-Item -LiteralPath $path -Destination $saved -ErrorAction Stop
    $recovered.Add($relative)
   }catch{$recoveryErrors.Add($item.path+': '+$_.Exception.Message)}
  }
 }
 $originalsUnchanged=$true
 if($receiptCreated -and (Test-Path -LiteralPath $receiptPath -PathType Leaf)){
  try{
   $partialReceipt=RequireWithin (Join-Path $recovery 'partial_install_receipt.json') $recovery
   New-Item -ItemType Directory -Path $recovery -Force|Out-Null
   Move-Item -LiteralPath $receiptPath -Destination $partialReceipt -ErrorAction Stop
  }catch{$recoveryErrors.Add('Partial success receipt recovery failed: '+$_.Exception.Message)}
 }
 try{AssertProtected}catch{$originalsUnchanged=$false;$recoveryErrors.Add($_.Exception.Message)}
 $failureReceipt=[ordered]@{status='LIGHT_POC_INSTALL_FAILED';utc=[DateTime]::UtcNow.ToString('o');failure=$failure;recovery_directory=$recovery;created=@($created);staged=@($staged);recovered=@($recovered);created_directories=@($createdDirectories);protected_originals_unchanged=$originalsUnchanged;game_running=$running;recovery_errors=@($recoveryErrors)}
 $failureReceiptPath=RequireWithin (Join-Path $audit ('light_poc_failed_install_'+$token+'.json')) $workspace
 try{[IO.File]::WriteAllText($failureReceiptPath,($failureReceipt|ConvertTo-Json -Depth 9),[Text.UTF8Encoding]::new($false))}catch{Write-Warning ('Could not write failure receipt: '+$_.Exception.Message)}
 $failureReceipt|ConvertTo-Json -Depth 6|Write-Output
 throw ('Light POC install failed. Original project files unchanged='+$originalsUnchanged+'. New additions recovered to '+$recovery+'. '+$failure)
}
