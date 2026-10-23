param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\misty_viktor_world'
$prior=Get-Content (Join-Path $audit 'access_r2_manifest.json') -Raw|ConvertFrom-Json
$plan=Get-Content (Join-Path $audit 'street_selection_plan.json') -Raw|ConvertFrom-Json
if($plan.status -ne 'SOURCE_INVENTORY_ONLY_NOT_BUILT_OR_INSTALLED'){throw 'Street selection not reviewed'}
$out=Join-Path $WorkspaceRoot 'build\MistyViktorStreetR3'
$source=Join-Path $out 'source'
New-Item -ItemType Directory -Force $source|Out-Null
$resources=[Collections.Generic.List[string]]::new()
foreach($path in $prior.resources){
 $src=Join-Path $WorkspaceRoot ('build\MistyViktorAccessR2\source\'+$path)
 $dst=Join-Path $source $path
 New-Item -ItemType Directory -Force (Split-Path -Parent $dst)|Out-Null
 Copy-Item -LiteralPath $src -Destination $dst -Force
 $resources.Add($path)
}
$options=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new()
function CloneFile($file){
 $j=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize([WolvenKit.Common.Conversion.RedFileDto]::new($file,$false),$script:options)
 return [WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Deserialize([WolvenKit.Common.Conversion.RedFileDto],$j,$script:options).Data
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
$blockPath=Join-Path $WorkspaceRoot 'research\phase2b_p4\staging_scan\ep1_1_nightcity\raw\base\worlds\03_night_city\_compiled\default\blocks\all.streamingblock'
$block=CloneFile (ReadWorld $blockPath)
$block.RootChunk.Descriptors.Clear()
$streetOwner='$/03_night_city/c_watson/little_china/wlc_02/#wlc_02_b_env'
$streetName='PTFRMV_TowerStreet'
$streetId=[uint32]3917072702
$slot=0;$placements=0;$sectorRows=[Collections.Generic.List[object]]::new()
foreach($row in $plan.source_ranges){
 if($row.selected.Count -eq 0){continue}
 $raw=Join-Path $WorkspaceRoot $row.raw_path
 if((Get-FileHash -LiteralPath $raw).Hash -ne $row.raw_sha256){throw "Street source changed: $raw"}
 $original=ReadWorld $raw;$file=CloneFile $original;$root=$file.RootChunk
 $oldNodes=@($root.Nodes);$oldData=@($root.NodeData.Data)
 $root.Nodes.Clear();$root.NodeData.Data.Clear()
 $ranges=[Activator]::CreateInstance($root.VariantIndices.GetType())
 [void]$ranges.Add([WolvenKit.RED4.Types.CInt32]::op_Implicit(0));$root.VariantIndices=$ranges
 $variantNodes=[Activator]::CreateInstance($root.VariantNodes.GetType())
 [void]$variantNodes.Add([Activator]::CreateInstance($root.VariantNodes.GetType().GetGenericArguments()[0]));$root.VariantNodes=$variantNodes
 $indices=@{};$ordinal=0
 foreach($item in $row.selected){
  if($item.type -notin @('worldStaticMeshNode','worldStaticDecalNode','worldCollisionNode')){throw 'Non-passive street node'}
  $old=[int]$item.node_index
  if($oldNodes[$old].Chunk.GetType().Name -ne $item.type){throw 'Street node selection changed'}
  if(-not $indices.ContainsKey($old)){$indices[$old]=$root.Nodes.Count;[void]$root.Nodes.Add($oldNodes[$old])}
  $data=$oldData[[int]$item.data_index]
  $data.NodeIndex=[WolvenKit.RED4.Types.CUInt16]::op_Implicit([uint16]$indices[$old])
  $data.Id=[uint64](720000000000000+($slot*10000)+$ordinal)
  $data.QuestPrefabRefHash=[WolvenKit.RED4.Types.NodeRef]::op_Implicit('')
  [void]$root.NodeData.Data.Add($data);$ordinal++
 }
 $depot="towercontinued\misty_viktor_world\street_$slot.streamingsector"
 Write-Cr2wFile $file (Join-Path $source $depot)
 $readback=ReadWorld (Join-Path $source $depot)
 Export-Cr2wJson $readback (Join-Path $audit "street_$slot.json")
 $sourceBlock=ReadWorld (Join-Path $WorkspaceRoot ($row.source_block.Replace('\json\','\raw\') -replace '\.json$',''))
 $descriptor=$sourceBlock.RootChunk.Descriptors[[int]$row.descriptor_index].DeepCopy()
 $sourceVariants=@($descriptor.Variants|Where-Object {$_.Name.ToString() -eq 'q307_misty_alley' -and $_.RangeIndex.ToString() -eq $row.variant.rangeIndex.ToString()})
 if($sourceVariants.Count -ne 1){throw 'Source street variant ambiguous'}
 $variant=$sourceVariants[0].DeepCopy();$descriptor.Variants.Clear()
 $variant.Name=[WolvenKit.RED4.Types.CName]::op_Implicit($streetName)
 $variant.NodeRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($streetOwner)
 $variant.EnabledByDefault=$false
 $variant.RangeIndex=[WolvenKit.RED4.Types.CUInt32]::op_Implicit(0)
 $variant.ParentVariantID=[WolvenKit.RED4.Types.CUInt32]::op_Implicit(0)
 $variant.VariantId=[WolvenKit.RED4.Types.CUInt32]::op_Implicit($streetId)
 [void]$descriptor.Variants.Add($variant)
 $descriptor.NumNodeRanges=[WolvenKit.RED4.Types.CUInt32]::op_Implicit(1)
 $descriptor.Data=[Activator]::CreateInstance($descriptor.GetType().GetProperty('Data').PropertyType,[object[]]@([WolvenKit.RED4.Types.ResourcePath]::op_Implicit($depot)))
 [void]$block.RootChunk.Descriptors.Add($descriptor)
 $resources.Add($depot)
 $sectorRows.Add([pscustomobject]@{depot=$depot;source=$row.raw_path;count=$ordinal;node_count=$root.Nodes.Count;source_range=$row.range;source_descriptor=$row.descriptor_index})
 $placements+=$ordinal;$slot++
}
if($slot -ne 12 -or $placements -ne 788){throw "Street selection changed: $slot sectors, $placements placements"}
$blockDepot='towercontinued\misty_viktor_world\street.streamingblock'
Write-Cr2wFile $block (Join-Path $source $blockDepot)
Export-Cr2wJson (ReadWorld (Join-Path $source $blockDepot)) (Join-Path $audit 'street_block.json')
$resources.Add($blockDepot)
$phaseDepot='towercontinued\misty_viktor_world\shell_optin.questphase'
$phase=Read-Cr2wFile (Join-Path $source $phaseDepot)
$graph=$phase.RootChunk.Graph.Chunk
if($graph.Nodes.Count -ne 19){throw 'R2 graph was not preserved'}
foreach($node in $graph.Nodes){foreach($socket in $node.Chunk.Sockets){$socket.Chunk.Connections.Clear()}}
$cleanup=Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\q307_extracted\raw\ep1\quest\main_quests\q307\phases\q307_cleanup.questphase')
function ToggleStreet($id,[bool]$show){
 $n=(Get-QuestNode $script:cleanup.RootChunk.Graph.Chunk 22).DeepCopy();$n.Id=[uint16]$id
 foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()}
 $p=@($n.Type.Chunk.Params|Where-Object {$_.GetType().Name -eq 'questTogglePrefabVariant_NodeTypeParams' -and @($_.VariantStates|Where-Object {$_.Name.ToString() -eq 'q307_zetatech'}).Count})
 if($p.Count -ne 1 -or $p[0].VariantStates.Count -ne 1){throw 'Toggle precedent changed'}
 $single=$p[0].DeepCopy();$single.PrefabNodeRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($script:streetOwner)
 $single.VariantStates[0].Name=[WolvenKit.RED4.Types.CName]::op_Implicit($script:streetName)
 $single.VariantStates[0].Show=$show;$n.Type.Chunk.Params.Clear();[void]$n.Type.Chunk.Params.Add($single)
 return $n
}
$revision=(Get-QuestNode $graph 18).Type.Chunk
if($revision.GetType().Name -ne 'questSetVar_NodeType' -or $revision.FactName.ToString() -ne 'PTFRMV_Revision'){throw 'R2 revision node changed'}
$revision.Value=[int32]3
Add-RedHandle $graph.Nodes (ToggleStreet 19 $true)
Add-RedHandle $graph.Nodes (ToggleStreet 20 $false)
$edges=@(@(0,'Out',1),@(1,'Out',18),@(18,'Out',2),@(2,'Out',3),@(3,'Out',10),@(10,'Out',19),@(19,'Out',11),@(11,'Out',12),@(12,'Out',8),@(8,'Out',4),@(4,'Out',5),@(5,'Out',20),@(20,'Out',13),@(13,'True',14),@(14,'Out',15),@(15,'Out',16),@(16,'Out',17),@(17,'Out',6),@(13,'False',6),@(6,'Out',9),@(9,'Out',7),@(7,'Out',2))
foreach($e in $edges){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $graph $e[0]) $e[1]) (Get-QuestSocket (Get-QuestNode $graph $e[2]) 'In'))}
Write-Cr2wFile $phase (Join-Path $source $phaseDepot)
Export-Cr2wJson (Read-Cr2wFile (Join-Path $source $phaseDepot)) (Join-Path $audit 'street_r3_phase.json')
$xl=Get-Content ($prior.archive+'.xl')
$expected='    - towercontinued\misty_viktor_world\shell.streamingblock'
if(@($xl|Where-Object {$_ -eq $expected}).Count -ne 1){throw 'R2 XL changed'}
$xl=@($xl|ForEach-Object {$_;if($_ -eq $expected){'    - towercontinued\misty_viktor_world\street.streamingblock'}})
$hash=[WolvenKit.Common.Services.HashService]::new();$hash.Load()
$archive=Join-Path $out 'TowerContinued_MistyViktorShellOptIn.archive';$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hash,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'R3 archive pack failed'}}finally{$stream.Dispose()}
[IO.File]::WriteAllLines(($archive+'.xl'),$xl,[Text.UTF8Encoding]::new($false))
$packed=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hash,[ref]$packed).ToString() -ne 'NoError'){throw 'R3 archive reopen failed'}
if(@(Compare-Object @($resources|Sort-Object) @($packed.Files.Values|ForEach-Object {$_.Name}|Sort-Object)).Count){throw 'Packed R3 scope mismatch'}
$manifest=[ordered]@{status='BUILT_R3_PASSIVE_STREET_OPTIN_NOT_INSTALLED_OR_LIVE';archive=$archive;sha256=(Get-FileHash $archive).Hash;xl_sha256=(Get-FileHash ($archive+'.xl')).Hash;resources=@($resources);street_block=$blockDepot;street_owner=$streetOwner;street_variant=$streetName;street_variant_id=$streetId;sectors=@($sectorRows);passive_placements=$placements;edges=$edges;guards=$prior.guards;native_scene_starts=0;story_fact_writes=0;actors=0;live_tested=$false}
[IO.File]::WriteAllText((Join-Path $audit 'street_r3_manifest.json'),($manifest|ConvertTo-Json -Depth 7))
[pscustomobject]@{status=$manifest.status;sha256=$manifest.sha256;sectors=$slot;placements=$placements;resources=$resources.Count}|ConvertTo-Json
