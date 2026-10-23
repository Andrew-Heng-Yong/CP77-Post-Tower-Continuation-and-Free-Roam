param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\afterlife_world\population_r2'
$out=Join-Path $WorkspaceRoot 'build\AfterlifePopulationR2'
$source=Join-Path $out 'source'
New-Item -ItemType Directory -Force $audit,$source|Out-Null
$r1=Get-Content (Join-Path $WorkspaceRoot 'research\afterlife_world\manifest.json') -Raw|ConvertFrom-Json -Depth 100
$pm=Get-Content (Join-Path $WorkspaceRoot 'research\afterlife_world\patrons_manifest.json') -Raw|ConvertFrom-Json -Depth 100
$facts=[ordered]@{};foreach($p in $r1.guards.psobject.Properties){$facts[$p.Name]=[int]$p.Value}
$policy=[ordered]@{q103_done=1;q103_active=0;q005_done=1;q005_plan_finished=1}
$openworld='$/03_night_city/c_watson/little_china/#loc_q103_afterlife/#loc_q103_afterlife_openworld/'
$controller='$/03_night_city/c_watson/little_china/#loc_q103_afterlife/loc_q103_afterlife_questdesign_prefabPGWI5FY/#afterlife_com_controller'
$door='$/03_night_city/c_watson/little_china/#loc_q103_afterlife/#loc_q103_afterlife_gameplay/#loc_q103_afterlife_devices/{q103_dvc_door_afterlife_main}_prefabZMJZD6A/#q103_dvc_door_afterlife_main'
$sourceHashes=[ordered]@{}
function CheckedPath([string]$relative){$p=Join-Path $WorkspaceRoot $relative;$script:sourceHashes[$relative]=(Get-FileHash -LiteralPath $p).Hash;return $p}
function ReadWorld([string]$path){
 $s=[IO.File]::OpenRead($path)
 try{$rd=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($s);$rd.add_ParsingError([WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e) return ($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])});$f=$null;if($rd.ReadFile([ref]$f,$true).ToString() -ne 'NoError'){throw "Parse failed: $path"};return $f}finally{$s.Dispose()}
}
function Ref([string]$s){return [WolvenKit.RED4.Types.NodeRef]::op_Implicit($s)}
function Name([string]$s){return [WolvenKit.RED4.Types.CName]::op_Implicit($s)}
function Logic([string]$op,$children){$c=[WolvenKit.RED4.Types.questLogicalCondition]::new();$c.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::$op;foreach($v in $children){Add-RedHandle $c.Conditions $v};return $c}
function Fact([string]$name,[int]$value,[bool]$inverse=$false){return New-FactCondition $name $value $(if($inverse){[WolvenKit.RED4.Types.Enums+EComparisonType]::NotEqual}else{[WolvenKit.RED4.Types.Enums+EComparisonType]::Equal})}
function Guard([bool]$inverse=$false){$p=[Collections.Generic.List[object]]::new();foreach($k in $script:facts.Keys){$p.Add((Fact $k $script:facts[$k] $inverse))};return Logic $(if($inverse){'OR'}else{'AND'}) $p}
function Policy([bool]$inverse=$false){$p=[Collections.Generic.List[object]]::new();foreach($k in $script:policy.Keys){$p.Add((Fact $k $script:policy[$k] $inverse))};return Logic $(if($inverse){'OR'}else{'AND'}) $p}
function Loaded([string]$ref,[bool]$inverse=$false){$c=[WolvenKit.RED4.Types.questNodeLoadingCondition]::new();$c.ObjectRef=Ref $ref;$c.Inverted=$inverse;return $c}

