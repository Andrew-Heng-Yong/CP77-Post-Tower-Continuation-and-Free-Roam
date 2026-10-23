param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\afterlife_world'
$source=Join-Path $WorkspaceRoot 'build\AfterlifeR1\patrons_source'
$prefix='towercontinued\afterlife_r1\patrons_'
$owner='$/03_night_city/c_watson/little_china/#loc_q103_afterlife/#loc_q103_afterlife_env'
$variant='PTFRAL1_Patrons'
function ReadWorld([string]$path){
 $s=[IO.File]::OpenRead($path)
 try{$rd=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($s);$rd.add_ParsingError([WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e) return ($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])});$f=$null;if($rd.ReadFile([ref]$f,$true).ToString() -ne 'NoError'){throw "Parse failed $path"};return $f}finally{$s.Dispose()}
}
function Ref([string]$s){return [WolvenKit.RED4.Types.NodeRef]::op_Implicit($s)}
function Name([string]$s){return [WolvenKit.RED4.Types.CName]::op_Implicit($s)}
function Hash([string]$s){return (Ref $s).GetRedHash()}
$original=ReadWorld (Join-Path $WorkspaceRoot 'research\phase2b_p4\staging_scan\ep1_1_nightcity\raw\base\worlds\03_night_city\_compiled\default\always_loaded_1.streamingsector')
$regs=@($original.RootChunk.Nodes|Where-Object {$_.Chunk.GetType().Name -eq 'worldCommunityRegistryNode'})
$registrySource=$original.RootChunk.Nodes[3256].Chunk
$persistentIndex=@{}
foreach($reg in $regs){foreach($pd in $reg.Chunk.WorkspotsPersistentData){$key=$pd.GlobalNodeId.Hash.ToString();if($persistentIndex.ContainsKey($key)){$persistentIndex[$key]=@($persistentIndex[$key])+@($pd)}else{$persistentIndex[$key]=$pd}}}
$worldFiles=[Collections.Generic.List[object]]::new()
foreach($p in @(Get-ChildItem (Join-Path $audit 'patron_world_sources\raw') -File -Recurse)){$worldFiles.Add(@{path=$p.FullName;file=(ReadWorld $p.FullName)})}
foreach($rel in @('research\misty_viktor_world\r7_showworld_sources\raw\base\worlds\03_night_city\_compiled\default\exterior_-12_8_0_1.streamingsector','research\afterlife_world\hologram_sources\raw\base\worlds\03_night_city\_compiled\default\exterior_-12_7_0_1.streamingsector')){$worldFiles.Add(@{path=(Join-Path $WorkspaceRoot $rel);file=(ReadWorld (Join-Path $WorkspaceRoot $rel))})}
$spotIndex=@{}
foreach($sf in $worldFiles){foreach($d in $sf.file.RootChunk.NodeData.Data){$i=[int]$d.NodeIndex.ToString();$n=$sf.file.RootChunk.Nodes[$i].Chunk;if($n.GetType().Name -eq 'worldAISpotNode'){$h=(Hash $d.QuestPrefabRefHash.ToString()).ToString();if($h -ne '0'){$spotIndex[$h]=@{file=$sf.file;path=$sf.path;node=$i;data=$d;original=$n;ref=$d.QuestPrefabRefHash.ToString()}}}}}
$r11=Join-Path $WorkspaceRoot 'build\MistyViktorStreetR11\source\towercontinued\misty_viktor_world'
$regFile=ReadWorld (Join-Path $r11 'street_people_r11_registry.streamingsector')
$spotFile=ReadWorld (Join-Path $r11 'street_people_r11_spots.streamingsector')
$regPlacement=$regFile.RootChunk.NodeData.Data[0].DeepCopy()
$areaPlacement=$regFile.RootChunk.NodeData.Data[1].DeepCopy()
$registry=$regFile.RootChunk.Nodes[0].Chunk.DeepCopy()
foreach($f in @($regFile,$spotFile)){$f.RootChunk.Nodes.Clear();$f.RootChunk.NodeData.Data.Clear();$f.RootChunk.NodeRefs.Clear()}
$registry.CommunitiesData.Clear();$registry.WorkspotsPersistentData.Clear();$registry.DebugName=Name 'PTFRAL1_PatronsRegistry'
$rows=[Collections.Generic.List[object]]::new();$spotRows=[Collections.Generic.List[object]]::new();$spotMap=@{};$areas=[Collections.Generic.List[object]]::new()
foreach($spec in @(@{index=7725;ref='$/03_night_city/#PTFRAL1_Crowd';original='$/03_night_city/c_watson/little_china/#loc_q103_afterlife/loc_q103_afterlife_questdesign_prefabPGWI5FY/#q103_pr_afterlife/#q103_com_afterlife_crowd';role='patron'},@{index=115;ref='$/03_night_city/#PTFRAL1_Emmerick';original='#emmerick';role='emmerick'})){
 $item=$registrySource.CommunitiesData[$spec.index].DeepCopy();$oldId=$item.CommunityId.EntityId.Hash.ToString();$newId=Hash $spec.ref
 $item.Template.Chunk.SpawnSetReference=Name 'None';$item.Template.Chunk.CrowdEntries.Clear()
 $candidates=@($original.RootChunk.Nodes|Where-Object {$_.Chunk.GetType().Name -like 'worldCompiledCommunityAreaNode*' -and $_.Chunk.SourceObjectId.Hash.ToString() -eq $oldId})
 $areaDatum=$areaPlacement.DeepCopy()
 foreach($wf in $worldFiles){for($ai=0;$ai -lt $wf.file.RootChunk.Nodes.Count;$ai++){$an=$wf.file.RootChunk.Nodes[$ai];if($an.Chunk.GetType().Name -like 'worldCompiledCommunityAreaNode*' -and $an.Chunk.SourceObjectId.Hash.ToString() -eq $oldId){$candidates+=@($an);$areaDatum=@($wf.file.RootChunk.NodeData.Data|Where-Object {$_.NodeIndex.ToString() -eq $ai.ToString()})[0].DeepCopy()}}}
 if($candidates.Count -ne 1){throw "Compiled area count $($candidates.Count) for $oldId"}
 $area=$candidates[0].Chunk.DeepCopy();$area.SourceObjectId.Hash=$newId;$area.SourcePrefabHash=[uint64]0;$area.DebugName=Name ('PTFRAL1_'+$spec.role)
 $selected=@($item.Template.Chunk.Entries|Where-Object {$_.Chunk.EntryName.ToString() -ne 'crowd_female_tiny_mike'})
 $originalInitial=@($item.EntriesInitialState);$originalAreaEntries=@($area.Area.Chunk.EntriesData)
 $item.Template.Chunk.Entries.Clear();$item.EntriesInitialState.Clear();$area.Area.Chunk.EntriesData.Clear();$item.CommunityId.EntityId.Hash=$newId
 foreach($entry in $selected){
  $e=$entry.DeepCopy();$entryName=$e.Chunk.EntryName.ToString()
  if($e.Chunk.Initializers.Count -ne 0){throw "Unexpected entry initializers: $entryName"}
  $phaseName=if($spec.role -eq 'emmerick'){'q005_emmerick_bouncer'}else{'q103'}
  $phase=@($e.Chunk.Phases|Where-Object {$_.Chunk.PhaseName.ToString() -eq $phaseName})
  if($phase.Count -ne 1){throw "Phase ambiguity $entryName"}
  $phase=$phase[0].DeepCopy();$e.Chunk.Phases.Clear();[void]$e.Chunk.Phases.Add($phase)
  $ae=@($originalAreaEntries|Where-Object {$_.EntryName.ToString() -eq $entryName})[0].DeepCopy()
  $ap=@($ae.PhasesData|Where-Object {$_.EntryPhaseName.ToString() -eq $phaseName})[0].DeepCopy();$ae.PhasesData.Clear();[void]$ae.PhasesData.Add($ap)
  $entrySpots=[Collections.Generic.List[string]]::new()
  foreach($tp in $ap.TimePeriodsData){foreach($id in $tp.SpotNodeIds){
   $key=$id.Hash.ToString()
   if(-not $spotMap.ContainsKey($key)){
    if(-not $spotIndex.ContainsKey($key)){throw "Missing original workspot $key for $entryName"}
    $s=$spotIndex[$key];$n=$s.original.DeepCopy();$d=$s.data.DeepCopy();$slot=$spotFile.RootChunk.Nodes.Count;$privateRef='$/03_night_city/#PTFRAL1_PatronSpot'+$slot;$privateHash=Hash $privateRef
    if($null -eq $n.Spot.Chunk){throw "Null workspot $($s.ref)"}
    $n.SourcePrefabHash=[uint64]0;$n.DebugName=Name ('PTFRAL1_PatronSpot'+$slot)
    $d.Id=[uint64](760000000001000+$slot);$d.NodeIndex=[uint16]$slot;$d.QuestPrefabRefHash=Ref $privateRef;$d.UkHash1=Ref ''
    Add-RedHandle $spotFile.RootChunk.Nodes $n;[void]$spotFile.RootChunk.NodeData.Data.Add($d);[void]$spotFile.RootChunk.NodeRefs.Add((Ref $privateRef))
    if(-not $persistentIndex.ContainsKey($key)){throw "Missing persistent descriptor $key"}
    $pds=@($persistentIndex[$key]);if($pds.Count -ne 1){throw "Selected persistent descriptor ambiguous $key"};$pd=$pds[0].DeepCopy();$pd.GlobalNodeId.Hash=$privateHash;[void]$registry.WorkspotsPersistentData.Add($pd)
    $spotMap[$key]=@{ref=$privateRef;hash=$privateHash;oldref=$s.ref}
    $spotRows.Add(@{source=[IO.Path]::GetRelativePath($WorkspaceRoot,$s.path);source_node=$s.node;source_ref=$s.ref;source_hash=$key;private_ref=$privateRef;private_hash=$privateHash.ToString();animation=$n.Spot.Chunk.Resource.DepotPath.ToString();position=@($d.Position.X.ToString(),$d.Position.Y.ToString(),$d.Position.Z.ToString())})
   }
   $id.Hash=$spotMap[$key].hash;$entrySpots.Add($spotMap[$key].ref)
  }}
  foreach($tp in $phase.Chunk.TimePeriods){for($k=0;$k -lt $tp.SpotNodeRefs.Count;$k++){$short=$tp.SpotNodeRefs[$k].ToString();$maps=@($spotMap.Values|Where-Object {$_.oldref.EndsWith('/'+$short) -or $_.oldref -eq $short});if($maps.Count -ne 1){throw "Explicit alias mapping ambiguity $entryName $short"};$tp.SpotNodeRefs[$k]=Ref $maps[0].ref}}
  $initial=@($originalInitial|Where-Object {$_.EntryName.ToString() -eq $entryName})[0].DeepCopy();$initial.EntryActiveOnStart=$false;$initial.InitialPhaseName=Name $phaseName
  [void]$item.Template.Chunk.Entries.Add($e);[void]$item.EntriesInitialState.Add($initial);[void]$area.Area.Chunk.EntriesData.Add($ae)
  $rows.Add(@{entry=$entryName;phase=$phaseName;role=$spec.role;private_spawner=$spec.ref;original_spawner=$spec.original;original_type=if($spec.role -eq 'emmerick'){'spawnset'}else{'community'};original_entry=$entryName;original_phase=if($spec.role -eq 'emmerick'){'None'}else{$phaseName};original_community_hash=$oldId;quantity=($phase.Chunk.TimePeriods|ForEach-Object {[int]$_.Quantity.ToString()}|Measure-Object -Maximum).Maximum;refs=@($entrySpots);readiness_refs=@($entrySpots);record=$e.Chunk.CharacterRecordId.ToString()})
 }
 if($spec.role -eq 'emmerick'){
  # The original non-streamable spawn-set area has no sector placement.
  # Anchor our private metadata at its selected authored bouncer workspot.
  $areaDatum=$spotFile.RootChunk.NodeData.Data[$spotFile.RootChunk.NodeData.Data.Count-1].DeepCopy()
 }
 [void]$registry.CommunitiesData.Add($item);$areas.Add(@{node=$area;ref=$spec.ref;placement=$areaDatum})
}
foreach($h in $spotFile.RootChunk.Nodes){$n=$h.Chunk;foreach($p in @(@{obj=$n;key='LookAtTarget'},@{obj=$n.Spot.Chunk;key='MasterNodeRef'})){$short=$p.obj.($p.key).ToString();if($short -notin @('0','')){$matches=@($spotMap.Values|Where-Object {$_.oldref.EndsWith('/'+$short) -or $_.oldref -eq $short});if($matches.Count -ne 1){throw "Dependent spot outside selected cohort: $short"};$p.obj.($p.key)=Ref $matches[0].ref}}}
Add-RedHandle $regFile.RootChunk.Nodes $registry
$regPlacement.Id=[uint64]760000000001500;$regPlacement.NodeIndex=[uint16]0;$regPlacement.QuestPrefabRefHash=Ref '$/03_night_city/#PTFRAL1_PatronsRegistry';[void]$regFile.RootChunk.NodeData.Data.Add($regPlacement);[void]$regFile.RootChunk.NodeRefs.Add($regPlacement.QuestPrefabRefHash)
foreach($a in $areas){$idx=$regFile.RootChunk.Nodes.Count;Add-RedHandle $regFile.RootChunk.Nodes $a.node;$d=$a.placement.DeepCopy();$d.Id=[uint64](760000000001500+$idx);$d.NodeIndex=[uint16]$idx;$d.QuestPrefabRefHash=Ref $a.ref;[void]$regFile.RootChunk.NodeData.Data.Add($d);[void]$regFile.RootChunk.NodeRefs.Add($d.QuestPrefabRefHash)}
$resources=@(($prefix+'registry.streamingsector'),($prefix+'spots.streamingsector'),($prefix+'world.streamingblock'))
Write-Cr2wFile $regFile (Join-Path $source $resources[0]);Write-Cr2wFile $spotFile (Join-Path $source $resources[1])
$block=ReadWorld (Join-Path $r11 'street_people_r11.streamingblock')
for($i=0;$i -lt 2;$i++){$block.RootChunk.Descriptors[$i].Data=[Activator]::CreateInstance($block.RootChunk.Descriptors[$i].GetType().GetProperty('Data').PropertyType,[object[]]@([WolvenKit.RED4.Types.ResourcePath]::op_Implicit($resources[$i])))}
$desc=$block.RootChunk.Descriptors[1];$desc.BlockIndex.RldGridCell=[uint32]8425321
$desc.StreamingBox.Min.X=[single]-1500.0;$desc.StreamingBox.Min.Y=[single]970.0;$desc.StreamingBox.Min.Z=[single]-15.0;$desc.StreamingBox.Max.X=[single]-1390.0;$desc.StreamingBox.Max.Y=[single]1080.0;$desc.StreamingBox.Max.Z=[single]50.0
$v=$desc.Variants[0];$v.Name=Name $variant;$v.NodeRef=Ref $owner;$v.VariantId=[uint32]3917072731
Write-Cr2wFile $block (Join-Path $source $resources[2])
foreach($depot in $resources){Export-Cr2wJson (ReadWorld (Join-Path $source $depot)) (Join-Path $audit ([IO.Path]::GetFileName($depot)+'.json'))}
$manifest=[ordered]@{status='BUILT_PATRONS_WORLD_LIVE_PENDING';source_root=$source;resources=$resources;block_depot=$resources[2];variant=$variant;variant_name=$variant;variant_owner=$owner;entries=@($rows);workspots=@($spotRows);entry_count=$rows.Count;maximum_actors=($rows|Measure-Object quantity -Sum).Sum;workspot_count=$spotRows.Count;excluded_entries=@('crowd_female_tiny_mike');initially_active=0;original_overrides=0;hashes=@($resources|ForEach-Object {@{depot=$_;sha256=(Get-FileHash (Join-Path $source $_)).Hash}})}
[IO.File]::WriteAllText((Join-Path $audit 'patrons_manifest.json'),($manifest|ConvertTo-Json -Depth 20),[Text.UTF8Encoding]::new($false))
[pscustomobject]$manifest|Select-Object status,entry_count,maximum_actors,workspot_count|ConvertTo-Json
