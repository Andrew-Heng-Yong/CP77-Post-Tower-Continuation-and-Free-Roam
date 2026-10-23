param([string]$Revision='encounters_04')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$WorkspaceRoot=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $WorkspaceRoot 'tools/build_phase2a.ps1') -HelpersOnly
$helper=Get-Content -LiteralPath (Join-Path $WorkspaceRoot 'tools/build_fresh_gigs_b5.ps1') -Raw
$begin=$helper.IndexOf('function ClearB5(');$end=$helper.IndexOf('$allRoots=@{};')
if($begin -lt 0 -or $end -le $begin){throw 'Helper boundary changed'}
. ([scriptblock]::Create($helper.Substring($begin,$end-$begin)))
if($Revision -cnotmatch '^encounters_\d{2}$'){throw 'Invalid revision'}
$out=Join-Path $PSScriptRoot ('build/'+$Revision);if(Test-Path -LiteralPath $out){throw 'Use successor directory'}
$source=Join-Path $out 'source';$readback=Join-Path $out 'readback';New-Item -ItemType Directory -Force $source,$readback|Out-Null
$contractRel='research/sidejobs_s28/encounters/contracts_02.json';$planRel='research/sidejobs_s28/encounters/build_plan_02.json'
$contract=Get-Content (Join-Path $WorkspaceRoot $contractRel) -Raw|ConvertFrom-Json;$plan=Get-Content (Join-Path $WorkspaceRoot $planRel) -Raw|ConvertFrom-Json
$pins=[ordered]@{};$resources=[ordered]@{};$boots=[Collections.Generic.List[string]]::new();$recipes=[Collections.Generic.List[object]]::new();$clones=[Collections.Generic.List[object]]::new()
function Pin([string]$p){$pins[$p]=(Get-FileHash -LiteralPath (Join-Path $WorkspaceRoot $p)).Hash}
foreach($p in $contract.source_pins.PSObject.Properties){Pin $p.Name;if($pins[$p.Name] -cne $p.Value){throw ('Changed source '+$p.Name)}}
foreach($p in @($contractRel,$planRel,'prealpha/sidejobs_s28/encounters/build_04.ps1','prealpha/sidejobs_s28/encounters/test_04.py','tools/build_phase2a.ps1','tools/build_fresh_gigs_b5.ps1')){Pin $p}
function GraphAt($g,[string]$path){if($path -ne 'root'){foreach($id in $path.Substring(5).Split('/')){$g=(Get-QuestNode $g ([int]$id)).PhaseGraph.Chunk}};return $g}
function ReadRoot([string]$raw){return (Read-Cr2wFile (Join-Path $WorkspaceRoot $raw)).RootChunk}
function CopyNode($g,$og,[int]$id,[int]$newid=-1){$o=Get-QuestNode $og $id;$n=$o.DeepCopy();ClearB5 $n;if($n -is [WolvenKit.RED4.Types.questPhaseNodeDefinition] -and $null -ne $n.PhaseGraph -and $null -ne $n.PhaseGraph.Chunk){RewireB5 $n.PhaseGraph.Chunk $o.PhaseGraph.Chunk};if($newid -ge 0){$n.Id=[uint16]$newid};AddNodeB5 $g $n}
function Own([string]$id,[string]$key){return 'PTFRS28_'+$id+'_'+$key}
function Ref($n,[string]$dep){$n.PhaseResource=[WolvenKit.RED4.Types.CResourceAsyncReference`1[WolvenKit.RED4.Types.questQuestPhaseResource]]::new($dep)}
function SaveRoot($root,[string]$name,[bool]$boot=$false){$file=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$file.RootChunk=$root;$depot='towercontinued\sidejobs_s28\encounters\'+$name+'.questphase';$raw=Join-Path $source $depot;Write-Cr2wFile $file $raw;Export-Cr2wJson (Read-Cr2wFile $raw) (Join-Path $readback ($name+'.json'));$resources[$depot]=(Get-FileHash $raw).Hash;if($boot){$boots.Add($depot)};return $depot}
function JournalCondition($spec){$p=[WolvenKit.RED4.Types.gameJournalPath]::new();$p.RealPath=$spec.path;$p.ClassName=$spec.class;$p.FileEntryIndex=2;$t=[WolvenKit.RED4.Types.questJournalEntryState_ConditionType]::new();Set-RedHandleProperty $t Path $p;$t.State=[WolvenKit.RED4.Types.Enums+gameJournalEntryState]([int]$spec.states[0]);$t.Inverted=$false;$c=[WolvenKit.RED4.Types.questJournalCondition]::new();Set-RedHandleProperty $c Type $t;return $c}
function InventoryCondition($spec){$g=GraphAt (ReadRoot $spec.raw).Graph.Chunk $spec.graph;$c=(Get-QuestNode $g ([int]$spec.node)).Condition.Chunk.DeepCopy();if($c.Type.Chunk.GetType().Name -cne 'questInventory_ConditionType' -or !$c.Type.Chunk.IsPlayer){throw 'Wrong inventory witness'};$c.Type.Chunk.ComparisonType=[WolvenKit.RED4.Types.Enums+EComparisonType]::Equal;$c.Type.Chunk.Quantity=[uint32]0;return $c}
$common=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;PTFRPA2_Finished=1;PTFRPA2_Fault=0;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;q307_active=0;q307_debug_reset=0;q115_point_of_no_return=0;q305_johnny_scene_active=0}
$mainMapping=@{}
$python='C:/Users/Ayong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
& $python (Join-Path $PSScriptRoot 'presentation_03.py') (Join-Path $out 'presentation_expected')
if($LASTEXITCODE -ne 0){throw 'Presentation preparation failed'}
$presentation=Get-Content (Join-Path $out 'presentation_expected/prepared.json') -Raw|ConvertFrom-Json -Depth 100
foreach($p in $presentation.source_pins.PSObject.Properties){Pin $p.Name}
$options=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new()
foreach($input in $presentation.inputs){
 $json=Get-Content (Join-Path $WorkspaceRoot $input.expected) -Raw
 $dto=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Deserialize([WolvenKit.Common.Conversion.RedFileDto],$json,$options)
 $raw=Join-Path $source $input.depot;Write-Cr2wFile $dto.Data $raw
 Export-Cr2wJson (Read-Cr2wFile $raw) (Join-Path $readback (($input.depot.Split('\')[-1])+'.json'))
 $resources[$input.depot]=(Get-FileHash $raw).Hash
}
$podRaw='research/omitted_jobs_audit/native_01/raw/base/quest/minor_quests/mq003/phases/mq003_orbital_pod.questphase'
$podOriginal=ReadRoot $podRaw;$pod=$podOriginal.DeepCopy();RewireB5 $pod.Graph.Chunk $podOriginal.Graph.Chunk
$podNodes=@($pod.Graph.Chunk.Nodes | ForEach-Object {$_.Chunk} | Where-Object {$_ -is [WolvenKit.RED4.Types.questSceneNodeDefinition] -and $_.SceneFile.DepotPath.ToString() -ceq 'base\quest\minor_quests\mq003\scenes\mq003_03_orbital_pod.scene'})
if($podNodes.Count -ne 1){throw 'Pod scene owner changed'}
$podNodes[0].SceneFile=[WolvenKit.RED4.Types.CResourceAsyncReference`1[WolvenKit.RED4.Types.scnSceneResource]]::new('towercontinued\sidejobs_s28\encounters\mq003_pod.scene')
$podDepot=SaveRoot $pod 'mq003_pod_phase';$clones.Add(@{kind='scene_reference';raw=$podRaw;depot=$podDepot;readback='mq003_pod_phase.json';source_graph='root';source_node=[int]$podNodes[0].Id;target='towercontinued\sidejobs_s28\encounters\mq003_pod.scene'})
$spaceRaw='research/sidejobs_s28/encounters/official_check_01/basegame_4_gamedata/raw/base/quest/minor_quests/mq003/mq003_orbitals.questphase'
$spaceOriginal=ReadRoot $spaceRaw;$space=$spaceOriginal.DeepCopy();RewireB5 $space.Graph.Chunk $spaceOriginal.Graph.Chunk
$spaceNodes=@($space.Graph.Chunk.Nodes | ForEach-Object {$_.Chunk} | Where-Object {$_ -is [WolvenKit.RED4.Types.questPhaseNodeDefinition] -and $_.PhaseResource.DepotPath.ToString() -ceq 'base\quest\minor_quests\mq003\phases\mq003_orbital_pod.questphase'})
if($spaceNodes.Count -ne 1){throw 'Pod phase owner changed'}
Ref $spaceNodes[0] $podDepot
$spaceDepot=SaveRoot $space 'mq003_main';$mainMapping['base\quest\minor_quests\mq003\mq003_orbitals.questphase']=$spaceDepot;$clones.Add(@{kind='reference';raw=$spaceRaw;depot=$spaceDepot;readback='mq003_main.json';source_graph='root';source_node=[int]$spaceNodes[0].Id;target=$podDepot})

# Ezekiel's quest actor Owner is supplied by the separate native diner loop.
# Signal only after the existing native service-disable write, then reuse the
# untouched original native initialization path. No native reset is added.
$dinerRaw='research/omitted_jobs_audit/native_01/raw/base/quest/minor_quests/mq022/phases/mq022_beginning.questphase'
$dinerOriginal=ReadRoot $dinerRaw;$diner=$dinerOriginal.DeepCopy();RewireB5 $diner.Graph.Chunk $dinerOriginal.Graph.Chunk;$dg=$diner.Graph.Chunk
AddNodeB5 $dg (New-SetFactNode 65000 (Own 'mq022_ezekiel' 'DinerStartReady') 1)
$edges=@(EdgesB5 $dg|ForEach-Object {$_});if(@($edges|Where-Object {$_[0] -eq 58 -and $_[2] -eq 71}).Count -ne 1){throw 'Native disable edge changed'}
$edges=@($edges|Where-Object {!($_[0] -eq 58 -and $_[2] -eq 71)})+@(@(58,'Out',65000,'In'),@(65000,'Out',71,'In'));RebuildB5 $dg $edges
$dinerDepot=SaveRoot $diner 'mq022_beginning';$clones.Add(@{kind='diner_signal';raw=$dinerRaw;depot=$dinerDepot;readback='mq022_beginning.json';source_graph='root';source_edge=@(58,'Out',71,'In');signal_node=65000;signal=(Own 'mq022_ezekiel' 'DinerStartReady')})
$mainRaw='research/omitted_jobs_audit/native_01/raw/base/quest/minor_quests/mq022/mq022.questphase';$mainOriginal=ReadRoot $mainRaw;$main=$mainOriginal.DeepCopy();RewireB5 $main.Graph.Chunk $mainOriginal.Graph.Chunk;Ref (Get-QuestNode $main.Graph.Chunk 84) $dinerDepot
$mainDepot=SaveRoot $main 'mq022_main';$mainMapping['base\quest\minor_quests\mq022\mq022.questphase']=$mainDepot;$clones.Add(@{kind='reference';raw=$mainRaw;depot=$mainDepot;readback='mq022_main.json';source_graph='root';source_node=84;target=$dinerDepot})
$defaultRaw='research/sidejobs_s28/encounters/official_check_01/basegame_4_gamedata/raw/base/quest/default_dialogs.questphase';$defaultJson=$defaultRaw.Replace('/raw/','/json/')+'.json';Pin $defaultRaw;Pin $defaultJson
$sharedScene='research/b0_vendor_rollout/special_scene_sources/raw/base/open_world/vendors/watson/northside/wat_nid_foodshop_02/wat_nid_foodshop_02.scene';Pin $sharedScene;Pin ($sharedScene.Replace('/raw/','/json/')+'.json')
$defaultRoot=ReadRoot $defaultRaw;$defaultParent=GraphAt $defaultRoot.Graph.Chunk 'root/7/30'
if($defaultRoot.PhasePrefabs.Count -ne 1 -or $defaultRoot.PhasePrefabs[0].PrefabNodeRef.ToString() -cne '#loading_conditions'){throw 'Default root prefab changed'}
foreach($job in $plan.jobs){
 $id=$job.id;$owner=@($contract.owners|Where-Object {$_.id -ceq $id})[0];$og=(ReadRoot $job.parent_raw).Graph.Chunk;$g=[WolvenKit.RED4.Types.questGraphDefinition]::new()
 foreach($i in $job.parent_ids){CopyNode $g $og ([int]$i)}
 $native=$job.native_depot;if($mainMapping.ContainsKey($native)){$native=$mainMapping[$native];Ref (Get-QuestNode $g $job.parent_child) $native}
 $guard=[ordered]@{};foreach($k in $common.Keys){$guard[$k]=$common[$k]};foreach($p in $owner.facts_equal.PSObject.Properties){$guard[$p.Name]=[int]$p.Value}
 foreach($suffix in @('Issued','Finished','Fault')){$guard[(Own $id $suffix)]=0};$guard[(Own $id 'Permit')]=1
 $condition=AllB5 $guard;foreach($j in $owner.journals){Add-RedHandle $condition.Conditions (JournalCondition $j)};foreach($i in $owner.inventory_native){Add-RedHandle $condition.Conditions (InventoryCondition $i)}
 foreach($f in $owner.fact_ranges.PSObject.Properties){Add-RedHandle $condition.Conditions (New-FactCondition $f.Name ([int]$f.Value.min) 'GreaterOrEqual');Add-RedHandle $condition.Conditions (New-FactCondition $f.Name ([int]$f.Value.max) 'LessOrEqual')}
 foreach($n in @((New-InputNode 65000 'In1'),(New-SetFactNode 65001 (Own $id 'Ready') 1),(New-SetFactNode 65002 (Own $id 'Revision') 1),(PauseB5 65003 $condition),(New-ConditionNode 65004 $condition.DeepCopy()),(New-SetFactNode 65005 (Own $id 'Issued') 1),(New-SetFactNode 65006 (Own $id 'Entered') 1),(New-SetFactNode 65007 (Own $id 'Finished') 1))){AddNodeB5 $g $n}
 $edges=@();foreach($e0 in $job.parent_edges){$e=@($e0);if($e[0] -eq 0){$e[0]=65005};if($e[2] -eq $job.parent_child){$e[2]=65006;$e[3]='In'};$edges+=,$e}
 $edges+=,@(65000,'Out',65001,'In');$edges+=,@(65001,'Out',65002,'In');$edges+=,@(65002,'Out',65003,'In');$edges+=,@(65003,'Out',65004,'In');$edges+=,@(65004,'False',65003,'In');$edges+=,@(65004,'True',65005,'In');$edges+=,@(65006,'Out',$job.parent_child,'In1');$edges+=,@($job.parent_child,'Out1',65007,'In')
 $service=$null
 if($id -ceq 'mq022_ezekiel'){
  CopyNode $g $defaultParent 4 64000
  $scopedDiner=Get-QuestNode $g 64000;if($scopedDiner.PhaseInstancePrefabs.Count -ne 0){throw 'Unexpected own diner prefabs'};foreach($prefab in $defaultRoot.PhasePrefabs){$scopedDiner.PhaseInstancePrefabs.Add($prefab.DeepCopy())}
  $serviceGuard=[ordered]@{(Own $id 'Issued')=1;(Own $id 'DinerStartReady')=1;(Own $id 'DinerIssued')=0;(Own $id 'Fault')=0;std_arr_foodshop_04_default_on=0}
  AddNodeB5 $g (PauseB5 65020 (AllB5 $serviceGuard));AddNodeB5 $g (New-SetFactNode 65021 (Own $id 'DinerIssued') 1)
  $edges+=,@(65005,'Out',65020,'In');$edges+=,@(65020,'Out',65021,'In');$edges+=,@(65021,'Out',64000,'In1')
  $service=@{source_raw=$defaultRaw;source_graph='root/7/30';source_node=4;target_node=64000;guard=$serviceGuard;spawn_before_native_default_dialogue=$true;independent_boot=$false;inherited_prefabs_source='RootChunk.phasePrefabs';inherited_prefabs_target='node64000.phaseInstancePrefabs';inherited_prefabs=@('#loading_conditions')}
 }
 RebuildB5 $g $edges;$root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();Set-RedHandleProperty $root Graph $g;$depot=SaveRoot $root ($id+'_entry') $true
 $recipes.Add(@{id=$id;depot=$depot;native=$native;parent_raw=$job.parent_raw;parent_ids=$job.parent_ids;parent_child=$job.parent_child;guard=$guard;edges=$edges;service=$service})
}
foreach($p in $pins.Keys){if((Get-FileHash (Join-Path $WorkspaceRoot $p)).Hash -cne $pins[$p]){throw 'Pin changed'}}
$component=[ordered]@{status='BUILT_S28_ENCOUNTERS_ENGINE_PENDING';resources=$resources;boots=$boots.ToArray();source_pins=$pins;contract=$contractRel;source_assessment=$contract.source_assessment;presentation=$presentation;historical_comparison_sources=@('research/coyote_sidejobs_audit/native_01/raw/base/quest/default_dialogs.questphase','research/omitted_jobs_audit/native_01/raw/base/quest/minor_quests/mq003/mq003_orbitals.questphase','research/sidejobs_s28/encounters/native_02/raw/base/quest/main_quests/part1/q101/phases/q101_p2_meet_takemura.questphase');recipes=$recipes.ToArray();clones=$clones.ToArray();mod_overrides=@();official_overrides=0;builder_sha256=(Get-FileHash $PSCommandPath).Hash;limitations=@('Unsupported existing progress defers without reset.','Native scene, reward, world and reload outcomes require live verification.')}
[IO.File]::WriteAllText((Join-Path $out 'component.json'),($component|ConvertTo-Json -Depth 100),[Text.UTF8Encoding]::new($false));Write-Output ('BUILT '+$out)