# Actual embedded vanilla owners, not the similarly named standalone phase.
$regional=Read-Cr2wFile (CheckedPath 'research\phase2b_p4\vendor_owner\raw\base\open_world\community\watson\little_china\wat_lch_phase.questphase')
$master=@($regional.EmbeddedFiles|Where-Object {$_.FileName.ToString().EndsWith('afterlife_master_phase.questphase')})[0].Content
$ordinary=@($regional.EmbeddedFiles|Where-Object {$_.FileName.ToString().EndsWith('q005_afterlife_phase.questphase')})[0].Content
$triggerTemplate=(Get-QuestNode $master.Graph.Chunk 37).Condition.Chunk.DeepCopy()
$distance=@((Get-QuestNode $master.Graph.Chunk 81).Condition.Chunk.Conditions|Where-Object {$_.Chunk.GetType().Name -eq 'questDistanceCondition'})[0].Chunk.DeepCopy()
if($triggerTemplate.TriggerAreaRef.ToString() -ne '#afterlife_tr_outside_area' -or $distance.Type.Chunk.DistanceDefinition2.Chunk.DistanceValue.ToString() -ne '45'){throw 'Vanilla local controller precedent changed'}
$distance.Type.Chunk.DistanceDefinition1.Chunk.NodeRef2.Reference=Ref $door
$triggers=ReadWorld (CheckedPath 'research\afterlife_world\population_r2_sources\raw\base\worlds\03_night_city\_compiled\default\quest_01e5ca81919708f1.streamingsector')
if($sourceHashes.Values -notcontains '1C28B8C2B884E62BC6C8975DF13551E9F31A359561527BBA4FB68F8FB984724B'){throw 'Trigger source hash changed'}
if($triggers.RootChunk.Nodes.Count -ne 4 -or $triggers.RootChunk.NodeData.Data.Count -ne 4 -or @($triggers.RootChunk.Nodes|Where-Object {$_.Chunk.GetType().Name -ne 'worldTriggerAreaNode'}).Count){throw 'Controller must contain exactly four actor-free triggers'}
$triggerRefs=@($triggers.RootChunk.NodeData.Data|ForEach-Object {$_.QuestPrefabRefHash.ToString()})
function Trigger([string]$short,[bool]$inside){$c=$script:triggerTemplate.DeepCopy();$c.TriggerAreaRef=Ref ($script:controller+'/#afterlife_tr_'+$short);if($c.TriggerAreaRef.ToString() -notin $script:triggerRefs){throw 'Unknown trigger'};$c.Type=if($inside){[WolvenKit.RED4.Types.Enums+questTriggerConditionType]::IsInside}else{[WolvenKit.RED4.Types.Enums+questTriggerConditionType]::IsOutside};return $c}
function Distance([bool]$near){$c=$script:distance.DeepCopy();$c.Type.Chunk.ComparisonType=if($near){[WolvenKit.RED4.Types.Enums+EComparisonType]::Less}else{[WolvenKit.RED4.Types.Enums+EComparisonType]::GreaterOrEqual};return $c}
function TriggerReadiness([bool]$inverse=$false){$cs=@($script:triggerRefs|ForEach-Object {Loaded $_ $inverse});return Logic $(if($inverse){'OR'}else{'AND'}) $cs}
function OutsideAll {return Logic 'AND' @((Trigger 'outside_area' $false),(Trigger 'inside_area' $false),(Trigger 'corridor' $false))}

