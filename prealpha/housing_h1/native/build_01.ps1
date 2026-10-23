param([string]$Revision='native_01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$WorkspaceRoot=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $WorkspaceRoot 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $WorkspaceRoot 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$helper=Get-Content (Join-Path $WorkspaceRoot 'tools/build_fresh_gigs_b5.ps1') -Raw
$begin=$helper.IndexOf('function ClearB5(');$end=$helper.IndexOf('$pauseTemplate=');if($begin -lt 0 -or $end -le $begin){throw 'Helper boundaries changed'}
. ([scriptblock]::Create($helper.Substring($begin,$end-$begin)))
if($Revision -cnotmatch '^native_\d{2}$'){throw 'Invalid revision'}
$out=Join-Path $PSScriptRoot ('build/'+$Revision);if(Test-Path $out){throw 'Use successor build directory'}
$source=Join-Path $out 'source';$readback=Join-Path $out 'readback';New-Item -ItemType Directory -Force $source,$readback|Out-Null
$catalogRel='research/housing_h1/native/catalog_01.json';$preparedRel='research/housing_h1/native/prepared_02/prepared.json';$officialRel='research/housing_h1/native/official_01/inventory.json';$donorRel='research/housing_h1/native/h10_donor_01/inventory.json'
$catalog=Get-Content (Join-Path $WorkspaceRoot $catalogRel) -Raw|ConvertFrom-Json -Depth 100
$prepared=Get-Content (Join-Path $WorkspaceRoot $preparedRel) -Raw|ConvertFrom-Json -Depth 100
$official=Get-Content (Join-Path $WorkspaceRoot $officialRel) -Raw|ConvertFrom-Json -Depth 100
$donor=Get-Content (Join-Path $WorkspaceRoot $donorRel) -Raw|ConvertFrom-Json -Depth 100
$pins=[ordered]@{};$resources=[ordered]@{};$boots=[Collections.Generic.List[string]]::new();$recipes=[Collections.Generic.List[object]]::new();$prefix='towercontinued\housing_h1\native\'
function Pin([string]$p){$pins[$p]=(Get-FileHash (Join-Path $WorkspaceRoot $p)).Hash}
foreach($p in @($catalogRel,$preparedRel,$officialRel,$donorRel,'research/housing_h1/native/purchase_placements_01.json','research/housing_h1/native/access_sources_01.json','prealpha/housing_h1/native/build_01.ps1','prealpha/housing_h1/native/prepare_scenes_02.py','tools/build_phase2a.ps1','tools/build_fresh_gigs_b5.ps1')){Pin $p}
foreach($doc in @($catalog,$prepared)){foreach($p in $doc.source_pins.PSObject.Properties){Pin $p.Name;if($pins[$p.Name] -cne $p.Value){throw 'Changed input'}}}
foreach($s in $official.rows){Pin $s.raw;Pin $s.json};foreach($s in $donor.rows){Pin $s.raw;Pin $s.json}
function GraphAt($g,[string]$path){if($path -ne 'root'){foreach($n in $path.Substring(5).Split('/')){$g=(Get-QuestNode $g ([int]$n)).PhaseGraph.Chunk}};return $g}
function ReadRoot([string]$raw){return (Read-Cr2wFile (Join-Path $WorkspaceRoot $raw)).RootChunk}
function Own([string]$id,[string]$suffix){return 'PTFRH1_'+$id+'_'+$suffix}
function Pause($id,$condition){$n=[WolvenKit.RED4.Types.questPauseConditionNodeDefinition]::new();$n.Id=[uint16]$id;Set-RedHandleProperty $n Condition $condition;[void](New-QuestSocket $n 'CutDestination' 'CutDestination');[void](New-QuestSocket $n 'In' 'Input');[void](New-QuestSocket $n 'Out' 'Output');return $n}
function CopyNode($g,$og,[int]$id,[int]$target){$n=(Get-QuestNode $og $id).DeepCopy();ClearB5 $n;$n.Id=[uint16]$target;AddNodeB5 $g $n;return $n}
function Phase($id,$g,$prefabs){$n=[WolvenKit.RED4.Types.questPhaseNodeDefinition]::new();$n.Id=[uint16]$id;Set-RedHandleProperty $n PhaseGraph $g;foreach($p in $prefabs){$n.PhaseInstancePrefabs.Add($p.DeepCopy())};[void](New-QuestSocket $n 'CutDestination' 'CutDestination');[void](New-QuestSocket $n 'In1' 'Input');return $n}
function SaveRoot($root,[string]$name,[bool]$boot=$false,[string]$override=''){$f=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$f.RootChunk=$root;$dep=if($override){$override}else{$prefix+$name+'.questphase'};$raw=Join-Path $source $dep;Write-Cr2wFile $f $raw;Export-Cr2wJson (Read-Cr2wFile $raw) (Join-Path $readback ($name+'.json'));$resources[$dep]=(Get-FileHash $raw).Hash;if($boot){$boots.Add($dep)};return $dep}
function Root($g){$r=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();Set-RedHandleProperty $r Graph $g;return $r}
function Inventory($item,[string]$comparison,[uint32]$quantity){$t=[WolvenKit.RED4.Types.questInventory_ConditionType]::new();$t.IsPlayer=$true;$t.ItemID=$item;$t.Quantity=$quantity;$t.ComparisonType=[WolvenKit.RED4.Types.Enums+EComparisonType]$comparison;$c=[WolvenKit.RED4.Types.questObjectCondition]::new();Set-RedHandleProperty $c Type $t;return $c}
function Common {$pairs=[ordered]@{PTFRH1_Ready=1;PTFRH1_Revision=1;PTFRH1_Fault=0;PostTowerFreeRoamActive=1;PTFRP0_DR13=1;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;q307_active=0};return AllB5 $pairs}
$options=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new()
foreach($i in $prepared.inputs){Pin $i.expected;$dto=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Deserialize([WolvenKit.Common.Conversion.RedFileDto],(Get-Content (Join-Path $WorkspaceRoot $i.expected) -Raw),$options);$raw=Join-Path $source $i.depot;Write-Cr2wFile $dto.Data $raw;Export-Cr2wJson (Read-Cr2wFile $raw) (Join-Path $readback (($i.depot.Split('\')[-1])+'.json'));$resources[$i.depot]=(Get-FileHash $raw).Hash}
# Existing H10 owner identity, edges and completion cleanup are retained.
$h10Original=ReadRoot $donor.rows[0].raw;$h10=$h10Original.DeepCopy();RewireB5 $h10.Graph.Chunk $h10Original.Graph.Chunk
$wait=Get-QuestNode $h10.Graph.Chunk 2;$guard=[WolvenKit.RED4.Types.questLogicalCondition]::new();$guard.Operation='AND';Add-RedHandle $guard.Conditions $wait.Condition.Chunk.DeepCopy()
$availability=[WolvenKit.RED4.Types.questLogicalCondition]::new();$availability.Operation='OR';Add-RedHandle $availability.Conditions (New-FactCondition 'PTFRH1_Ready' 0 'Equal');Add-RedHandle $availability.Conditions (New-FactCondition 'PTFRH1_h10_Entitled' 1 'Equal');Add-RedHandle $guard.Conditions $availability;Set-RedHandleProperty $wait Condition $guard
$null=SaveRoot $h10 'h10_owner' $false $donor.rows[0].depot
$keyNodes=@{northside=85;japantown=28;glen=21;corpo=20};$travelNodes=@{northside=19;japantown=47;glen=43;corpo=44};$purchaseWait=@{northside=10;japantown=3;glen=3;corpo=10}
foreach($row in $catalog.properties){
 $id=$row.id;$r=ReadRoot $row.source.raw;$og=$r.Graph.Chunk;$markerGraph=GraphAt $og $row.marker_source.graph
 $g=[WolvenKit.RED4.Types.questGraphDefinition]::new();AddNodeB5 $g (New-InputNode 0 'In1');$edges=@()
 $loss=Common;Add-RedHandle $loss.Conditions (AllB5 ([ordered]@{(Own $id 'Entitled')=0;(Own $id 'LossPermit')=1;(Own $id 'LossApplied')=0;(Own $id 'ServiceActive')=0}))
 if($id -ceq 'h10'){foreach($f in @('PTFRB0H10P_Active','PTFRB0H10M_Active','PTFRB0H10I_M_Active','PTFRB0H10I_H_Active','PTFRB0H10I_B_Active','PTFRB0H10I_S_Active','PTFRB0H10I_W_Active')){Add-RedHandle $loss.Conditions (New-FactCondition $f 0 'Equal')}}
 AddNodeB5 $g (Pause 10 $loss);$null=CopyNode $g $markerGraph $row.marker_source.node 11;AddNodeB5 $g (New-SetFactNode 12 (Own $id 'LossApplied') 1)
 $edges+=,@(0,'Out',10,'In');$edges+=,@(10,'Out',11,'Inactive');$edges+=,@(11,'Out',12,'In')
 $access=Common;Add-RedHandle $access.Conditions (AllB5 ([ordered]@{(Own $id 'Entitled')=1;(Own $id 'AccessPermit')=1;(Own $id 'LossApplied')=1;(Own $id 'AccessApplied')=0}))
 AddNodeB5 $g (Pause 20 $access);$null=CopyNode $g $markerGraph $row.marker_source.node 26;AddNodeB5 $g (New-SetFactNode 27 (Own $id 'AccessApplied') 1);$edges+=,@(0,'Out',20,'In');$edges+=,@(26,'Out',27,'In')
 $keySpec=$null
 if($id -ceq 'h10'){$edges+=,@(20,'Out',26,'Active')}else{
  Add-RedHandle $access.Conditions (New-FactCondition 'q101_done' 0 'Greater')
  $key=CopyNode $g $markerGraph $keyNodes[$id] 22;$item=$key.Type.Chunk.Params[0].ItemID
  AddNodeB5 $g (New-ConditionNode 21 (Inventory $item 'Equal' 0));AddNodeB5 $g (Pause 23 (Inventory $item 'GreaterOrEqual' 1));$null=CopyNode $g $markerGraph $travelNodes[$id] 25
  foreach($e in @(@(20,'Out',21,'In'),@(21,'True',22,'In'),@(21,'False',23,'In'),@(22,'Out',23,'In'),@(23,'Out',25,'In'),@(25,'Out',26,'Active'))){$edges+=,$e}
  $keySpec=@{graph=$row.marker_source.graph;node=$keyNodes[$id];item_hash=$item.ToString();quantity=1;guard='player quantity == 0';ack_guard='player quantity >= 1';travel_node=$travelNodes[$id]}
  # One persistent scoped branch; purchase and service scenes have disjoint entitlement gates.
  $sg=[WolvenKit.RED4.Types.questGraphDefinition]::new();AddNodeB5 $sg (New-InputNode 0 'In1');$se=@();$nativeService=GraphAt $og $row.service_graph
  $service=Common;Add-RedHandle $service.Conditions (AllB5 ([ordered]@{(Own $id 'Entitled')=1;(Own $id 'AccessApplied')=1}));Add-RedHandle $service.Conditions (Get-QuestNode $nativeService $row.service_wait_node).Condition.Chunk.DeepCopy()
  AddNodeB5 $sg (Pause 10 $service);AddNodeB5 $sg (New-SetFactNode 11 (Own $id 'ServiceActive') 1);$sn=CopyNode $sg $nativeService $row.service_scene_node 12;$sn.SceneFile=[WolvenKit.RED4.Types.CResourceAsyncReference`1[WolvenKit.RED4.Types.scnSceneResource]]::new($prefix+$id+'_services.scene');AddNodeB5 $sg (New-SetFactNode 13 (Own $id 'ServiceActive') 0)
  foreach($e in @(@(0,'Out',10,'In'),@(10,'Out',11,'In'),@(11,'Out',12,'in'),@(12,'out',13,'In'),@(12,'Default INT',13,'In'),@(13,'Out',10,'In'))){$se+=,$e}
  # Preserve the exact initial native local-area OR purchased-history predicate.
  $pe=@(EdgesB5 $nativeService|ForEach-Object {$_});$first=@($pe|Where-Object {$_[0] -eq 0})[0][2];$initial=(Get-QuestNode $nativeService $first).Condition.Chunk.DeepCopy()
  $buy=Common;Add-RedHandle $buy.Conditions (AllB5 ([ordered]@{(Own $id 'Entitled')=0;(Own $id 'PurchaseReady')=1;(Own $id 'PurchaseRequest')=0}));Add-RedHandle $buy.Conditions $initial;Add-RedHandle $buy.Conditions (New-FactCondition 'q101_done' 0 'Greater')
  AddNodeB5 $sg (Pause 20 $buy);AddNodeB5 $sg (New-SetFactNode 21 (Own $id 'PurchaseSceneActive') 1);$pn=CopyNode $sg $nativeService $row.service_scene_node 22;$pn.SceneFile=[WolvenKit.RED4.Types.CResourceAsyncReference`1[WolvenKit.RED4.Types.scnSceneResource]]::new($prefix+$id+'_purchase.scene')
  # Purchase scenes expose their original entry label, and the private normal out.
  $pn.Sockets.Clear();[void](New-QuestSocket $pn 'CutDestination' 'CutDestination');[void](New-QuestSocket $pn 'in_purchase' 'Input');[void](New-QuestSocket $pn 'out' 'Output');[void](New-QuestSocket $pn 'Default INT' 'Output')
  AddNodeB5 $sg (New-SetFactNode 23 (Own $id 'PurchaseSceneActive') 0)
  foreach($e in @(@(0,'Out',20,'In'),@(20,'Out',21,'In'),@(21,'Out',22,'in_purchase'),@(22,'out',23,'In'),@(22,'Default INT',23,'In'),@(23,'Out',20,'In'))){$se+=,$e};RebuildB5 $sg $se
  $scope=Common;Add-RedHandle $scope.Conditions (AllB5 ([ordered]@{(Own $id 'LossApplied')=1;(Own $id 'ScopeIssued')=0}));Add-RedHandle $scope.Conditions (New-FactCondition 'q101_done' 0 'Greater')
  AddNodeB5 $g (Pause 30 $scope);AddNodeB5 $g (New-SetFactNode 31 (Own $id 'ScopeIssued') 1);AddNodeB5 $g (Phase 32 $sg $r.PhasePrefabs)
  foreach($e in @(@(0,'Out',30,'In'),@(30,'Out',31,'In'),@(31,'Out',32,'In1'))){$edges+=,$e}
 }
 RebuildB5 $g $edges;$depot=SaveRoot (Root $g) ($id+'_owner') $true
 $recipes.Add(@{id=$id;depot=$depot;source=$row.source;marker=$row.marker_source;key=$keySpec;loss_nodes=@(10,11,12);access_nodes=@(20,21,22,23,25,26,27);scoped_node=$(if($id -eq 'h10'){$null}else{32});source_prefabs='RootChunk.phasePrefabs'})
}
# Retain only the already-earned Kerry visitor service route. No Kerry actor,
# dating/sleep entry, ownership fact, purchase, marker reset or NPC spawn.
$ks=@($official.rows|Where-Object {$_.depot -ceq 'dlc\dlc6_apart\phases\dlc6_apart_kerry_villa.questphase'})[0];$kr=ReadRoot $ks.raw;$kg=$kr.Graph.Chunk
$parent=@($official.rows|Where-Object {$_.depot -ceq 'dlc\dlc6_apart\phases\dlc6_apart.questphase'})[0];$pr=ReadRoot $parent.raw;$earned=(Get-QuestNode (GraphAt $pr.Graph.Chunk 'root/11') 3).Condition.Chunk.DeepCopy()
$g=[WolvenKit.RED4.Types.questGraphDefinition]::new();$sg=[WolvenKit.RED4.Types.questGraphDefinition]::new();AddNodeB5 $g (New-InputNode 0 'In1');AddNodeB5 $sg (New-InputNode 0 'In1')
$gate=Common;Add-RedHandle $gate.Conditions $earned;Add-RedHandle $gate.Conditions (New-FactCondition 'q101_done' 0 'Greater');Add-RedHandle $gate.Conditions (New-FactCondition 'PTFRH1_kerry_ScopeIssued' 0 'Equal')
AddNodeB5 $g (Pause 1 $gate);AddNodeB5 $g (New-SetFactNode 2 'PTFRH1_kerry_ScopeIssued' 1)
$service=Common;Add-RedHandle $service.Conditions $earned.DeepCopy();Add-RedHandle $service.Conditions (Get-QuestNode $kg 3).Condition.Chunk.DeepCopy();AddNodeB5 $sg (Pause 3 $service)
AddNodeB5 $sg (New-SetFactNode 5 'PTFRH1_kerry_ServiceActive' 1);$n=CopyNode $sg $kg 4 4;$n.SceneFile=[WolvenKit.RED4.Types.CResourceAsyncReference`1[WolvenKit.RED4.Types.scnSceneResource]]::new($prefix+'kerry_services.scene');AddNodeB5 $sg (New-SetFactNode 6 'PTFRH1_kerry_ServiceActive' 0)
RebuildB5 $sg @(@(0,'Out',3,'In'),@(3,'Out',5,'In'),@(5,'Out',4,'in'),@(4,'out',6,'In'),@(4,'Default INT',6,'In'),@(6,'Out',3,'In'));AddNodeB5 $g (Phase 3 $sg $kr.PhasePrefabs);RebuildB5 $g @(@(0,'Out',1,'In'),@(1,'Out',2,'In'),@(2,'Out',3,'In1'))
$null=SaveRoot (Root $g) 'kerry_visitor_owner' $true
$override=[ordered]@{};$override[$donor.rows[0].depot]=$donor.rows[0].raw_sha256
$component=[ordered]@{status='BUILT_HOUSING_H1_NATIVE_ENGINE_PENDING';resources=$resources;boots=$boots.ToArray();source_pins=$pins;override_donors=$override;current_official_sources=$official.rows;archive_pins=$official.archives;donor=$donor;recipes=$recipes.ToArray();presentation=$prepared;purchase_placements='research/housing_h1/native/purchase_placements_01.json';builder_sha256=(Get-FileHash $PSCommandPath).Hash;game_writes=0;limits=@('Same saved H10 owner graph reload and all native scene/device interactions require live verification.','No loss-time key removal, native purchased fact reset, shared stash modification or excluded character acquisition.','Fast travel registration is original purchase access, never revoked during loss.')}
[IO.File]::WriteAllText((Join-Path $out 'component.json'),($component|ConvertTo-Json -Depth 100),[Text.UTF8Encoding]::new($false));Write-Output ('BUILT '+$out)
