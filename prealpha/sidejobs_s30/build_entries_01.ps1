Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
. (Join-Path $ws 'tools/shark_b7_2_helpers.ps1')
$helper=Get-Content (Join-Path $ws 'tools/build_fresh_gigs_b5.ps1') -Raw
$begin=$helper.IndexOf('function ClearB5(');$end=$helper.IndexOf('$allRoots=@{};')
. ([scriptblock]::Create($helper.Substring($begin,$end-$begin)))
$p=Get-Content (Join-Path $PSScriptRoot 'prepared_01/contracts.json') -Raw|ConvertFrom-Json -Depth 100
$source=Join-Path $PSScriptRoot 'serialized_01/source'
$readback=Join-Path $PSScriptRoot 'serialized_01/entry_readback'
if(Test-Path $readback){throw 'Use successor build'}
New-Item -ItemType Directory $readback|Out-Null
function SaveGraph($g,$dep){
 $r=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();Set-RedHandleProperty $r Graph $g
 $f=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$f.RootChunk=$r
 $raw=Join-Path $source $dep;New-Item -ItemType Directory (Split-Path $raw -Parent) -Force|Out-Null
 Write-Cr2wFile $f $raw
 $rb=Join-Path $readback ($dep+'.json');New-Item -ItemType Directory (Split-Path $rb -Parent) -Force|Out-Null
 Export-Cr2wJson (Read-Cr2wFile $raw) $rb
}
function CopyNode($g,$og,[int]$id){
 $o=Get-QuestNode $og $id;$n=$o.DeepCopy();ClearB5 $n
 if($n -is [WolvenKit.RED4.Types.questPhaseNodeDefinition] -and $null -ne $n.PhaseGraph -and $null -ne $n.PhaseGraph.Chunk){RewireB5 $n.PhaseGraph.Chunk $o.PhaseGraph.Chunk}
 AddNodeB5 $g $n
}
function JournalCondition($row){
 $path=[WolvenKit.RED4.Types.gameJournalPath]::new();$path.RealPath=$row.path;$path.ClassName=$row.class;$path.FileEntryIndex=2
 $t=[WolvenKit.RED4.Types.questJournalEntryState_ConditionType]::new();Set-RedHandleProperty $t Path $path
 $t.State=[WolvenKit.RED4.Types.Enums+gameJournalEntryState]([int]$row.states[0]);$t.Inverted=$false
 $c=[WolvenKit.RED4.Types.questJournalCondition]::new();Set-RedHandleProperty $c Type $t;return $c
}
$common=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;PTFRPA2_Finished=1;PTFRPA2_Fault=0;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;q307_active=0;q307_debug_reset=0;q115_point_of_no_return=0;q305_johnny_scene_active=0;PTFRU9_Support_Issued=1;PTFRU9_Support_Fault=0}
$parentRaw=Join-Path $ws 'research/sidejobs_s29/native_03/basegame_4_gamedata/raw/base/quest/minor_quests/minorquests.questphase'
$parent=(Read-Cr2wFile $parentRaw).RootChunk.Graph.Chunk
$parentIDs=@(20,54,55,59,62,70,73,80,81,83,84,86)
$parentEdges=@(
 ,@(54,'Out',86,'In1'),,@(55,'Out',70,'In1'),,@(59,'Out1',20,'In1'),,@(62,'Out1',59,'In1'),
 ,@(70,'Out1',73,'In1'),,@(73,'Out1',62,'In1'),,@(80,'Out',55,'In'),,@(81,'Out1',83,'In1'),
 ,@(83,'Out1',84,'In1'),,@(84,'Out1',54,'In'),,@(86,'Out1',80,'In')
)
$built=@()
foreach($job in $p.jobs){
 $g=[WolvenKit.RED4.Types.questGraphDefinition]::new();$tag=$job.tag;$child=64000;$edges=@()
 if($job.id -ceq 'mq006_rollercoaster'){
  $child=20
  foreach($id in $parentIDs){CopyNode $g $parent $id}
  $node=Get-QuestNode $g 20
  $node.PhaseResource=[WolvenKit.RED4.Types.CResourceAsyncReference`1[WolvenKit.RED4.Types.questQuestPhaseResource]]::new($job.private_native)
  $edges=@();foreach($e in $parentEdges){$edges+=,@($e[0])}
 }else{
  $node=[WolvenKit.RED4.Types.questPhaseNodeDefinition]::new();$node.Id=[uint16]$child
  $node.PhaseResource=[WolvenKit.RED4.Types.CResourceAsyncReference`1[WolvenKit.RED4.Types.questQuestPhaseResource]]::new($job.private_native)
  [void](New-QuestSocket $node $job.input 'Input');[void](New-QuestSocket $node $job.output 'Output');AddNodeB5 $g $node
 }
 $pairs=[ordered]@{};foreach($k in $common.Keys){$pairs[$k]=$common[$k]}
 foreach($f in $job.facts_equal.PSObject.Properties){$pairs[$f.Name]=[int]$f.Value}
 foreach($n in @('Issued','Entered','Finished','Fault')){$pairs[$tag+'_'+$n]=0}
 $pairs[$tag+'_Permit']=1
 $c=AllB5 $pairs;Add-RedHandle $c.Conditions (JournalCondition $job.journals[0])
 foreach($f in $job.fact_ranges.PSObject.Properties){Add-RedHandle $c.Conditions (New-FactCondition $f.Name ([int]$f.Value.min) 'GreaterOrEqual');Add-RedHandle $c.Conditions (New-FactCondition $f.Name ([int]$f.Value.max) 'LessOrEqual')}
 foreach($n in @((New-InputNode 65000 'In1'),(New-SetFactNode 65001 ($tag+'_Ready') 1),(New-SetFactNode 65002 ($tag+'_Revision') 1),(PauseB5 65003 $c),(New-ConditionNode 65004 $c.DeepCopy()),(New-SetFactNode 65005 ($tag+'_Issued') 1),(New-SetFactNode 65006 ($tag+'_Entered') 1),(New-SetFactNode 65007 ($tag+'_Finished') 1))){AddNodeB5 $g $n}
 $edges+=,@(65000,'Out',65001,'In');$edges+=,@(65001,'Out',65002,'In');$edges+=,@(65002,'Out',65003,'In');$edges+=,@(65003,'Out',65004,'In');$edges+=,@(65004,'False',65003,'In');$edges+=,@(65004,'True',65005,'In')
 if($job.id -ceq 'mq006_rollercoaster'){
  AddNodeB5 $g (New-SetFactNode 65008 'PTFRWORLD_Coaster_QuestOwns' 1)
  AddNodeB5 $g (New-SetFactNode 65009 'PTFRWORLD_Coaster_QuestOwns' 0)
  $edges+=,@(65005,'Out',65008,'In');$edges+=,@(65008,'Out',65006,'In');$edges+=,@(65006,'Out',81,'In1')
  $edges+=,@(20,'Out1',65009,'In');$edges+=,@(65009,'Out',65007,'In')
 }else{
  $edges+=,@(65005,'Out',65006,'In');$edges+=,@(65006,'Out',$child,$job.input);$edges+=,@($child,$job.output,65007,'In')
 }
 foreach($edge in $edges){if(@($edge).Count -ne 4){throw ('Malformed edge '+$job.id+' '+($edge|ConvertTo-Json -Compress -Depth 8))}}
 RebuildB5 $g $edges
 $dep='towercontinued\sidejobs_s30\entries\'+$job.id+'.questphase';SaveGraph $g $dep
 $built+=,@{id=$job.id;depot=$dep;edges=$edges;guard=$pairs;child=$child}
}
$m=@{status='BUILT_NOT_INSTALLED';entries=$built;parent_raw_sha256=(Get-FileHash $parentRaw).Hash;contracts_sha256=(Get-FileHash (Join-Path $PSScriptRoot 'prepared_01/contracts.json')).Hash}
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'serialized_01/entries_manifest.json'),($m|ConvertTo-Json -Depth 100),[Text.UTF8Encoding]::new($false))
@{entries=$built.Count;output=$source}|ConvertTo-Json