# Resolve the original identities and all compiled slots. No community/workspot
# resource is cloned or edited. Quota, record, appearance and budget stay native.
$regFile=ReadWorld (CheckedPath 'research\phase2b_p4\staging_scan\ep1_1_nightcity\raw\base\worlds\03_night_city\_compiled\default\always_loaded_1.streamingsector')
$registry=$regFile.RootChunk.Nodes[3256].Chunk
$worlds=[Collections.Generic.List[object]]::new()
foreach($rel in @('research\misty_viktor_world\r7_showworld_sources\raw\base\worlds\03_night_city\_compiled\default\exterior_-12_8_0_1.streamingsector','research\afterlife_world\hologram_sources\raw\base\worlds\03_night_city\_compiled\default\exterior_-12_7_0_1.streamingsector')){$worlds.Add(@{path=$rel;file=(ReadWorld (CheckedPath $rel))})}
$spots=@{}
foreach($w in $worlds){
 $defaultEnd=if($w.file.RootChunk.VariantIndices.Count -gt 1){[int]$w.file.RootChunk.VariantIndices[1].ToString()}else{$w.file.RootChunk.NodeData.Data.Count}
 for($di=0;$di -lt $w.file.RootChunk.NodeData.Data.Count;$di++){$d=$w.file.RootChunk.NodeData.Data[$di];$n=$w.file.RootChunk.Nodes[[int]$d.NodeIndex.ToString()].Chunk;if($n.GetType().Name -eq 'worldAISpotNode' -and $d.QuestPrefabRefHash.ToString().StartsWith($openworld)){$hash=$d.QuestPrefabRefHash.GetRedHash().ToString();if($hash -ne '0'){$spots[$hash]=@{ref=$d.QuestPrefabRefHash.ToString();source=$w.path;node=[int]$d.NodeIndex.ToString();placement=$di;default_range=($di -lt $defaultEnd);workspot=$n.Spot.Chunk.Resource.DepotPath.ToString()}}}}
}
$rows=[Collections.Generic.List[object]]::new();$slots=[Collections.Generic.List[object]]::new()
foreach($spec in @(@{index=1070;ref=($openworld+'#q005_com_afterlife_background');count=20;capacity=66},@{index=8665;ref=($openworld+'#afterlife_com');count=5;capacity=5})){
 $item=$registry.CommunitiesData[$spec.index];$cid=$item.CommunityId.EntityId.Hash.ToString()
 if($cid -ne (Ref $spec.ref).GetRedHash().ToString()){throw 'Original community reference/hash mismatch'}
 $areas=@($regFile.RootChunk.Nodes|Where-Object {$_.Chunk.GetType().Name -like 'worldCompiledCommunityAreaNode*' -and $_.Chunk.SourceObjectId.Hash.ToString() -eq $cid})
 foreach($w in $worlds){$areas+=@($w.file.RootChunk.Nodes|Where-Object {$_.Chunk.GetType().Name -like 'worldCompiledCommunityAreaNode*' -and $_.Chunk.SourceObjectId.Hash.ToString() -eq $cid})}
 if($areas.Count -ne 1){throw 'Original area ambiguity'};$area=$areas[0].Chunk
 $selected=@($item.Template.Chunk.Entries|Where-Object {$spec.index -eq 1070 -or $_.Chunk.EntryName.ToString() -in @('cleaner','mercenary_big','valentino_01','valentino_02','valentino_03')})
 if($selected.Count -ne $spec.count){throw 'Ordinary entry count changed'}
 $total=0
 foreach($e in $selected){
  $e=$e.Chunk;$entry=$e.EntryName.ToString();$ph=@($e.Phases|Where-Object {$_.Chunk.PhaseName.ToString() -eq 'q005'})
  if($ph.Count -ne 1 -or $ph[0].Chunk.TimePeriods.Count -ne 1){throw 'Ordinary phase changed'};$tp=$ph[0].Chunk.TimePeriods[0];$qty=[int]$tp.Quantity.ToString();$total+=$qty
  $ae=@($area.Area.Chunk.EntriesData|Where-Object {$_.EntryName.ToString() -eq $entry})[0];$ap=@($ae.PhasesData|Where-Object {$_.EntryPhaseName.ToString() -eq 'q005'})[0]
  $ids=@($ap.TimePeriodsData[0].SpotNodeIds|ForEach-Object {$_.Hash.ToString()});if($ids.Count -ne $qty){throw 'Configured quota/slot mismatch'}
  $refs=@();$slotIndex=0
  foreach($id in $ids){if(-not $spots.ContainsKey($id)){throw "Missing ordinary spot $entry/$id"};$s=$spots[$id];if(-not $s.default_range){throw "Selected workspot is variant-owned: $entry/$id"};$refs+=@($s.ref);$slots.Add(@{community_id=$cid;entry=$entry;phase='q005';slot=$slotIndex;spot_id=$id;ref=$s.ref;source=$s.source;source_node=$s.node;source_placement=$s.placement;default_range=$true;workspot=$s.workspot});$slotIndex++}
  foreach($short in $tp.SpotNodeRefs){if(@($refs|Where-Object {$_ -eq $short.ToString() -or $_.EndsWith('/'+$short.ToString())}).Count -ne 1){throw 'Template/compiled slot mismatch'}}
  $rows.Add(@{community_id=$cid;spawner=$spec.ref;entry=$entry;phase='q005';quantity=$qty;record=$e.CharacterRecordId.ToString();refs=$refs;area_type=$item.CommunityAreaType.ToString()})
 }
 if($total -ne $spec.capacity){throw 'Ordinary capacity changed'}
}
if($rows.Count -ne 25 -or $slots.Count -ne 71){throw 'Ordinary roster mismatch'}

