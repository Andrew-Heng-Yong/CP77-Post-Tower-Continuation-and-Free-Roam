Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$nativePath=Join-Path $PSScriptRoot '../native_review/outside_phases_native_01/basegame_4_gamedata.archive/pac_wwd_phase.questphase'
$native=Read-Cr2wFile $nativePath
$ng=(Get-QuestNode $native.RootChunk.Graph.Chunk 3).PhaseGraph.Chunk
$sourceEdges=@(Get-GraphEdges $ng)
$community='$/03_night_city/c_pacifica/#west_wind_estate_001/west_wind_estate_openworld_prefabZERJ55I/west_wind_estate_openworld_community_prefabVYVTSYI/#pac_wwd_ripper_com'
$trigger='$/03_night_city/c_pacifica/#west_wind_estate_001/wwd_service_points_prefabUGGY6KA/pac_wwd_ripdoc_01_prefabISH67RQ/pac_wwd_ripdoc_01_openworld_prefabANGY5VQ/#pac_wwd_ripdoc_01_tr_rec'
$prefix='PTFRWA3GREETING_WWD_'
$facts=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;q307_active=0;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;PTFRBASE_Suspended=0;q305_johnny_scene_active=0;q115_point_of_no_return=0;q000_done=1}
$donor=Read-Cr2wFile (Join-Path $ws 'diagnostics/world_npc_idle_20261026_01/combat_owners/base_open_world_combat_events_pacifica_coastview_ce_pac_cvi_phase.questphase')
$cg=(Get-QuestNode (Get-QuestNode (Get-QuestNode $donor.RootChunk.Graph.Chunk 28).PhaseGraph.Chunk 14).PhaseGraph.Chunk 61).PhaseGraph.Chunk
$pause=Get-QuestNode $cg 30
function Fact($name,$value){return New-FactCondition $name $value ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal)}
function Pause($id,$condition){$n=$pause.DeepCopy();$n.Id=[uint16]$id;foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()};Set-RedHandleProperty $n Condition $condition;return $n}
function Guard([bool]$claim){
 $guard=[WolvenKit.RED4.Types.questLogicalCondition]::new();$guard.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
 foreach($k in $facts.Keys){Add-RedHandle $guard.Conditions (Fact $k $facts[$k])}
 if($claim){Add-RedHandle $guard.Conditions (Fact ($prefix+'Claimed') 0)}
 $ready=$pause.Condition.Chunk.DeepCopy();$ready.Type.Chunk.SpawnerReference=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($community)
 $ready.Type.Chunk.CommunityEntryNames.Clear();$ready.Type.Chunk.CommunityEntryNames.Add([WolvenKit.RED4.Types.CName]::op_Implicit('ripdoc_rec'))
 Add-RedHandle $guard.Conditions $ready
 return $guard
}
$g=[WolvenKit.RED4.Types.questGraphDefinition]::new()
Add-RedHandle $g.Nodes (New-InputNode 0 'In1')
Add-RedHandle $g.Nodes (Pause 100 (Guard $true))
Add-RedHandle $g.Nodes (New-SetFactNode 101 ($prefix+'Claimed') 1)
Add-RedHandle $g.Nodes (New-SetFactNode 102 ($prefix+'Entered') 1)
foreach($id in @(3,4,7,8,9)){
 $n=Get-QuestNode $ng $id
 foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()}
 Add-RedHandle $g.Nodes $n
}
$node3=Get-QuestNode $g 3
$nativeTrigger=$node3.Condition.Chunk
$nativeTrigger.TriggerAreaRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($trigger)
$loopGuard=Guard $false
Add-RedHandle $loopGuard.Conditions $nativeTrigger
Set-RedHandleProperty $node3 Condition $loopGuard
(Get-QuestNode $g 4).Type.Chunk.Params[0].PuppetRef.Reference=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($community)
(Get-QuestNode $g 9).Condition.Chunk.Type.Chunk.ObjectRef.Reference=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($community)
function Link($a,$socket,$b){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $a) $socket) (Get-QuestSocket (Get-QuestNode $g $b) 'In'))}
Link 0 'Out' 100;Link 100 'Out' 101;Link 101 'Out' 102;Link 102 'Out' 3
Link 3 'Out' 9;Link 9 'True' 4;Link 4 'Out' 8;Link 8 'Out' 7;Link 7 'Out' 3
$root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();$root.CookingPlatform=[WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC
Set-RedHandleProperty $root Graph $g
$file=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$file.RootChunk=$root
$depot='towercontinued/world_support_wa3/greeting_wwd.questphase'
$dest=Join-Path $PSScriptRoot ('../candidate_01/source/'+$depot)
if(Test-Path $dest){throw 'Preserve existing owner'}
Write-Cr2wFile $file $dest
$back=Read-Cr2wFile $dest
Export-Cr2wJson $back (Join-Path $PSScriptRoot 'readback_01.json')
$edges=@(Get-GraphEdges $back.RootChunk.Graph.Chunk)
if($edges.Count -ne 9 -or $back.RootChunk.Graph.Chunk.Nodes.Count -ne 9){throw 'Roundtrip shape'}
$proof=@{status='WA3_NATIVE_GREETING_BUILT';resource=$depot;path=$dest;sha256=(Get-FileHash $dest).Hash;native=$nativePath;native_sha256=(Get-FileHash $nativePath).Hash;native_edges=$sourceEdges;edges=$edges;facts=$facts;community=$community;community_hash=[WolvenKit.RED4.Types.NodeRef]::CalculateHash($community).ToString();entry='ripdoc_rec';trigger=$trigger;trigger_hash=[WolvenKit.RED4.Types.NodeRef]::CalculateHash($trigger).ToString();game_writes=0;save_writes=0}
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'build_proof_01.json'),($proof|ConvertTo-Json -Depth 20)+"`n",[Text.UTF8Encoding]::new($false))
@{status=$proof.status;sha256=$proof.sha256}|ConvertTo-Json
