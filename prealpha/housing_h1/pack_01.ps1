param([Parameter(Mandatory=$true)][string]$Component,[Parameter(Mandatory=$true)][string]$Output)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
. (Join-Path $ws 'tools/shark_b7_2_helpers.ps1')
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$componentPath=[IO.Path]::GetFullPath($Component);$root=Split-Path -Parent $componentPath
$out=[IO.Path]::GetFullPath($Output)
if(!$componentPath.StartsWith($ws+'\') -or !$out.StartsWith($ws+'\') -or (Test-Path -LiteralPath $out)){throw 'New workspace output required'}
$m=Get-Content -LiteralPath $componentPath -Raw|ConvertFrom-Json
New-Item -ItemType Directory -Path $out,(Join-Path $out 'source'),(Join-Path $out 'readback'),(Join-Path $out 'package/archive/pc/mod') -Force | Out-Null
$pins=[ordered]@{};$resources=[ordered]@{};$boots=@($m.boots)
function Pin($p){
 if([IO.Path]::IsPathRooted($p) -or $p -match '(^|/)\.\.(/|$)'){throw 'Unsafe pin'}
 $h=(Get-FileHash -LiteralPath (Join-Path $ws $p)).Hash
 if($pins.Contains($p) -and $pins[$p] -cne $h){throw 'Conflicting pin'}
 $pins[$p]=$h
}
foreach($p in $m.source_pins.PSObject.Properties){Pin $p.Name;if($pins[$p.Name] -cne $p.Value){throw 'Native source drift'}}
foreach($p in @('prealpha/housing_h1/pack_01.ps1','tools/build_phase2a.ps1','tools/shark_b7_2_helpers.ps1','tools/gig_family_b7_1_xl.ps1','tools/afterlife_faces_r5_deployment.ps1')){Pin $p}
Pin ([IO.Path]::GetRelativePath($ws,$componentPath).Replace('\','/'))
$override='towercontinued\b0_h10_persistent\h10_owner.questphase'
foreach($p in $m.resources.PSObject.Properties){
 if($p.Name -cnotlike 'towercontinued\housing_h1\*' -and $p.Name -cne $override){throw 'Unexpected resource namespace'}
 $source=Join-Path (Join-Path $root 'source') $p.Name
 if((Get-FileHash -LiteralPath $source).Hash -cne $p.Value){throw 'Native resource drift'}
 $target=Join-Path (Join-Path $out 'source') $p.Name
 New-Item -ItemType Directory -Path (Split-Path -Parent $target) -Force | Out-Null
 Copy-Item -LiteralPath $source -Destination $target
 $resources[$p.Name]=$p.Value
 Export-Cr2wJson (Read-Cr2wFile $target) (Join-Path $out ('readback/'+$p.Name.Replace('\','_')+'.json'))
}
if(!$resources.Contains($override) -or @($boots).Count -lt 5 -or @($boots|Select-Object -Unique).Count -ne $boots.Count){throw 'Incomplete housing resource scope'}
$archivePins=[ordered]@{};$xlPins=[ordered]@{};$collisions=@()
foreach($a in Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc/mod') -Filter '*.archive' -File|Sort-Object Name){
 $archivePins[$a.FullName]=(Get-FileHash -LiteralPath $a.FullName).Hash
 $arc=$null
 if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($a.FullName,$hs,[ref]$arc).ToString() -cne 'NoError'){throw 'Installed archive read failed'}
 foreach($entry in $arc.Files.Values){
  if(!$resources.Contains($entry.Name)){continue}
  if($entry.Name -cne $override -or $a.Name -cne 'TowerContinued_PreAlpha.archive'){throw 'Unexpected resource collision'}
  $mem=[IO.MemoryStream]::new()
  try{$entry.Extract($mem);$digest=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($mem.ToArray()))}finally{$mem.Dispose()}
  if($digest -cne $m.override_donors.$override){throw 'H10 donor changed'}
  $collisions+=,@{depot=$entry.Name;archive=$a.FullName;sha256=$digest}
 }
}
if($collisions.Count -ne 1){throw 'Expected exact single H10 mod override'}
foreach($x in Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc/mod') -Filter '*.xl' -File|Sort-Object Name){$xlPins[$x.FullName]=(Get-FileHash -LiteralPath $x.FullName).Hash}
B71Parser|Out-Null
$inventory=@(B72Inventory $game);$used=@($inventory.id)
# Read the current native injection parent, rather than an old extracted copy.
$parentReads=@();$official=@(Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc/content') -Filter '*.archive' -File)+@(Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc/ep1') -Filter '*.archive' -File)
foreach($a in $official){
 $arc=$null
 if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($a.FullName,$hs,[ref]$arc).ToString() -cne 'NoError'){throw 'Official archive read failed'}
 foreach($entry in $arc.Files.Values){
  if($entry.Name -cne 'ep1\quest\ep1.quest'){continue}
  $mem=[IO.MemoryStream]::new()
  try{$entry.Extract($mem);$p=Join-Path $out ('readback/parent_'+$parentReads.Count+'.quest');[IO.File]::WriteAllBytes($p,$mem.ToArray())}finally{$mem.Dispose()}
  Export-Cr2wJson (Read-Cr2wFile $p) ($p+'.json')
  $parent=Get-Content -LiteralPath ($p+'.json') -Raw|ConvertFrom-Json
  $used+=@($parent.Data.RootChunk.graph.Data.nodes.Data.id)
  $parentReads+=,@{archive=$a.FullName;archive_sha256=(Get-FileHash -LiteralPath $a.FullName).Hash;raw=$p;sha256=(Get-FileHash -LiteralPath $p).Hash}
 }
}
if($parentReads.Count -lt 1){throw 'Current native parent missing'}
$injections=@()
foreach($boot in $boots){
 if(!$resources.Contains($boot) -or $boot -cnotlike 'towercontinued\housing_h1\*'){throw 'Unpacked/nonprivate boot'}
 $id=B72Id ($boot+':1')
 if($id -in $used -or $id -ne (B72IdIndependent ($boot+':1'))){throw 'Injection ID collision'}
 $used+=,$id;$injections+=,@{depot=$boot;id=$id}
}
$name='00000000_TowerContinued_Housing_H1.archive'
if($name -cge 'TowerContinued_PreAlpha.archive'){throw 'Override priority error'}
$archive=Join-Path $out ('package/archive/pc/mod/'+$name)
$xl=B71Render $boots;B71Parse $xl|Out-Null
[IO.File]::WriteAllText(($archive+'.xl'),$xl,[Text.UTF8Encoding]::new($false))
$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new((Join-Path $out 'source')),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -cne 'NoError' -or $packed.Files.Count -ne $resources.Count){throw 'Packed resource scope mismatch'}
foreach($entry in $packed.Files.Values){
 if(!$resources.Contains($entry.Name)){throw 'Unexpected packed resource'}
 $mem=[IO.MemoryStream]::new()
 try{$entry.Extract($mem);if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($mem.ToArray())) -cne $resources[$entry.Name]){throw 'Packed byte mismatch'}}finally{$mem.Dispose()}
}
foreach($p in $archivePins.Keys){if((Get-FileHash -LiteralPath $p).Hash -cne $archivePins[$p]){throw 'Installed archive changed'}}
foreach($p in $xlPins.Keys){if((Get-FileHash -LiteralPath $p).Hash -cne $xlPins[$p]){throw 'Installed XL changed'}}
$files=@(foreach($p in @($archive,($archive+'.xl'))){@{relative='archive/pc/mod/'+[IO.Path]::GetFileName($p);sha256=(Get-FileHash -LiteralPath $p).Hash}})
$result=@{status='PASS_H1_PACK_AND_RESOURCE_SCOPE_NOT_LIVE';component=$componentPath;component_sha256=(Get-FileHash -LiteralPath $componentPath).Hash;resources=$resources;boots=$boots;injections=$injections;files=$files;source_pins=$pins;archive_pins=$archivePins;xl_pins=$xlPins;collisions=$collisions;current_native_parent=$parentReads;packed_readback=$true;official_overrides=@();mod_overrides=@($override)}
[IO.File]::WriteAllText((Join-Path $out 'pack.json'),($result|ConvertTo-Json -Depth 60),[Text.UTF8Encoding]::new($false))
@{status=$result.status;resources=$resources.Count;boots=$boots.Count;output=$out}|ConvertTo-Json
