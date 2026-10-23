param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\afterlife_world\idles_r3'
$out=Join-Path $WorkspaceRoot 'build\AfterlifeIdlesR3'
$source=Join-Path $out 'source'
New-Item -ItemType Directory -Force $audit,$source|Out-Null
$hashes=[ordered]@{}
function Checked([string]$relative){$p=Join-Path $WorkspaceRoot $relative;$script:hashes[$relative]=(Get-FileHash -LiteralPath $p).Hash;return $p}
function ReadWorld([string]$p){$s=[IO.File]::OpenRead($p);try{$r=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($s);$r.add_ParsingError([WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e) return ($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])});$f=$null;if($r.ReadFile([ref]$f,$true).ToString() -ne 'NoError'){throw "Cannot parse $p"};return $f}finally{$s.Dispose()}}
function Ref([string]$s){return [WolvenKit.RED4.Types.NodeRef]::op_Implicit($s)}
function Name([string]$s){return [WolvenKit.RED4.Types.CName]::op_Implicit($s)}
$r2=Get-Content (Checked 'research\afterlife_world\population_r2\manifest.json') -Raw|ConvertFrom-Json -Depth 60
$world=ReadWorld (Checked 'research\afterlife_world\patron_world_sources\raw\base\worlds\03_night_city\_compiled\default\quest_9da2b9328cb64d35.streamingsector')
$original=ReadWorld (Checked 'research\phase2b_p4\staging_scan\ep1_1_nightcity\raw\base\worlds\03_night_city\_compiled\default\always_loaded_1.streamingsector')
$community='$/03_night_city/c_watson/little_china/#loc_q103_afterlife/loc_q103_afterlife_questdesign_prefabPGWI5FY/#afterlife_pr_default_community/#q005_com_afterlife_community'
$item=$original.RootChunk.Nodes[3256].Chunk.CommunitiesData[3027]
if($item.CommunityId.EntityId.Hash.ToString() -ne (Ref $community).GetRedHash().ToString()){throw 'Original community identity mismatch'}
# Copy only four independent scene1 workspots, not the containing quest prefab
# (which also contains walkers, story triggers, a police car and other staging).
$prior='build\AfterlifeR1\source\towercontinued\afterlife_r1\'
$regFile=ReadWorld (Checked ($prior+'patrons_registry.streamingsector'))
$spotFile=ReadWorld (Checked ($prior+'patrons_spots.streamingsector'))
$reg=$regFile.RootChunk.Nodes[0].Chunk.DeepCopy();$reg.DebugName=Name 'PTFRAL3_WorkspotRegistry'
$reg.CommunitiesData.Clear();$reg.WorkspotsPersistentData.Clear()
$regPlacement=$regFile.RootChunk.NodeData.Data[0].DeepCopy()
foreach($f in @($regFile,$spotFile)){$f.RootChunk.Nodes.Clear();$f.RootChunk.NodeData.Data.Clear();$f.RootChunk.NodeRefs.Clear()}
$rows=[Collections.Generic.List[object]]::new()
$nodeIndices=@(4,1,5,14)
for($i=0;$i -lt 4;$i++){
 $entry='merc_'+($i+1).ToString('00');$nodeIndex=$nodeIndices[$i]
 $e=@($item.Template.Chunk.Entries|Where-Object {$_.Chunk.EntryName.ToString() -eq $entry})[0].Chunk
 $phase=@($e.Phases|Where-Object {$_.Chunk.PhaseName.ToString() -eq 'scene1'})[0].Chunk
 if($phase.TimePeriods.Count -ne 1 -or $phase.TimePeriods[0].Quantity.ToString() -ne '1' -or $phase.TimePeriods[0].SpotNodeRefs.Count -ne 1){throw 'Unexpected booth quota'}
 $n=$world.RootChunk.Nodes[$nodeIndex].Chunk.DeepCopy();$ds=@($world.RootChunk.NodeData.Data|Where-Object {$_.NodeIndex.ToString() -eq $nodeIndex.ToString()})
 if($ds.Count -ne 1){throw 'Workspot placement ambiguity'};$d=$ds[0].DeepCopy();$oldRef=$d.QuestPrefabRefHash.ToString();$oldHash=$d.QuestPrefabRefHash.GetRedHash().ToString()
 if(-not $oldRef.EndsWith('/'+$phase.TimePeriods[0].SpotNodeRefs[0].ToString())){throw 'scene1 workspot mismatch'}
 if($n.GetType().Name -ne 'worldAISpotNode' -or $n.Spot.Chunk.MasterNodeRef.ToString() -ne '0' -or $n.LookAtTarget.ToString() -ne '0'){throw 'Workspot is not independent'}
 $private='$/03_night_city/#PTFRAL3_Merc'+($i+1).ToString('00')
 $n.SourcePrefabHash=[uint64]0;$n.DebugName=Name ('PTFRAL3_Merc'+($i+1).ToString('00'))
 $d.Id=[uint64](760000000003000+$i);$d.NodeIndex=[uint16]$i;$d.QuestPrefabRefHash=Ref $private;$d.UkHash1=Ref ''
 Add-RedHandle $spotFile.RootChunk.Nodes $n;[void]$spotFile.RootChunk.NodeData.Data.Add($d);[void]$spotFile.RootChunk.NodeRefs.Add((Ref $private))
 $pds=@($original.RootChunk.Nodes|Where-Object {$_.Chunk.GetType().Name -eq 'worldCommunityRegistryNode'}|ForEach-Object {$_.Chunk.WorkspotsPersistentData}|Where-Object {$_.GlobalNodeId.Hash.ToString() -eq $oldHash})
 if($pds.Count -ne 1){throw 'Persistent workspot descriptor ambiguity'};$pd=$pds[0].DeepCopy();$pd.GlobalNodeId.Hash=(Ref $private).GetRedHash();[void]$reg.WorkspotsPersistentData.Add($pd)
 $rows.Add(@{entry=$entry;community=$community;record=$e.CharacterRecordId.ToString();source_phase='scene1';source_node=$nodeIndex;source_ref=$oldRef;source_hash=$oldHash;private_ref=$private;private_hash=(Ref $private).GetRedHash().ToString();animation=$n.Spot.Chunk.Resource.DepotPath.ToString();position=@([float]$d.Position.X.ToString(),[float]$d.Position.Y.ToString(),[float]$d.Position.Z.ToString());ready_fact=('PTFRAL3_Merc'+($i+1).ToString('00')+'Ready')})
}
Add-RedHandle $regFile.RootChunk.Nodes $reg
$regPlacement.Id=[uint64]760000000003100;$regPlacement.NodeIndex=[uint16]0;$regPlacement.QuestPrefabRefHash=Ref '$/03_night_city/#PTFRAL3_WorkspotRegistry'
[void]$regFile.RootChunk.NodeData.Data.Add($regPlacement);[void]$regFile.RootChunk.NodeRefs.Add($regPlacement.QuestPrefabRefHash)
$prefix='towercontinued\afterlife_idles_r3\'
$resources=@(($prefix+'registry.streamingsector'),($prefix+'spots.streamingsector'),($prefix+'world.streamingblock'),($prefix+'readiness.questphase'))
Write-Cr2wFile $regFile (Join-Path $source $resources[0]);Write-Cr2wFile $spotFile (Join-Path $source $resources[1])
$block=ReadWorld (Checked ($prior+'patrons_world.streamingblock'))
for($i=0;$i -lt 2;$i++){$block.RootChunk.Descriptors[$i].Data=[Activator]::CreateInstance($block.RootChunk.Descriptors[$i].GetType().GetProperty('Data').PropertyType,[object[]]@([WolvenKit.RED4.Types.ResourcePath]::op_Implicit($resources[$i])))}
$owner='$/03_night_city/c_watson/little_china/#loc_q103_afterlife/#loc_q103_afterlife_env';$variant='PTFRAL3_Idles'
$v=$block.RootChunk.Descriptors[1].Variants[0];$v.Name=Name $variant;$v.NodeRef=Ref $owner;$v.VariantId=[uint32]3917072733
Write-Cr2wFile $block (Join-Path $source $resources[2])
# Native readiness and default-off world ownership; no actor/community actions.
$f=Read-Cr2wFile (Checked ($prior+'population.questphase'));$g=$f.RootChunk.Graph.Chunk
$pause=(Get-QuestNode $g 100).DeepCopy();$toggle=(Get-QuestNode $g 12).DeepCopy();$toggle.Type.Chunk.Params.RemoveAt(1)
$toggle.Type.Chunk.Params[0].PrefabNodeRef=Ref $owner;$toggle.Type.Chunk.Params[0].VariantStates[0].Name=Name $variant
$g.Nodes.Clear();$f.EmbeddedFiles.Clear();$f.RootChunk.PhasePrefabs.Clear()
$guards=[ordered]@{};foreach($p in $r2.guards.psobject.Properties){$guards[$p.Name]=[int]$p.Value};foreach($p in $r2.policy.psobject.Properties){$guards[$p.Name]=[int]$p.Value}
$guards['PTFRAL2_Migration']=2;$guards['PTFRAL2_LocalActive']=1;$guards['PTFRAL3_Suspended']=0
function Logic([string]$op,$cs){$c=[WolvenKit.RED4.Types.questLogicalCondition]::new();$c.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::$op;foreach($x in $cs){Add-RedHandle $c.Conditions $x};return $c}
function Fact([string]$n,[int]$v,[bool]$inverse=$false){return New-FactCondition $n $v $(if($inverse){[WolvenKit.RED4.Types.Enums+EComparisonType]::NotEqual}else{[WolvenKit.RED4.Types.Enums+EComparisonType]::Equal})}
function Guard([bool]$inverse=$false){return Logic $(if($inverse){'OR'}else{'AND'}) @($script:guards.Keys|ForEach-Object {Fact $_ $script:guards[$_] $inverse})}
function State($r,[bool]$inverse=$false){$c=[WolvenKit.RED4.Types.questNodeLoadingCondition]::new();$c.ObjectRef=Ref $r.private_ref;$c.Inverted=$inverse;return Logic $(if($inverse){'OR'}else{'AND'}) @((Guard $inverse),(Fact 'PTFRAL3_WorldApplied' 1 $inverse),$c)}
function Pause([int]$id,$c){$n=$script:pause.DeepCopy();$n.Id=[uint16]$id;foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()};Set-RedHandleProperty $n Condition $c;return $n}
function Toggle([int]$id,[bool]$show){$n=$script:toggle.DeepCopy();$n.Id=[uint16]$id;foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()};$n.Type.Chunk.Params[0].VariantStates[0].Show=$show;return $n}
function Put($n){Add-RedHandle $script:g.Nodes $n}
function Link([int]$a,[string]$s,[int]$b){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $script:g $a) $s) (Get-QuestSocket (Get-QuestNode $script:g $b) 'In'))}
Put (New-InputNode 0 'In1');Put (New-SetFactNode 1 'PTFRAL3_Registered' 1);Put (New-SetFactNode 2 'PTFRAL3_WorldApplied' 0)
Link 0 Out 1;Link 1 Out 2
for($i=0;$i -lt 4;$i++){Put (New-SetFactNode (3+$i) $rows[$i].ready_fact 0);Link (2+$i) Out (3+$i)}
Put (Pause 10 (Guard));Put (New-ConditionNode 11 (Guard));Put (Toggle 12 $true);Put (New-SetFactNode 13 'PTFRAL3_WorldApplied' 1)
Put (Pause 14 (Guard $true));Put (Toggle 15 $false);Put (New-SetFactNode 16 'PTFRAL3_WorldApplied' 0)
Link 6 Out 10;Link 10 Out 11;Link 11 False 10;Link 11 True 12;foreach($i in 12..15){Link $i Out ($i+1)};Link 16 Out 10
for($i=0;$i -lt 4;$i++){$r=$rows[$i];$id=100+10*$i
 Put (Pause $id (State $r));Put (New-ConditionNode ($id+1) (State $r));Put (New-SetFactNode ($id+2) $r.ready_fact 1);Put (Pause ($id+3) (State $r $true));Put (New-SetFactNode ($id+4) $r.ready_fact 0)
 Link 6 Out $id;Link $id Out ($id+1);Link ($id+1) False $id;Link ($id+1) True ($id+2);Link ($id+2) Out ($id+3);Link ($id+3) Out ($id+4);Link ($id+4) Out $id
}
Write-Cr2wFile $f (Join-Path $source $resources[3])
foreach($p in $resources){Export-Cr2wJson (ReadWorld (Join-Path $source $p)) (Join-Path $audit ([IO.Path]::GetFileName($p)+'.json'))}
$disk=@(Get-ChildItem -LiteralPath $source -File -Recurse|ForEach-Object {[IO.Path]::GetRelativePath($source,$_.FullName)})
if(@(Compare-Object ($resources|Sort-Object) ($disk|Sort-Object)).Count){throw 'Unexpected package resource'}
$archive=Join-Path $out 'TowerContinued_AfterlifeIdlesR3.archive'
$xl=@('streaming:','  blocks:',('    - '+$resources[2]),'quest:','  phases:',('    - path: '+$resources[3]),'      parent: ep1\quest\ep1.quest','      input:','        node: [1]','        socket: Out')
[IO.File]::WriteAllLines(($archive+'.xl'),$xl,[Text.UTF8Encoding]::new($false))
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$s=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$s)){throw 'Archive build failed'}}finally{$s.Dispose()}
$packed=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -ne 'NoError'){throw 'Archive reopen failed'}
if(@(Compare-Object ($resources|Sort-Object) @($packed.Files.Values|ForEach-Object {$_.Name}|Sort-Object)).Count){throw 'Packed scope mismatch'}
foreach($p in $packed.Files.Values){$ms=[IO.MemoryStream]::new();try{$p.Extract($ms);$h=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($ms.ToArray()))}finally{$ms.Dispose()};if($h -ne (Get-FileHash (Join-Path $source $p.Name)).Hash){throw 'Packed byte readback failed'}}
foreach($p in $hashes.Keys){if((Get-FileHash (Join-Path $WorkspaceRoot $p)).Hash -ne $hashes[$p]){throw 'Source changed during build'}}
$m=[ordered]@{status='BUILT_R3_NOT_INSTALLED_NOT_LIVE';archive=$archive;sha256=(Get-FileHash $archive).Hash;xl_sha256=(Get-FileHash ($archive+'.xl')).Hash;resources=$resources;source_root=$source;guards=$guards;entries=@($rows);native_nodes=$g.Nodes.Count;variant=$variant;variant_owner=$owner;source_hashes=$hashes;packed_readback_pass=$true;spawn_actions=0;new_actor_identities=0;original_overrides=0;scene_starts=0;story_writes=0;installed=$false;live_tested=$false}
[IO.File]::WriteAllText((Join-Path $audit 'manifest.json'),($m|ConvertTo-Json -Depth 20),[Text.UTF8Encoding]::new($false))
[pscustomobject]$m|Select-Object status,native_nodes,sha256,new_actor_identities,packed_readback_pass|ConvertTo-Json
