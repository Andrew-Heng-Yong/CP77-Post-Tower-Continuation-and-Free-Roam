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
function Inside([string]$path,[string]$root){
 $full=[IO.Path]::GetFullPath($path)
 if(-not $full.StartsWith($root+'\',[StringComparison]::OrdinalIgnoreCase)){throw ('Target escaped root: '+$full)}
 $cursor=$full
 while($cursor.Length -ge $root.Length){
  if(Test-Path -LiteralPath $cursor){
   if(((Get-Item -LiteralPath $cursor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw ('Reparse point: '+$cursor)}
  }
  if($cursor.Equals($root,[StringComparison]::OrdinalIgnoreCase)){break}
  $cursor=[IO.Path]::GetDirectoryName($cursor)
  if(-not $cursor){throw 'Invalid target ancestry'}
 }
 return $full
}
function GameClosed {if(@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Cyberpunk is running; installation stopped'}}
function HashIs([string]$path,[string]$sha){
 if($sha -notmatch '^[0-9A-Fa-f]{64}$' -or -not (Test-Path -LiteralPath $path -PathType Leaf) -or (Get-FileHash -LiteralPath $path).Hash -ne $sha){throw ('Hash/missing mismatch: '+$path)}
}
GameClosed
$manifestPath=Inside (Join-Path $audit 'original_lamp_s1_package_manifest.json') $workspace
$manifest=Get-Content -LiteralPath $manifestPath -Raw|ConvertFrom-Json
if($manifest.status -ne 'BUILT_SINGLETON_ORIGINAL_LAMP_NOT_INSTALLED_OR_LIVE' -or $manifest.original_placement_alias_writes -ne 1 -or $manifest.original_light_properties_changed -ne 0 -or $manifest.original_variant_writes -ne 0 -or $manifest.story_fact_writes -ne 0){throw 'Candidate scope changed'}
$expectedArchive=Inside (Join-Path $workspace 'build\MistyOriginalLampAliasS1\TowerContinued_MistyOriginalLampAliasS1.archive') $workspace
$expectedProbe=Inside (Join-Path $workspace 'diagnostics\PTFR_MistyViktor_Original_Lamp_S1\init.lua') $workspace
if([IO.Path]::GetFullPath($manifest.archive) -ne $expectedArchive -or [IO.Path]::GetFullPath($manifest.probe) -ne $expectedProbe){throw 'Source paths changed'}
$files=@(
 [pscustomobject]@{relative='archive\pc\mod\TowerContinued_MistyOriginalLampAliasS1.archive';source=$expectedArchive;sha=$manifest.sha256},
 [pscustomobject]@{relative='archive\pc\mod\TowerContinued_MistyOriginalLampAliasS1.archive.xl';source=$expectedArchive+'.xl';sha=$manifest.xl_sha256},
 [pscustomobject]@{relative='bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_MistyViktor_Original_Lamp_S1\init.lua';source=$expectedProbe;sha=$manifest.probe_sha256}
)
$receipt=Inside (Join-Path $audit 'original_lamp_s1_install_receipt.json') $workspace
if(Test-Path -LiteralPath $receipt){throw 'Singleton already has a receipt; do not reinstall blindly'}
foreach($file in $files){
 HashIs $file.source $file.sha
 $target=Inside (Join-Path $game $file.relative) $game
 if(Test-Path -LiteralPath $target){throw ('Additive target already exists: '+$target)}
}
$r7=Get-Content (Inside (Join-Path $audit 'details_r7_install_receipt.json') $workspace) -Raw|ConvertFrom-Json
$poc=Get-Content (Inside (Join-Path $audit 'light_poc_install_receipt.json') $workspace) -Raw|ConvertFrom-Json
if($r7.status -ne 'INSTALLED_R7_DETAILS_IDLE_OPTIN_LIVE_PENDING' -or $poc.status -ne 'INSTALLED_LIGHT_POC_IDLE_OPTIN_LIVE_PENDING'){throw 'Earlier installed package receipts changed'}
foreach($prior in @($r7.files)+@($poc.files)){HashIs (Inside (Join-Path $game $prior.relative) $game) $prior.sha256}
$protected=[ordered]@{}
foreach($scope in @('archive\pc\mod','r6\scripts','r6\tweaks','bin\x64\plugins\cyber_engine_tweaks\mods')){
 $dir=Inside (Join-Path $game $scope) $game
 if(-not (Test-Path -LiteralPath $dir -PathType Container)){continue}
 foreach($entry in (Get-ChildItem -LiteralPath $dir -Recurse -File -Force)){
  $relative=[IO.Path]::GetRelativePath($game,$entry.FullName)
  if(@($relative.Split('\')|Where-Object {$_ -like 'TowerContinued*' -or $_ -like 'PTFR_*'}).Count){
   $path=Inside $entry.FullName $game
   $protected[$path]=(Get-FileHash -LiteralPath $path).Hash
  }
 }
}
function AssertProtected {foreach($path in $protected.Keys){HashIs $path $protected[$path]}}
AssertProtected
GameClosed
if($ValidateOnly){@{status='VALIDATED_ONLY_NOT_INSTALLED';additive_targets=3;protected_files=$protected.Count;replacements=0;game_closed=$true;source_sha256=$manifest.sha256}|ConvertTo-Json;return}
$created=[Collections.Generic.List[string]]::new()
$staged=[Collections.Generic.List[string]]::new()
try{
 foreach($file in $files){
  GameClosed;AssertProtected;HashIs $file.source $file.sha
  $target=Inside (Join-Path $game $file.relative) $game
  if(Test-Path -LiteralPath $target){throw ('Target appeared: '+$target)}
  $parent=Inside (Split-Path -Parent $target) $game
  if(-not (Test-Path -LiteralPath $parent -PathType Container)){New-Item -ItemType Directory -Path $parent -Force|Out-Null}
  $temp=Inside ($target+'.'+[Guid]::NewGuid().ToString('N')+'.ptfr-new') $game
  $writer=[IO.File]::Open($temp,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
  $staged.Add($temp)
  try{$reader=[IO.File]::OpenRead($file.source);try{$reader.CopyTo($writer);$writer.Flush($true)}finally{$reader.Dispose()}}finally{$writer.Dispose()}
  HashIs $temp $file.sha;GameClosed
  [IO.File]::Move($temp,$target)
  $created.Add($target)
  HashIs $target $file.sha
 }
 GameClosed;AssertProtected
 $data=[ordered]@{status='INSTALLED_SINGLETON_ORIGINAL_ALIAS_IDLE_OPTIN_LIVE_PENDING';utc=[DateTime]::UtcNow.ToString('o');files=@($files|ForEach-Object {@{relative=$_.relative;sha256=$_.sha}});protected_files=$protected.Count;replaced_files=0;original_sector_override=1;alias_only=$true;light_visibility_changed_on_install=$false;automatic_activation=$false;story_fact_writes=0;live_tested=$false;save_files_modified=$false;rollback='With game closed, recover only these three verified additive paths; leave R7 and prior POC untouched.'}
 $bytes=[Text.UTF8Encoding]::new($false).GetBytes(($data|ConvertTo-Json -Depth 7))
 $stream=[IO.File]::Open($receipt,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
 try{$stream.Write($bytes,0,$bytes.Length);$stream.Flush($true)}finally{$stream.Dispose()}
 $data|ConvertTo-Json -Depth 7
}catch{
 $failure=$_.Exception.Message
 # Never remove existing user files. A partial install remains identified by
 # these exact new-only paths and must be recovered with the game closed.
 [pscustomobject]@{status='PARTIAL_SINGLETON_INSTALL_REVIEW_REQUIRED';failure=$failure;created=@($created);staged=@($staged);prior_files_preserved=$true}|ConvertTo-Json -Depth 5|Write-Output
 throw
}