# Keep legacy graph IDs/sockets and seven other payloads. Saved tokens anywhere
# in the 26 old crowd branches can now only retire, never reactivate that crowd.
foreach($p in $r1.payloads){if((Get-FileHash -LiteralPath $p.source).Hash -ne $p.sha256){throw 'R1 source changed'};$to=Join-Path $source $p.depot;New-Item -ItemType Directory -Force (Split-Path $to)|Out-Null;Copy-Item -LiteralPath $p.source -Destination $to}
$legacy=Read-Cr2wFile (Join-Path $source $r1.population_phase)
$legacyCrowd=@($r1.population_branches|Where-Object {$_.role -eq 'patron'})
foreach($b in $legacyCrowd){$n=Get-QuestNode $legacy.RootChunk.Graph.Chunk ($b.start+2);$a=$n.Actions[1].DeepCopy();$a.Type.Chunk.Action=[WolvenKit.RED4.Types.Enums+populationSpawnerObjectCtrlAction]::Deactivate;$n.Actions.Clear();[void]$n.Actions.Add($a);(Get-QuestNode $legacy.RootChunk.Graph.Chunk ($b.start+4)).Type.Chunk.Value=0}
Write-Cr2wFile $legacy (Join-Path $source $r1.population_phase)
Export-Cr2wJson (Read-Cr2wFile (Join-Path $source $r1.population_phase)) (Join-Path $audit 'legacy_population.json')
$pauseTemplate=(Get-QuestNode $legacy.RootChunk.Graph.Chunk 100).DeepCopy()
$spawnTemplate=(Get-QuestNode $ordinary.Graph.Chunk 41).DeepCopy();$actionTemplate=$spawnTemplate.Actions[0].DeepCopy()
function Pause([int]$id,$c){$n=$script:pauseTemplate.DeepCopy();$n.Id=[uint16]$id;foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()};Set-RedHandleProperty $n Condition $c;return $n}
function Count([int]$id,[string]$name){$n=New-SetFactNode $id $name 1;$n.Type.Chunk.SetExactValue=$false;return $n}
function Spawn([int]$id,$items,[string]$action){$n=$script:spawnTemplate.DeepCopy();$n.Id=[uint16]$id;foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()};$n.Actions.Clear();foreach($r in $items){$a=$script:actionTemplate.DeepCopy();$a.Type.Chunk.Action=[WolvenKit.RED4.Types.Enums+populationSpawnerObjectCtrlAction]::$action;$a.Type.Chunk.SpawnerReference=Ref $r.spawner;$a.Type.Chunk.CommunityEntryName=Name $r.entry;$a.Type.Chunk.CommunityEntryPhaseName=Name $r.phase;[void]$n.Actions.Add($a)};return $n}
function Put($g,$n){Add-RedHandle $g.Nodes $n}
function Link($g,[int]$a,[string]$s,[int]$b,[string]$dest='In'){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $a) $s) (Get-QuestSocket (Get-QuestNode $g $b) $dest))}
function PhaseFile($g){$root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();$root.CookingPlatform=[WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC;Set-RedHandleProperty $root Graph $g;$f=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$f.RootChunk=$root;return $f}
$gateDepot='towercontinued\afterlife_population_r2\gate.questphase';$ownerDepot='towercontinued\afterlife_population_r2\owner.questphase'
$gate=[WolvenKit.RED4.Types.questGraphDefinition]::new()
Put $gate (New-InputNode 0 'In1');Put $gate (Pause 1 (Guard));Put $gate (New-ConditionNode 2 (Guard))
$child=[WolvenKit.RED4.Types.questPhaseNodeDefinition]::new();$child.Id=[uint16]3;$child.PhaseResource=[Activator]::CreateInstance($child.GetType().GetProperty('PhaseResource').PropertyType,[object[]]@([WolvenKit.RED4.Types.ResourcePath]::op_Implicit($ownerDepot)))
[void](New-QuestSocket $child 'CutDestination' ([WolvenKit.RED4.Types.Enums+questSocketType]::CutDestination));[void](New-QuestSocket $child 'In1' ([WolvenKit.RED4.Types.Enums+questSocketType]::Input));Put $gate $child
Link $gate 0 Out 1;Link $gate 1 Out 2;Link $gate 2 False 1;Link $gate 2 True 3 In1
$g=[WolvenKit.RED4.Types.questGraphDefinition]::new()
function MigrationState {return Logic 'AND' @((Guard),(TriggerReadiness),(OutsideAll),(Logic 'AND' @($script:legacyCrowd|ForEach-Object {$_.refs}|Sort-Object -Unique|ForEach-Object {Loaded $_ $true})))}
function EntryState {return Logic 'AND' @((Guard),(Policy),(Fact 'PTFRAL2_Migration' 2),(TriggerReadiness),(Loaded $script:door),(Trigger 'fast_travel' $false),(Logic 'OR' @((Trigger 'outside_area' $true),(Trigger 'inside_area' $true),(Trigger 'corridor' $true))),(Logic 'OR' @((Trigger 'inside_area' $true),(Trigger 'corridor' $true),(Distance $true))))}
function ExitState {return Logic 'OR' @((Guard $true),(Policy $true),(Fact 'PTFRAL2_Migration' 2 $true),(TriggerReadiness $true),(Loaded $script:door $true),(Trigger 'fast_travel' $true),(OutsideAll),(Logic 'AND' @((Trigger 'inside_area' $false),(Trigger 'corridor' $false),(Distance $false))))}
function ActorState($r,[bool]$inverse=$false){$cs=[Collections.Generic.List[object]]::new();$cs.Add($(if($inverse){ExitState}else{EntryState}));$cs.Add((Fact 'PTFRAL2_LocalActive' 1 $inverse));foreach($ref in $r.refs){$cs.Add((Loaded $ref $inverse))};return Logic $(if($inverse){'OR'}else{'AND'}) $cs}
Put $g (New-InputNode 0 'In1');Put $g (New-SetFactNode 1 'PTFRAL2_Registered' 1);Put $g (New-SetFactNode 2 'PTFRAL2_LocalActive' 0);Put $g (New-SetFactNode 3 'PTFRAL2_Migration' 0)
Link $g 0 Out 1;Link $g 1 Out 2;Link $g 2 Out 3
Put $g (Pause 10 (Guard));Put $g (New-ConditionNode 11 (Guard))
$retireRows=@($legacyCrowd|ForEach-Object {@{spawner=$_.private_spawner;entry=$_.entry;phase=$_.phase}})
Put $g (Spawn 12 $retireRows 'Deactivate');Put $g (Count 13 'PTFRAL2_RetireRequests');Put $g (Pause 14 (MigrationState))
$delay=[WolvenKit.RED4.Types.questTimeCondition]::new();$seconds=[WolvenKit.RED4.Types.questRealtimeDelay_ConditionType]::new();$seconds.Seconds=[uint32]1;Set-RedHandleProperty $delay Type $seconds
Put $g (Pause 15 $delay);Put $g (New-ConditionNode 16 (MigrationState));Put $g (New-SetFactNode 17 'PTFRAL2_Migration' 2)
Link $g 3 Out 10;Link $g 10 Out 11;Link $g 11 False 10;Link $g 11 True 12;foreach($i in 12..15){Link $g $i Out ($i+1)};Link $g 16 False 14;Link $g 16 True 17
Put $g (Pause 20 (EntryState));Put $g (New-ConditionNode 21 (EntryState));Put $g (New-SetFactNode 22 'PTFRAL2_LocalActive' 1);Put $g (Count 23 'PTFRAL2_Visits');Put $g (Pause 24 (ExitState));Put $g (New-SetFactNode 25 'PTFRAL2_LocalActive' 0);Put $g (Count 26 'PTFRAL2_Exits')
Link $g 17 Out 20;Link $g 20 Out 21;Link $g 21 False 20;Link $g 21 True 22;foreach($i in 22..25){Link $g $i Out ($i+1)};Link $g 26 Out 20
$index=0
foreach($r in $rows){$i=100+20*$index;$r.start=$i;$r.ready_fact='PTFRAL2_Entry'+$index.ToString('00')+'Owned'
 Put $g (Pause $i (ActorState $r));Put $g (New-ConditionNode ($i+1) (ActorState $r));Put $g (Spawn ($i+2) @($r) 'Activate');Put $g (Count ($i+3) 'PTFRAL2_Acquires');Put $g (New-SetFactNode ($i+4) $r.ready_fact 1);Put $g (Pause ($i+5) (ActorState $r $true));Put $g (Spawn ($i+6) @($r) 'Deactivate');Put $g (Count ($i+7) 'PTFRAL2_Releases');Put $g (New-SetFactNode ($i+8) $r.ready_fact 0)
 Link $g 3 Out $i;Link $g $i Out ($i+1);Link $g ($i+1) False $i;Link $g ($i+1) True ($i+2);foreach($j in 2..7){Link $g ($i+$j) Out ($i+$j+1)};Link $g ($i+8) Out $i;$index++
}
$ownerFile=PhaseFile $g
$prefab=@($master.PhasePrefabs|Where-Object {$_.PrefabNodeRef.ToString() -eq '#afterlife_com_controller'})[0].DeepCopy();$prefab.PrefabNodeRef=Ref $controller;[void]$ownerFile.RootChunk.PhasePrefabs.Add($prefab)
Write-Cr2wFile (PhaseFile $gate) (Join-Path $source $gateDepot);Write-Cr2wFile $ownerFile (Join-Path $source $ownerDepot)
foreach($pair in @(@($gateDepot,'gate.json'),@($ownerDepot,'owner.json'))){Export-Cr2wJson (Read-Cr2wFile (Join-Path $source $pair[0])) (Join-Path $audit $pair[1])}
$resources=@($r1.resources)+@($gateDepot,$ownerDepot)
$disk=@(Get-ChildItem -LiteralPath $source -File -Recurse|ForEach-Object {[IO.Path]::GetRelativePath($source,$_.FullName)})
if(@(Compare-Object ($resources|Sort-Object) ($disk|Sort-Object)).Count){throw 'Unexpected R2 package payload'}
# Keep the installed filename/legacy resource identity; never load R1 and R2 as
# two archives. ArchiveXL only adds the uniquely named, guarded R2 gate.
$archive=Join-Path $out 'TowerContinued_AfterlifeR1.archive'
$xl=Get-Content -LiteralPath ($r1.archive+'.xl');$xl+=@(('    - path: '+$gateDepot),'      parent: ep1\quest\ep1.quest','      input:','        node: [1]','        socket: Out')
[IO.File]::WriteAllLines(($archive+'.xl'),$xl,[Text.UTF8Encoding]::new($false))
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'R2 archive pack failed'}}finally{$stream.Dispose()}
$packed=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -ne 'NoError'){throw 'R2 archive reopen failed'}
if(@(Compare-Object ($resources|Sort-Object) @($packed.Files.Values|ForEach-Object {$_.Name}|Sort-Object)).Count){throw 'Packed resource scope mismatch'}
foreach($e in $packed.Files.Values){$ms=[IO.MemoryStream]::new();try{$e.Extract($ms);$hash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($ms.ToArray()))}finally{$ms.Dispose()};if($hash -ne (Get-FileHash (Join-Path $source $e.Name)).Hash){throw 'Packed byte readback failed'}}
foreach($p in $sourceHashes.Keys){if((Get-FileHash (Join-Path $WorkspaceRoot $p)).Hash -ne $sourceHashes[$p]){throw 'Research source changed'}}
$manifest=[ordered]@{status='BUILT_R2_OFFLINE_VALIDATION_PENDING_NOT_INSTALLED';source_root=$source;archive=$archive;sha256=(Get-FileHash $archive).Hash;xl_sha256=(Get-FileHash ($archive+'.xl')).Hash;resources=$resources;payloads=@($resources|ForEach-Object {@{depot=$_;sha256=(Get-FileHash (Join-Path $source $_)).Hash}});guards=$facts;policy=$policy;entries=@($rows);slots=@($slots);background_entries=20;background_configured_slots=66;ordinary_extra_entries=5;ordinary_extra_slots=5;new_actor_identities=0;legacy_retired_entries=26;legacy_retired_slots=78;gate=$gateDepot;owner=$ownerDepot;gate_nodes=$gate.Nodes.Count;owner_nodes=$g.Nodes.Count;controller_prefab=$controller;controller_triggers=$triggerRefs;door=$door;source_hashes=$sourceHashes;packed_readback_pass=$true;original_overrides=0;story_writes=0;scene_starts=0;runtime_script_changes=0;installed=$false;live_tested=$false;migration='Deactivate only legacy private crowd; wait outside all original local volumes and for all its workspots to unload, then recheck after one second. This is a streaming barrier, not actor-removal acknowledgement.'}
[IO.File]::WriteAllText((Join-Path $audit 'manifest.json'),($manifest|ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false))
[pscustomobject]$manifest|Select-Object status,gate_nodes,owner_nodes,background_entries,background_configured_slots,ordinary_extra_entries,new_actor_identities,sha256|ConvertTo-Json
