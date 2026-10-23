param([string]$Revision='vehicles_01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly
$helper=Get-Content -LiteralPath (Join-Path $ws 'tools/build_fresh_gigs_b5.ps1') -Raw
$begin=$helper.IndexOf('function ClearB5(');$end=$helper.IndexOf('$allRoots=@{};')
if($begin -lt 0 -or $end -le $begin){throw 'Helper definitions changed'}
. ([scriptblock]::Create($helper.Substring($begin,$end-$begin)))
if($Revision -cnotmatch '^vehicles_\d{2}$'){throw 'Invalid revision'}
$out=Join-Path $PSScriptRoot ('build/'+$Revision)
if(Test-Path -LiteralPath $out){throw 'Use immutable successor'}
New-Item -ItemType Directory $out,(Join-Path $out 'source'),(Join-Path $out 'readback')|Out-Null
$contractRel='prealpha/sidejobs_s28/vehicles/contracts_01.json';$planRel='research/sidejobs_s28/vehicles/plan_01.json'
$spec=Get-Content (Join-Path $ws $contractRel) -Raw|ConvertFrom-Json
$plan=Get-Content (Join-Path $ws $planRel) -Raw|ConvertFrom-Json
$pins=[ordered]@{};$resources=[ordered]@{};$recipes=[Collections.Generic.List[object]]::new()
function Pin($p){$pins[$p]=(Get-FileHash -LiteralPath (Join-Path $ws $p)).Hash}
function ReadRoot($raw){Pin $raw;Pin ($raw.Replace('/raw/','/json/')+'.json');return (Read-Cr2wFile (Join-Path $ws $raw)).RootChunk}
function GraphAt($g,$path){if($path -cne 'root'){foreach($id in $path.Substring(5).Split('/')){$g=(Get-QuestNode $g ([int]$id)).PhaseGraph.Chunk}};return $g}
foreach($p in $spec.source_pins.PSObject.Properties){Pin $p.Name;if($pins[$p.Name] -cne $p.Value){throw ('Source changed '+$p.Name)}}
foreach($p in @($contractRel,$planRel,'prealpha/sidejobs_s28/vehicles/build_01.ps1','prealpha/sidejobs_s28/vehicles/test_01.py','tools/build_phase2a.ps1','tools/build_fresh_gigs_b5.ps1','tools/shark_b7_2_helpers.ps1','tools/gig_family_b7_1_xl.ps1','tools/afterlife_faces_r5_deployment.ps1')){Pin $p}
$vehicleDonor='research/gig_restoration/stock_shark_u2/sources/raw/base/quest/persistent_content.questphase'
$vehicleGraph=GraphAt (ReadRoot $vehicleDonor).Graph.Chunk 'root/151/5/20'
$available=(Get-QuestNode $vehicleGraph 19).Condition.Chunk
if($available.Type.Chunk.GetType().Name -cne 'questVehicleAvailable_ConditionType'){throw 'Native vehicle witness changed'}
$carRaw='research/omitted_jobs_audit/native_01/raw/base/quest/minor_quests/mq050/mq050.questphase'
$car=(ReadRoot $carRaw).Graph.Chunk
function NotCondition($c){$n=[WolvenKit.RED4.Types.questLogicalCondition]::new();$n.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::NOR;Add-RedHandle $n.Conditions $c;return $n}
function JournalCondition($j){
 if(@($j.states).Count -ne 1 -or $j.states[0] -ne 1){throw 'Only fresh journals'}
 $p=[WolvenKit.RED4.Types.gameJournalPath]::new();$p.RealPath=$j.path;$p.ClassName=$j.class;$p.FileEntryIndex=2
 $t=[WolvenKit.RED4.Types.questJournalEntryState_ConditionType]::new();Set-RedHandleProperty $t Path $p;$t.State=[WolvenKit.RED4.Types.Enums+gameJournalEntryState]::Inactive;$t.Inverted=$false
 $c=[WolvenKit.RED4.Types.questJournalCondition]::new();Set-RedHandleProperty $c Type $t;return $c
}
foreach($o in $spec.owners){
 $job=@($plan.jobs|Where-Object {$_.id -ceq $o.id})[0]
 $parent=GraphAt (ReadRoot $job.parent.raw).Graph.Chunk $job.parent.graph
 $original=Get-QuestNode $parent ([int]$job.parent.node)
 $phase=$original.DeepCopy();ClearB5 $phase;$phase.Id=[uint16]100
 if($null -ne $phase.PhaseGraph -and $null -ne $phase.PhaseGraph.Chunk){throw 'Expected standalone main reference'}
 $pairs=[ordered]@{}
 foreach($part in @($spec.common_equal,$o.facts_equal)){foreach($p in $part.PSObject.Properties){$pairs[$p.Name]=[int]$p.Value}}
 foreach($suffix in @('Issued','Entered','Finished','Fault')){$pairs[$o.tag+'_'+$suffix]=0}
 foreach($suffix in @('Ready','Revision','Permit')){$pairs[$o.tag+'_'+$suffix]=1}
 $guard=AllB5 $pairs
 foreach($f in $o.fact_ranges.PSObject.Properties){Add-RedHandle $guard.Conditions (New-FactCondition $f.Name ([int]$f.Value.min) 'GreaterOrEqual');Add-RedHandle $guard.Conditions (New-FactCondition $f.Name ([int]$f.Value.max) 'LessOrEqual')}
 foreach($j in $o.journals){Add-RedHandle $guard.Conditions (JournalCondition $j)}
 $nativeAvailability=$available.DeepCopy();$nativeAvailability.Type.Chunk.VehicleName=$o.vehicle_zero[0].record
 Add-RedHandle $guard.Conditions (NotCondition $nativeAvailability)
 $inventory=$null;$spawned=$null
 if($o.id -ceq 'mq050_ken_block_tribute'){
  $inventory=(Get-QuestNode $car 80).Condition.Chunk.DeepCopy()
  if($inventory.Type.Chunk.GetType().Name -cne 'questInventory_ConditionType' -or !$inventory.Type.Chunk.IsPlayer){throw 'Wrong key inventory witness'}
  $inventory.Type.Chunk.ComparisonType=[WolvenKit.RED4.Types.Enums+EComparisonType]::Equal;$inventory.Type.Chunk.Quantity=[uint32]0
  Add-RedHandle $guard.Conditions $inventory
  $spawned=(Get-QuestNode $car 42).Condition.Chunk.DeepCopy()
  if($spawned.Type.Chunk.GetType().Name -cne 'questVehicleSpawned_ConditionType'){throw 'Wrong pre-discovery car witness'}
  Add-RedHandle $guard.Conditions (NotCondition $spawned)
 }
 $g=[WolvenKit.RED4.Types.questGraphDefinition]::new()
 foreach($n in @((New-InputNode 0 'In1'),(New-SetFactNode 1 ($o.tag+'_Ready') 1),(New-SetFactNode 2 ($o.tag+'_Revision') 1),(PauseB5 3 $guard),(New-ConditionNode 4 $guard.DeepCopy()),(New-SetFactNode 5 ($o.tag+'_Issued') 1),(New-SetFactNode 6 ($o.tag+'_Entered') 1),$phase,(New-SetFactNode 101 ($o.tag+'_Finished') 1))){AddNodeB5 $g $n}
 $edges=@(@(0,'Out',1,'In'),@(1,'Out',2,'In'),@(2,'Out',3,'In'),@(3,'Out',4,'In'),@(4,'False',3,'In'),@(4,'True',5,'In'),@(6,'Out',100,'In1'),@(100,'Out1',101,'In'))
 $prereq=$null
 if($null -ne $job.parent.prerequisite_node){
  $prereq=(Get-QuestNode $parent ([int]$job.parent.prerequisite_node)).DeepCopy();ClearB5 $prereq;$prereq.Id=[uint16]90;AddNodeB5 $g $prereq
  $edges+=,@(5,'Out',90,'In');$edges+=,@(90,'Out',6,'In')
 }else{$edges+=,@(5,'Out',6,'In')}
 RebuildB5 $g $edges
 $root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();Set-RedHandleProperty $root Graph $g
 $file=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$file.RootChunk=$root
 $raw=Join-Path (Join-Path $out 'source') $o.depot;$json=Join-Path $out ('readback/'+$o.id+'.json')
 Write-Cr2wFile $file $raw;Export-Cr2wJson (Read-Cr2wFile $raw) $json
 $resources[$o.depot]=(Get-FileHash -LiteralPath $raw).Hash
 $recipes.Add(@{id=$o.id;depot=$o.depot;parent=$job.parent;native=$job.main;target=100;prerequisite_target=90;guard=$pairs;edges=$edges;availability_source=@{raw=$vehicleDonor;graph='root/151/5/20';node=19};inventory_source=if($null -ne $inventory){@{raw=$carRaw;graph='root';node=80}}else{$null};spawned_source=if($null -ne $spawned){@{raw=$carRaw;graph='root';node=42}}else{$null};readback='readback/'+$o.id+'.json';readback_sha256=(Get-FileHash -LiteralPath $json).Hash})
}
foreach($p in $pins.Keys){if((Get-FileHash -LiteralPath (Join-Path $ws $p)).Hash -cne $pins[$p]){throw ('Source drift '+$p)}}
$result=[ordered]@{
 status='SOURCE_CANDIDATE_BLOCKED_NOT_DISPATCHABLE';component='vehicles';resources=$resources;boots=@();proposed_boots=@($spec.owners|ForEach-Object {$_.depot});source_pins=$pins;contract=$contractRel;contract_sha256=(Get-FileHash -LiteralPath (Join-Path $ws $contractRel)).Hash;recipes=$recipes.ToArray();native_resources=$spec.native_resources;official_overrides=@();mod_overrides=@();builder_sha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash
 blockers=@('Native VehicleAvailable is only an additional availability check, not proven atomic durable entitlement. Runtime IsVehiclePlayerUnlocked is authoritative but sampled.','Three Johnny world workspots still need initialActions/independent-prop audit.','Official game archives/cache changed during source work. Current native byte equivalence and full compile must be established with compatible tooling.','MQ050 pre-journal named-car contradiction is guarded; pre-journal native controller/world-key ownership is not a proven resume slice.')
 limitations=@('Boots intentionally empty; candidate cannot be dispatched by aggregate loader.','Unsupported progress remains deferred. No reset, item grant, vehicle unlock, debug input, or reward rewrite is added.','Standalone native mains retain original resource prefab context and all connected child gameplay.')
}
[IO.File]::WriteAllText((Join-Path $out 'component.json'),($result|ConvertTo-Json -Depth 100),[Text.UTF8Encoding]::new($false))
Write-Output ('BUILT NON-DISPATCHABLE '+$out)
