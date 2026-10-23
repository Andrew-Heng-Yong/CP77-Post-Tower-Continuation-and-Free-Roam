param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$audit=Join-Path $WorkspaceRoot 'research\misty_viktor_world'
$base=Join-Path $WorkspaceRoot 'research\phase2b_p4\staging_scan\ep1_1_nightcity\json\base\worlds\03_night_city\_compiled\default'
$variantName='q307_fast_travel_terminal_cutscene_hide'
$owner='$/03_night_city/c_watson/little_china/#little_china_data_terminals'
function Root([string]$path){return (Get-Content -LiteralPath $path -Raw|ConvertFrom-Json -Depth 100).Data.RootChunk}
$block=Root (Join-Path $base 'blocks\all.streamingblock.json')
$ranges=[Collections.Generic.List[object]]::new()
for($di=0;$di -lt $block.descriptors.Count;$di++){
 $d=$block.descriptors[$di]
 foreach($v in $d.variants){
  if($v.name.'$value' -ne $variantName){continue}
  if($v.nodeRef.'$value' -ne $owner){throw 'Unexpected terminal variant owner'}
  $name=[IO.Path]::GetFileName($d.data.DepotPath.'$value')
  $path=Join-Path $base ($name+'.json');$s=Root $path
  $index=[int]$v.rangeIndex;$start=[int]$s.variantIndices[$index]
  $end=if($index+1 -lt $s.variantIndices.Count){[int]$s.variantIndices[$index+1]}else{$s.nodeData.Data.Count}
  $rows=@(for($i=$start;$i -lt $end;$i++){
   $data=$s.nodeData.Data[$i];$node=$s.nodes[$data.NodeIndex].Data
   $r=[ordered]@{node_data_index=$i;node_index=$data.NodeIndex;type=$node.'$type';debug_name=$node.debugName.'$value';position=@($data.Position.X,$data.Position.Y,$data.Position.Z);quest_prefab_ref=$data.QuestPrefabRefHash.'$value';node=$node}
   [pscustomobject]$r
  })
  $ranges.Add([pscustomobject]@{descriptor=$di;sector=$d.data.DepotPath.'$value';source_json=[IO.Path]::GetRelativePath($WorkspaceRoot,$path);source_sha256=(Get-FileHash -LiteralPath $path).Hash;level=$d.level;variant=$v;range_start=$start;range_end_exclusive=$end;count=$end-$start;members=$rows})
 }
}
if($ranges.Count -ne 2 -or ($ranges|Measure-Object count -Sum).Sum -ne 2){throw 'Expected exactly two singleton terminal ranges'}
if($ranges[0].members[0].type -ne 'worldEntityNode' -or $ranges[1].members[0].type -ne 'worldEntityProxyMeshNode'){throw 'Unexpected terminal range node types'}
$localization=Root (Join-Path $audit 'bradbury_localization\json\base\localization\en-us\onscreens\onscreens.json.json')
$label=@($localization.root.Data.entries|Where-Object {$_.primaryKey -eq '44449'})
if($label.Count -ne 1 -or $label[0].femaleVariant -ne 'Bradbury & Buran'){throw 'Terminal display name mismatch'}
$cutscenePath=Join-Path $WorkspaceRoot 'research\q307_extracted\json\ep1\quest\main_quests\q307\phases\q307_09_cutscene.questphase.json'
$cutscene=Root $cutscenePath
$node=@($cutscene.graph.Data.nodes|Where-Object {$_.Data.id -eq 2})[0].Data.phaseGraph.Data.nodes|Where-Object {$_.Data.id -eq 5}
$param=@($node.Data.type.Data.params|Where-Object {$_.prefabNodeRef.'$value' -eq '#little_china_data_terminals'})
if($param.Count -ne 1 -or $param[0].variantStates.Count -ne 1 -or $param[0].variantStates[0].name.'$value' -ne $variantName -or $param[0].variantStates[0].show -ne 0){throw 'Vanilla cutscene operation mismatch'}
$native=($param[0]|ConvertTo-Json -Depth 20)|ConvertFrom-Json -Depth 20
$native.prefabNodeRef.'$value'=$owner;$native.variantStates[0].show=1
$result=[ordered]@{
 status='READ_ONLY_SOURCE_AUDIT_NOT_BUILT_OR_INSTALLED'
 terminal_record='FastTravelPoints.wat_lch_dataterm_05'
 display_name=$label[0]
 tweakdb_flat_evidence=@{description='Little China FT 05';displayName='LocKey#44449';showInWorld=$true;showOnWorldMap=$true;source='r6/cache/tweakdb.bin; read with WolvenKit TweakDBReader'}
 ranges=@($ranges)
 vanilla_hide=@{resource='ep1\quest\main_quests\q307\phases\q307_09_cutscene.questphase';outer_node=2;inner_node=5;type='questWorldDataManagerNodeDefinition';source_params=$param[0]}
 proposed_native_params=$native
 strict_expectations=@{ranges=2;lod0_dataTerm_entities=1;lod1_proxy_meshes=1;other_nodes=0;new_entities=0;new_markers=0;story_fact_writes=0;map_discovery_writes=0;variantId=2595116582}
 stop_policy='Leave exact original terminal variant enabled after post-completion opt-in Stop; it is ordinary default-on service hidden for final-cutscene composition, with no terminal re-enable in inspected q307 cleanup. This is a deliberate restoration, not exact saved-baseline rollback. Future original quest writer retains ability to hide it because no polling/reassertion is added.'
 live_status='User reports absent physical terminal; activation, prompt, map menu and correct destination remain unverified.'
}
[IO.File]::WriteAllText((Join-Path $audit 'bradbury_terminal_audit.json'),($result|ConvertTo-Json -Depth 60)+[Environment]::NewLine)
[IO.File]::WriteAllText((Join-Path $audit 'bradbury_toggle_params.json'),($native|ConvertTo-Json -Depth 20)+[Environment]::NewLine)
$ranges|ForEach-Object {[pscustomobject]@{sector=$_.sector;descriptor=$_.descriptor;range=$_.variant.rangeIndex;count=$_.count;members=$_.members|Select-Object node_data_index,node_index,type,position}}|ConvertTo-Json -Depth 8
