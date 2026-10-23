param([string]$Revision='dt1_01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if($Revision -cnotmatch '^dt1_\d{2}$'){throw 'Invalid revision'}
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$build=Join-Path $PSScriptRoot ('build/'+$Revision)
$manifest=Join-Path $build 'build.json';$output=Join-Path $build 'resource_check.json'
if(Test-Path -LiteralPath $output){throw 'Immutable evidence exists'}
function SHA($p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash}
function ExtractSHA($entry){$m=[IO.MemoryStream]::new();try{$entry.Extract($m);[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($m.ToArray()))}finally{$m.Dispose()}}
function Bound($relative){
 if([IO.Path]::IsPathRooted($relative) -or $relative -match '(^|[\\/])\.\.([\\/]|$)'){throw 'Unsafe relative source'}
 $p=[IO.Path]::GetFullPath((Join-Path $workspace $relative));$prefix=[IO.Path]::GetFullPath($workspace).TrimEnd('\')+'\'
 if(!$p.StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase)){throw 'Source escapes workspace'}
 return $p
}
$m=Get-Content -LiteralPath $manifest -Raw|ConvertFrom-Json
if($m.status -cne 'BUILT_DT1_LIVE_PENDING' -or @($m.official_overrides).Count -ne 0 -or @($m.resources.PSObject.Properties).Count -lt 1){throw 'Unexpected bundle scope'}
$pins=@{};foreach($p in $m.source_pins.PSObject.Properties){$full=Bound $p.Name;if((SHA $full) -cne $p.Value){throw "Source pin drift: $($p.Name)"};$pins[$full]=$p.Value}
foreach($helper in @('prealpha/dogtown_dt1/resource_check.ps1','tools/build_phase2a.ps1','tools/shark_b7_2_helpers.ps1','tools/gig_family_b7_1_xl.ps1','tools/afterlife_faces_r5_deployment.ps1','research/q307_extracted/raw/ep1/quest/ep1.quest','research/q307_extracted/json/ep1/quest/ep1.quest.json')){
 if(!$pins.ContainsKey((Bound $helper))){throw "Unbound required source: $helper"}
}
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly
. (Join-Path $workspace 'tools/shark_b7_2_helpers.ps1')
[void](B71Parser)
$native=@{};$new=@{};$wanted=@{};$keys=@{}
foreach($p in $m.native_sources.PSObject.Properties){
 if($p.Name -cnotmatch '^(base|ep1)\\' -or $p.Value -cnotmatch '^[A-F0-9]{64}$'){throw 'Invalid native source'}
 $witness=@($m.source_pins.PSObject.Properties|Where-Object {($_.Name -match '/raw/(.+)$') -and ($Matches[1].Replace('/','\') -ceq $p.Name) -and $_.Value -ceq $p.Value})
 if($witness.Count -lt 1){throw 'Native source has no pinned raw witness'}
 $native[$p.Name]=$p.Value;$wanted[$p.Name]=$p.Value
}
if(!$native.ContainsKey('ep1\quest\ep1.quest')){throw 'Actual root witness required'}
foreach($r in $m.resources.PSObject.Properties){
 if($r.Name -cnotmatch '^towercontinued\\dogtown_dt1\\' -or $r.Name -match '\.\.' -or $native.ContainsKey($r.Name)){throw 'Invalid new resource'}
 if((SHA (Join-Path (Join-Path $build 'source') $r.Name)) -cne $r.Value){throw 'Built resource drift'}
 $new[$r.Name]=$r.Value;$wanted[$r.Name]=$r.Value
}
foreach($depot in $wanted.Keys){$key=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot);if($keys.ContainsKey($key)){throw 'FNV collision'};$keys[$key]=$depot}
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077';$modRoot=Join-Path $game 'archive/pc/mod'
if(Test-Path -LiteralPath (Join-Path $modRoot 'modlist.txt')){throw 'Explicit load order needs separate review'}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$mods=@(Get-ChildItem -LiteralPath $modRoot -Filter '*.archive' -File|Sort-Object Name)
$xls=@(Get-ChildItem -LiteralPath $modRoot -Filter '*.xl' -File|Sort-Object Name)
if($xls.Count -ne @($m.installed_xl).Count){throw 'Installed XL set changed'}
$xlPins=@{}
foreach($x in $m.installed_xl){
 if($x.name -cnotin $xls.Name -or $xlPins.ContainsKey($x.name)){throw 'Installed XL identity changed'}
 $path=Join-Path $modRoot $x.name;if((SHA $path) -cne $x.sha256){throw 'Installed XL hash changed'};$xlPins[$x.name]=$x.sha256
}
$inventory=@(B72Inventory $game)
# B72Inventory returns OrderedDictionary; Select-Object does not expose its
# keys like a deserialized PSCustomObject. Normalize both by explicit fields.
function InjectionRow($entry){[pscustomobject]@{path=$entry.path;node=[int]$entry.node;id=[int]$entry.id;source=$entry.source;source_sha256=$entry.source_sha256}|ConvertTo-Json -Compress}
$old=@($m.installed_injections|ForEach-Object {InjectionRow $_}|Sort-Object)
$current=@($inventory|ForEach-Object {InjectionRow $_}|Sort-Object)
if(($old -join '|') -cne ($current -join '|')){throw 'Installed injection inventory drift'}
$archiveRows=@();$overrides=@()
foreach($f in $mods){
 $hash=SHA $f.FullName;$ar=$null
 if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($f.FullName,$hs,[ref]$ar).ToString() -ne 'NoError'){throw 'Invalid installed archive'}
 foreach($key in $ar.Files.Keys){if($keys.ContainsKey([uint64]$key)){throw "Installed resource collision: $($f.Name) $($keys[[uint64]$key])"}}
 if((SHA $f.FullName) -cne $hash){throw 'Installed archive changed'}
 $archiveRows+=,@{name=$f.Name;sha256=$hash}
}
$official=@();$found=@{};$actualRootIds=$null
$officialFiles=@(Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc/content'),(Join-Path $game 'archive/pc/ep1') -Filter '*.archive' -File|Sort-Object FullName)
foreach($f in $officialFiles){
 $before=Get-Item -LiteralPath $f.FullName;$ar=$null
 if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($f.FullName,$hs,[ref]$ar).ToString() -ne 'NoError'){throw 'Invalid official archive'}
 foreach($key in $ar.Files.Keys){if($keys.ContainsKey([uint64]$key)){
  $depot=$keys[[uint64]$key];if(!$native.ContainsKey($depot)){throw 'New resource collides with official game'}
  $hash=ExtractSHA $ar.Files[$key];if($hash -cne $native[$depot]){throw "Official source byte mismatch: $depot"}
  $found[$depot]=$hash;$official+=,@{path=$depot;archive=$f.FullName;sha256=$hash}
  if($depot -ceq 'ep1\quest\ep1.quest'){
   $mem=[IO.MemoryStream]::new();try{
    $ar.Files[$key].Extract($mem);$mem.Position=0;$cr=$null
    if(([WolvenKit.RED4.Archive.IO.CR2WReader]::new($mem)).ReadFile([ref]$cr,$true).ToString() -ne 'NoError'){throw 'Cannot decode official root'}
    $actualRootIds=@($cr.RootChunk.Graph.Chunk.Nodes|ForEach-Object {[int]::Parse($_.Chunk.Id.ToString(),[Globalization.CultureInfo]::InvariantCulture)})
   }finally{$mem.Dispose()}
  }
 }}
 $after=Get-Item -LiteralPath $f.FullName
 if($before.Length -ne $after.Length -or $before.LastWriteTimeUtc -ne $after.LastWriteTimeUtc){throw 'Official archive changed'}
}
if($found.Count -ne $native.Count -or $null -eq $actualRootIds){throw 'Incomplete official witnesses'}
$frozen=Get-Content -LiteralPath (Join-Path $workspace 'research/q307_extracted/json/ep1/quest/ep1.quest.json') -Raw|ConvertFrom-Json
if((@($actualRootIds|Sort-Object)-join '|') -cne (@($frozen.Data.RootChunk.graph.Data.nodes.Data.id|Sort-Object)-join '|')){throw 'Frozen root IDs differ from current official'}
$newIds=@();foreach($boot in $m.boots){
 if(!$new.ContainsKey($boot)){throw 'Unpacked injection'}
 $id=B72Id ($boot+':1')
 if($id -ne (B72IdIndependent ($boot+':1')) -or $id -in $actualRootIds -or $id -in @($inventory.id) -or $id -in $newIds){throw 'Boot CRC collision'}
 $newIds+=,$id
}
if(($newIds -join '|') -cne (@($m.injection_ids)-join '|')){throw 'Build injection IDs differ'}
$expectedXL=B71Render @($m.boots)
if((Get-Content -LiteralPath (Join-Path $build 'TowerContinued_Dogtown_DT1.archive.xl') -Raw) -cne $expectedXL){throw 'New XL differs from declared boots'}
$packed=$null;$archivePath=Join-Path $build 'TowerContinued_Dogtown_DT1.archive'
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archivePath,$hs,[ref]$packed).ToString() -ne 'NoError' -or $packed.Files.Count -ne $new.Count){throw 'Invalid packed bundle'}
foreach($entry in $packed.Files.Values){if(!$new.ContainsKey($entry.Name) -or (ExtractSHA $entry) -cne $new[$entry.Name]){throw 'Packed resource mismatch'}}
foreach($p in $pins.GetEnumerator()){if((SHA $p.Key) -cne $p.Value){throw 'Source changed during audit'}}
foreach($a in $archiveRows){if((SHA (Join-Path $modRoot $a.name)) -cne $a.sha256){throw 'Installed archive drift after scan'}}
foreach($x in $xlPins.GetEnumerator()){if((SHA (Join-Path $modRoot $x.Key)) -cne $x.Value){throw 'XL drift after scan'}}
if((@($mods.Name|Sort-Object)-join '|') -cne (@(Get-ChildItem -LiteralPath $modRoot -Filter '*.archive' -File|ForEach-Object Name|Sort-Object)-join '|')){throw 'Installed archive set changed after scan'}
if((@($xls.Name|Sort-Object)-join '|') -cne (@(Get-ChildItem -LiteralPath $modRoot -Filter '*.xl' -File|ForEach-Object Name|Sort-Object)-join '|')){throw 'Installed XL set changed after scan'}
$r=@{status='PASS_NOT_LIVE';build_sha256=SHA $manifest;checker_sha256=SHA $PSCommandPath;official=$official;official_comparisons=$native.Count;overrides=$overrides;official_overrides=@();installed_archives=$archiveRows;installed_xls=@($m.installed_xl);native_root_ids=$actualRootIds;injection_ids=$newIds;installed_injections=$inventory.Count;packed_readbacks=$new.Count;modlist_absent=$true;native_graph_live_proof=$false;game_writes=0}
[IO.File]::WriteAllText($output,($r|ConvertTo-Json -Depth 25),[Text.UTF8Encoding]::new($false))
@{status=$r.status;official=$native.Count;archives=$mods.Count;xl=$xls.Count;boots=$newIds.Count;packed=$new.Count}|ConvertTo-Json
