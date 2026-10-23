param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),[string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',[ValidateSet(2,3,4,5,6)][int]$RepairRevision=6,[switch]$ValidateOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if(@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Game must be closed'}
$game=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
$audit=Join-Path $WorkspaceRoot $(switch($RepairRevision){2{'research\b0_world_interactions\coaster_fix'};3{'research\b0_world_interactions\coaster_crash'};4{'research\b0_world_interactions\coaster_hands_binding'};5{'research\b0_world_interactions\coaster_repeat_gesture'};6{'research\b0_world_interactions\coaster_direct_entry'}})
$rollback='rollback_revision'+($RepairRevision-1)
$prior=Get-Content (Join-Path $audit ($rollback+'\install_receipt.json')) -Raw|ConvertFrom-Json
$relative=@('archive\pc\mod\TowerContinued_WorldInteractions.archive','archive\pc\mod\TowerContinued_WorldInteractions.archive.xl','bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_WorldInteractions_Audit\init.lua')
$expectedHashes=@($prior.sha256)
if($RepairRevision -eq 6){
 $observer=Get-Content (Join-Path $WorkspaceRoot 'research\b0_world_interactions\coaster_animation_audit\install_receipt.json') -Raw|ConvertFrom-Json
 if($observer.native_archive_sha256 -ne $prior.sha256[0]){throw 'Observer baseline differs'}
 $relative+='r6\scripts\PTFR_Coaster_AnimationAudit\CoasterAnimationAudit.reds'
 $expectedHashes[2]=$observer.sha256[1];$expectedHashes+=$observer.sha256[0]
}
$targets=@($relative|ForEach-Object {Join-Path $game $_})
foreach($i in 0..($targets.Count-1)){
 if(-not [IO.Path]::GetFullPath($targets[$i]).StartsWith($game+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Out-of-root target'}
 if((Get-FileHash -LiteralPath $targets[$i]).Hash -ne $expectedHashes[$i]){throw 'Unexpected installed revision; no overwrite'}
}
$python='C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
foreach($test in 'test_world_interactions.py','test_world_interactions_lua.py'){
 & $python (Join-Path $WorkspaceRoot ('tools\'+$test));if($LASTEXITCODE -ne 0){throw "Test failed: $test"}
}
if($RepairRevision -eq 6){
 $observerSource=Join-Path $WorkspaceRoot 'diagnostics\PTFR_Coaster_AnimationAudit\CoasterAnimationAudit.reds'
 $lint=@(& (Join-Path $WorkspaceRoot 'research\finalboards_dismissal\tooling\redscript-cli.exe') lint -s $observerSource -b (Join-Path $game 'r6\cache\final.redscripts') 2>&1)
 $lint|ForEach-Object {Write-Host $_}
 if($LASTEXITCODE -ne 0 -or -not ($lint -match 'Lint successful') -or ($lint -match '\bERROR\b')){throw 'Observer compile failed'}
}
# Prove the exact packed-resource delta against the installed failed revision.
foreach($assembly in 'WolvenKit.Core.dll','WolvenKit.Common.dll','WolvenKit.RED4.dll'){
 [void][Reflection.Assembly]::LoadFrom((Join-Path 'C:\Users\Ayong\Documents\WolvenKit-8.20.0' $assembly))
}
$hash=[WolvenKit.Common.Services.HashService]::new();$hash.Load()
$newArchive=Join-Path $WorkspaceRoot 'build\WorldInteractions\TowerContinued_WorldInteractions.archive'
$old=$null;$new=$null;$reader=[WolvenKit.RED4.Archive.IO.ArchiveReader]::new()
foreach($pair in @(@((Join-Path $audit ($rollback+'\TowerContinued_WorldInteractions.archive')),'old'),@($newArchive,'new'))){
 $loaded=$null;if($reader.ReadArchive($pair[0],$hash,[ref]$loaded).ToString() -ne 'NoError'){throw 'Archive unreadable'}
 if($pair[1] -eq 'old'){$old=$loaded}else{$new=$loaded}
}
function EntryHash($entry){$m=[IO.MemoryStream]::new();try{$entry.Extract($m);return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($m.ToArray()))}finally{$m.Dispose()}}
$oldEntries=@{};foreach($e in $old.Files.Values){$oldEntries[$e.Name]=EntryHash $e}
if($new.Files.Count -ne $(if($RepairRevision -eq 2){8}else{10}) -or $old.Files.Count -ne $(if($RepairRevision -ge 4){10}else{8})){throw 'Unexpected archive coverage'}
$expectedChanged=@($(switch($RepairRevision){2{'towercontinued\world_interactions\coaster_owner.questphase'};3{'towercontinued\world_interactions\coaster.scene';'towercontinued\world_interactions\coaster_hands_1.workspot';'towercontinued\world_interactions\coaster_hands_2.workspot'};{$_ -in 4,5,6}{'towercontinued\world_interactions\coaster.scene'}}))
$changed=@();foreach($e in $new.Files.Values){if(-not $oldEntries.ContainsKey($e.Name)){$changed+=$e.Name}elseif((EntryHash $e) -ne $oldEntries[$e.Name]){$changed+=$e.Name}}
if(@(Compare-Object @($expectedChanged|Sort-Object) @($changed|Sort-Object)).Count){throw "Unexpected resource changes: $changed"}
if((Get-FileHash -LiteralPath ($newArchive+'.xl')).Hash -ne $prior.sha256[1]){throw 'Registration changed'}
$sources=@($newArchive,($newArchive+'.xl'),(Join-Path $WorkspaceRoot 'archive\b0_world_interactions\cet\init.lua'))
if($RepairRevision -eq 6){$sources+=$observerSource}
$writeIndices=@(0,2);if($RepairRevision -eq 6){$writeIndices+=3}
if($ValidateOnly){Write-Host 'VALIDATED: baseline hashes, exact scene delta, nine unchanged native payloads, unchanged registration, Lua and observer compilation; no installation';return}
$protected=[ordered]@{}
foreach($dir in 'archive\pc\mod','r6\scripts','bin\x64\plugins\cyber_engine_tweaks\mods'){
 foreach($f in Get-ChildItem (Join-Path $game $dir) -Recurse -File|Where-Object {($_.Name -like '*TowerContinued*' -or $_.FullName -match '[\\/]PTFR_') -and $_.FullName -notin $targets}){$protected[$f.FullName]=(Get-FileHash -LiteralPath $f.FullName).Hash}
}
$backup=Join-Path $audit ('deployment_backup_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ'))
if(Test-Path -LiteralPath $backup){throw 'Backup already exists'}
New-Item -ItemType Directory -Path $backup|Out-Null
foreach($i in 0..($targets.Count-1)){[IO.File]::Copy($targets[$i],(Join-Path $backup ([IO.Path]::GetFileName($targets[$i]))),$false)}
if(@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Game started; abort'}
try{
 foreach($i in $writeIndices){[IO.File]::Copy($sources[$i],$targets[$i],$true);if((Get-FileHash $sources[$i]).Hash -ne (Get-FileHash $targets[$i]).Hash){throw 'Deployment hash mismatch'}}
 foreach($p in $protected.Keys){if((Get-FileHash -LiteralPath $p).Hash -ne $protected[$p]){throw "Protected file changed: $p"}}
}catch{
 foreach($i in $writeIndices){[IO.File]::Copy((Join-Path $backup ([IO.Path]::GetFileName($targets[$i]))),$targets[$i],$true)}
 throw
}
$receipt=@{status="INSTALLED_COASTER_REPAIR_CANDIDATE_REVISION$RepairRevision";utc=[DateTime]::UtcNow.ToString('o');files=$targets;sha256=@($targets|ForEach-Object {(Get-FileHash $_).Hash});preserved_files=$protected.Count;backup=$backup;changed_native_resources=$changed;unchanged_native_resources=$(if($RepairRevision -ge 4){9}else{7});registration_unchanged=$true;save_files_modified=$false;live_tested=$false}
[IO.File]::WriteAllText((Join-Path $audit 'install_receipt.json'),($receipt|ConvertTo-Json -Depth 5),[Text.UTF8Encoding]::new($false))
$receipt|ConvertTo-Json -Depth 5
