param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\misty_viktor_world'
$prior=Get-Content (Join-Path $audit 'street_r3_manifest.json') -Raw|ConvertFrom-Json
$plan=Get-Content (Join-Path $audit 'street_selection_plan.json') -Raw|ConvertFrom-Json
$overlap=Get-Content (Join-Path $audit 'overlap_source_audit.json') -Raw|ConvertFrom-Json
$out=Join-Path $WorkspaceRoot 'build\MistyViktorCleanupR4'
$source=Join-Path $out 'source'
New-Item -ItemType Directory -Force $source|Out-Null
foreach($path in $prior.resources){
 $src=Join-Path $WorkspaceRoot ('build\MistyViktorStreetR3\source\'+$path)
 $dst=Join-Path $source $path
 New-Item -ItemType Directory -Force (Split-Path -Parent $dst)|Out-Null
 Copy-Item -LiteralPath $src -Destination $dst -Force
}
function ReadWorld($path){
 $stream=[IO.File]::OpenRead($path)
 try{
  $reader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($stream)
  $handler=[WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e) return ($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])}
  $reader.add_ParsingError($handler);$file=$null
  if($reader.ReadFile([ref]$file,$true).ToString() -ne 'NoError'){throw "World parse failure: $path"}
  return $file
 }finally{$stream.Dispose()}
}
$selected=@($plan.source_ranges|Where-Object {$_.selected.Count -gt 0})
$police=@($overlap.r3_police_scene_candidates)
if($police.Count -ne 24){throw "Expected exactly 24 reviewed police placements, found $($police.Count)"}
$removed=[Collections.Generic.List[object]]::new()
$emptySlots=[Collections.Generic.List[int]]::new()
foreach($slot in 0..($selected.Count-1)){
 $row=$selected[$slot]
 $indices=@{};foreach($item in $row.selected){$indices[[int]$item.data_index]=$true}
 $candidates=@($police|Where-Object {$row.raw_path.Replace('/','\').EndsWith($_.sector.Replace('/','\')) -and $indices.ContainsKey([int]$_.data_index)})
 if($candidates.Count -eq 0){continue}
 $exclude=@{};foreach($item in $candidates){
  $key=[int]$item.data_index
  if($exclude.ContainsKey($key)){throw "Duplicate police source index $key"}
  $exclude[$key]=$item
 }
 $path=Join-Path $source "towercontinued\misty_viktor_world\street_$slot.streamingsector"
 $file=ReadWorld $path;$root=$file.RootChunk
 $nodes=@($root.Nodes);$data=@($root.NodeData.Data)
 if($data.Count -ne $row.selected.Count){throw "R3 street sector $slot drifted"}
 $root.Nodes.Clear();$root.NodeData.Data.Clear();$nodeMap=@{}
 for($ordinal=0;$ordinal -lt $row.selected.Count;$ordinal++){
  $item=$row.selected[$ordinal];$old=$data[$ordinal]
  if([uint64]::Parse($old.Id.ToString()) -ne [uint64](720000000000000+($slot*10000)+$ordinal)){throw "R3 street ID drifted at $slot/$ordinal"}
  if($exclude.ContainsKey([int]$item.data_index)){
   $match=$exclude[[int]$item.data_index]
   if([int]$item.node_index -ne [int]$match.node_index -or $item.type -ne $match.type){throw "Police source mismatch at $slot/$ordinal"}
   $removed.Add([pscustomobject]@{slot=$slot;ordinal=$ordinal;source_data_index=[int]$item.data_index;type=$item.type;name=$match.name})
   continue
  }
  $index=[int]::Parse($old.NodeIndex.ToString())
  if(-not $nodeMap.ContainsKey($index)){$nodeMap[$index]=$root.Nodes.Count;[void]$root.Nodes.Add($nodes[$index])}
  $old.NodeIndex=[WolvenKit.RED4.Types.CUInt16]::op_Implicit([uint16]$nodeMap[$index])
  [void]$root.NodeData.Data.Add($old)
 }
 if($root.NodeData.Data.Count -eq 0){$emptySlots.Add($slot)}
 else{
  Write-Cr2wFile $file $path
  Export-Cr2wJson (ReadWorld $path) (Join-Path $audit "cleanup_r4_street_$slot.json")
 }
}
if($removed.Count -ne 24){throw "Removed $($removed.Count) rather than 24 police placements"}
if($emptySlots.Count -ne 1 -or $emptySlots[0] -ne 3){throw "Unexpected all-police street sectors: $($emptySlots -join ',')"}
$blockDepot='towercontinued\misty_viktor_world\street.streamingblock'
$blockPath=Join-Path $source $blockDepot
$block=ReadWorld $blockPath
if($block.RootChunk.Descriptors.Count -ne 12){throw 'R3 street block descriptor drifted'}
foreach($slot in @($emptySlots|Sort-Object -Descending)){
 $expected="towercontinued\misty_viktor_world\street_$slot.streamingsector"
 if($block.RootChunk.Descriptors[$slot].Data.DepotPath.ToString() -ne $expected){throw "Street descriptor $slot drifted"}
 $block.RootChunk.Descriptors.RemoveAt($slot)
 $exact=Join-Path $source $expected
 if(-not [IO.Path]::GetFullPath($exact).StartsWith([IO.Path]::GetFullPath($source)+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'Unsafe generated sector path'}
 Remove-Item -LiteralPath $exact
}
Write-Cr2wFile $block $blockPath
Export-Cr2wJson (ReadWorld $blockPath) (Join-Path $audit 'cleanup_r4_block.json')
$phaseDepot='towercontinued\misty_viktor_world\shell_optin.questphase'
$phase=Read-Cr2wFile (Join-Path $source $phaseDepot)
$graph=$phase.RootChunk.Graph.Chunk
if($graph.Nodes.Count -ne 21){throw 'R3 graph drifted'}
foreach($node in $graph.Nodes){foreach($socket in $node.Chunk.Sockets){$socket.Chunk.Connections.Clear()}}
$revision=(Get-QuestNode $graph 18).Type.Chunk
if($revision.FactName.ToString() -ne 'PTFRMV_Revision' -or [int]$revision.Value -ne 3){throw 'R3 revision drifted'}
$revision.Value=[int32]4
$cleanup=Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\q307_extracted\raw\ep1\quest\main_quests\q307\phases\q307_cleanup.questphase')
$node=(Get-QuestNode $cleanup.RootChunk.Graph.Chunk 22).DeepCopy();$node.Id=[uint16]21
foreach($socket in $node.Sockets){$socket.Chunk.Connections.Clear()}
$owner='$/03_night_city/c_watson/little_china/loc_mystic_mistys_ripperdoc_prefabH2DWJJI/#loc_mystic_mistys_ripperdoc_env/#loc_mystic_mistys_ripperdoc_interior'
$matching=@($node.Type.Chunk.Params|Where-Object {$_.GetType().Name -eq 'questTogglePrefabVariant_NodeTypeParams' -and $_.PrefabNodeRef.ToString() -eq '#loc_mystic_mistys_ripperdoc_interior'})
if($matching.Count -ne 1){throw 'Vanilla q307 original Misty hide owner drifted'}
$param=$matching[0].DeepCopy();$states=@($param.VariantStates|Where-Object {$_.Name.ToString() -eq 'q307_hide_misty'})
if($param.VariantStates.Count -ne 1 -or $states.Count -ne 1 -or $states[0].Show.ToString() -notin @('False','0')){throw 'Vanilla q307 hide action drifted'}
$param.PrefabNodeRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($owner)
$node.Type.Chunk.Params.Clear();[void]$node.Type.Chunk.Params.Add($param)
Add-RedHandle $graph.Nodes $node
$edges=@(@(0,'Out',1),@(1,'Out',18),@(18,'Out',2),@(2,'Out',3),@(3,'Out',21),@(21,'Out',10),@(10,'Out',19),@(19,'Out',11),@(11,'Out',12),@(12,'Out',8),@(8,'Out',4),@(4,'Out',5),@(5,'Out',20),@(20,'Out',13),@(13,'True',14),@(14,'Out',15),@(15,'Out',16),@(16,'Out',17),@(17,'Out',6),@(13,'False',6),@(6,'Out',9),@(9,'Out',7),@(7,'Out',2))
foreach($e in $edges){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $graph $e[0]) $e[1]) (Get-QuestSocket (Get-QuestNode $graph $e[2]) 'In'))}
Write-Cr2wFile $phase (Join-Path $source $phaseDepot)
Export-Cr2wJson (Read-Cr2wFile (Join-Path $source $phaseDepot)) (Join-Path $audit 'cleanup_r4_phase.json')
$archive=Join-Path $out 'TowerContinued_MistyViktorShellOptIn.archive'
$hash=[WolvenKit.Common.Services.HashService]::new();$hash.Load()
$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hash,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'R4 archive pack failed'}}finally{$stream.Dispose()}
Copy-Item -LiteralPath ($prior.archive+'.xl') -Destination ($archive+'.xl') -Force
$packed=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hash,[ref]$packed).ToString() -ne 'NoError'){throw 'R4 archive reopen failed'}
$resources=@($prior.resources|Where-Object {$_ -notin @($emptySlots|ForEach-Object {"towercontinued\misty_viktor_world\street_$($_).streamingsector"})})
if(@(Compare-Object @($resources|Sort-Object) @($packed.Files.Values|ForEach-Object {$_.Name}|Sort-Object)).Count){throw 'R4 packed scope mismatch'}
$manifest=[ordered]@{status='BUILT_R4_CLEANUP_NOT_INSTALLED_OR_LIVE';archive=$archive;sha256=(Get-FileHash $archive).Hash;xl_sha256=(Get-FileHash ($archive+'.xl')).Hash;resources=$resources;removed_empty_slots=@($emptySlots);police_removed=@($removed);police_removed_count=$removed.Count;passive_placements=764;native_hide_owner=$owner;native_hide_variant='q307_hide_misty';native_hide_show=$false;native_hide_from_vanilla_q307_cleanup_node=22;edges=$edges;guards=$prior.guards;actors=0;native_scene_starts=0;story_fact_writes=0;live_tested=$false}
[IO.File]::WriteAllText((Join-Path $audit 'cleanup_r4_manifest.json'),($manifest|ConvertTo-Json -Depth 7))
[pscustomobject]@{status=$manifest.status;sha256=$manifest.sha256;police_removed=$removed.Count;resources=$resources.Count}|ConvertTo-Json
