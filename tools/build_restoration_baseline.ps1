param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),[string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$out=Join-Path $WorkspaceRoot 'build\RestorationBaseline_R1'
$research=Join-Path $WorkspaceRoot 'research\restoration_baseline'
$frozen=Join-Path $research 'frozen'
$stage=Join-Path $out 'game'
New-Item -ItemType Directory -Force -Path $out,$research,$frozen,$stage | Out-Null
$archiveNames=@(
 'Afterlife_NativeScene_A2','Afterlife_TriggerAudit','B0_Afterlife_Mirror','B0_DeferredOrdinary',
 'B0_H10_Architecture','B0_H10_Floor','B0_H10_Interactions','B0_H10_Living','B0_H10_Persistent','B0_H10_VOnlyMirror',
 'B0_JpnNetrunner01','B0_JunkMeleePair','B0_LCH_Clothing_Vendor','B0_Northside_Foodshop','B0_Northside_Gunsmith','B0_Northside_Medicstore',
 'B0_OrdinaryVendorBatch','B0_RipNetEight','B0_TimeUnpauseNone','B0_VendorVariants','B0_Wilson_Vendor',
 'Coyote_NativeScene_C2','Coyote_TriggerAudit','OrdinaryMirrors_C4','Phase2B_P0_DirectReturn')
$scripts=@('PTFR_Afterlife_NativeBootstrap_A4\AfterlifeNativeBootstrapA4.reds',
 'PTFR_B0_Afterlife_Mirror\AfterlifeMirrorDriver.reds','PTFR_B0_DeferredVendors\DeferredVendorDriver.reds',
 'PTFR_B0_OrdinaryVendors\OrdinaryVendorDriver.reds','PTFR_B0_VendorShared\VendorSharedFarDriver.reds',
 'PTFR_B0_VendorVariants\VendorVariantDriver.reds')
$bridges=@('PTFR_B0_Wilson_Vendor','PTFR_B0_LCH_Clothing_Vendor','PTFR_B0_Northside_Gunsmith',
 'PTFR_B0_Northside_Foodshop','PTFR_B0_Northside_Medicstore','PTFR_B0_VendorBatch',
 'PTFR_B0_JunkMelee_Pair','PTFR_B0_RipNet_Eight','PTFR_B0_JpnNetrunner01','PTFR_Afterlife_Native_Auto_A3')
$cet='bin\x64\plugins\cyber_engine_tweaks\mods'
$inventoryPath=Join-Path $research 'frozen_inventory.json'
if(-not (Test-Path -LiteralPath $inventoryPath)){
 $paths=[Collections.Generic.List[string]]::new()
 foreach($name in $archiveNames){
  $paths.Add('archive\pc\mod\TowerContinued_'+$name+'.archive')
  if($name -ne 'Phase2B_P0_DirectReturn'){$paths.Add('archive\pc\mod\TowerContinued_'+$name+'.archive.xl')}
 }
 foreach($p in $scripts){$paths.Add('r6\scripts\'+$p)}
 foreach($name in $bridges){$paths.Add($cet+'\'+$name+'\init.lua')}
 # Include the currently automatic cohorts' passive/manual diagnostics as-is.
 foreach($name in @('PTFR_B0_OrdinaryVendors','PTFR_B0_DeferredVendors','PTFR_B0_VendorVariants','PTFR_B0_Afterlife_Mirror')){$paths.Add($cet+'\'+$name+'\init.lua')}
 $items=@()
 foreach($p in $paths){
  $src=Join-Path $GameRoot $p;$dst=Join-Path $frozen $p
  $hash=(Get-FileHash -LiteralPath $src).Hash
  if(Test-Path -LiteralPath $dst){if((Get-FileHash -LiteralPath $dst).Hash -ne $hash){throw 'Partial snapshot mismatch'}}
  else{New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dst)|Out-Null;Copy-Item -LiteralPath $src -Destination $dst}
  $items+=@{path=$p;sha256=$hash}
 }
 [IO.File]::WriteAllText($inventoryPath,(@{version='Baseline-R1';files=$items}|ConvertTo-Json -Depth 5))
}
$inventory=Get-Content -LiteralPath $inventoryPath -Raw|ConvertFrom-Json
$files=[Collections.Generic.List[object]]::new()
foreach($item in $inventory.files){
 $src=Join-Path $frozen $item.path
 if((Get-FileHash -LiteralPath $src).Hash -ne $item.sha256){throw 'Frozen input changed'}
 $dst=Join-Path $stage $item.path
 New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dst)|Out-Null
 Copy-Item -LiteralPath $src -Destination $dst
 $files.Add([pscustomobject]@{path=$item.path;before=$item.sha256;sha256=$item.sha256;action='preserved'})
}
function Overlay([string]$source,[string]$relative){
 $src=Join-Path $WorkspaceRoot $source;$dst=Join-Path $stage $relative
 New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dst)|Out-Null
 Copy-Item -LiteralPath $src -Destination $dst
 $hash=(Get-FileHash -LiteralPath $dst).Hash
 $entry=@($files|Where-Object path -eq $relative)
 if($entry.Count -eq 1){$entry[0].sha256=$hash;$entry[0].action='replace-with-backup'}
 elseif($entry.Count -eq 0){$files.Add([pscustomobject]@{path=$relative;before=$null;sha256=$hash;action='add'})}
 else{throw 'Duplicate package destination'}
}
Overlay 'redscript\PTFR_RestorationBaseline\RestorationBaseline.reds' 'r6\scripts\PTFR_RestorationBaseline\RestorationBaseline.reds'
Overlay 'redscript\PTFR_RestorationBaseline\compat\AfterlifeNativeBootstrapA4.reds' 'r6\scripts\PTFR_Afterlife_NativeBootstrap_A4\AfterlifeNativeBootstrapA4.reds'
Overlay 'redscript\PTFR_RestorationBaseline\compat\VendorSharedFarDriver.reds' 'r6\scripts\PTFR_B0_VendorShared\VendorSharedFarDriver.reds'
Overlay 'diagnostics\PTFR_RestorationBaseline\init.lua' ($cet+'\PTFR_RestorationBaseline\init.lua')
foreach($name in $bridges){Overlay 'diagnostics\PTFR_RestorationBaseline\legacy_bridge.lua' ($cet+'\'+$name+'\init.lua')}
$actual=@(Get-ChildItem -LiteralPath $stage -Recurse -File|ForEach-Object {[IO.Path]::GetRelativePath($stage,$_.FullName)})
if(@(Compare-Object ($actual|Sort-Object) (@($files.path)|Sort-Object)).Count){throw 'Unexpected staging file'}
$manifest=@{version='Baseline-R1';status='BUILT_NOT_LIVE_VALIDATED';files=$files.ToArray();archivesPreserved=$archiveNames.Count;newNativeOwners=0;rulesSha256=(Get-FileHash (Join-Path $research 'rules.json')).Hash;savesModified=$false;scope='Current development baseline, dependencies not bundled; no archive renaming or new quest registrations'}
[IO.File]::WriteAllText((Join-Path $out 'manifest.json'),($manifest|ConvertTo-Json -Depth 6))
'Built Baseline-R1: '+$files.Count+' files; 25 existing archives unchanged; 12 runtime replacements with rollback, 2 additions'
