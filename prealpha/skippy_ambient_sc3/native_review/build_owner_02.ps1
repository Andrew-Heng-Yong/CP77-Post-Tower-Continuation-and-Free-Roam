# SC3 ambient lifecycle. Workspace-only; parent packages and deploys separately.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$out=Join-Path $PSScriptRoot 'candidate_02'
if(Test-Path -LiteralPath $out){throw 'Preserve candidate; use successor'}
[void][IO.Directory]::CreateDirectory($out)
$nativePath=Join-Path $ws 'research/activity_state_r3/native_sources/raw/base/quest/minor_quests/mq007/mq007.questphase'
$oldPath=Join-Path $ws 'prealpha/skippy_coaster_sc1/candidate_07/archive_source/towercontinued/skippy_ambient_sc1/skippy_ambient_owner.questphase'
$nativeHash=(Get-FileHash -LiteralPath $nativePath).Hash
$oldHash=(Get-FileHash -LiteralPath $oldPath).Hash
$native=Read-Cr2wFile $nativePath
$old=Read-Cr2wFile $oldPath
$ng=$native.RootChunk.Graph.Chunk
$ambient=Get-QuestNode $ng 3 # Retain native shared socket identities; DeepCopy breaks connections.
$equip=(Get-QuestNode $ng 12).DeepCopy()
foreach($n in @($ambient,$equip)){foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()}}
$fullRef='$/03_night_city/#c_heywood/vista_del_rey/hvdr_03/hvdr_03_questdesign_prefabXYPFG2Y/#mq007_pr_oneliners_screen'
if($ambient.PhaseInstancePrefabs.Count -ne 1 -or $ambient.PhaseInstancePrefabs[0].PrefabNodeRef.ToString() -cne '#mq007_pr_oneliners_screen'){throw 'Wrong native ambient prefab'}
$ambient.PhaseInstancePrefabs[0].PrefabNodeRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($fullRef)
if($equip.Condition.Chunk.Type.Chunk -isnot [WolvenKit.RED4.Types.questCharacterEquippedItem_ConditionType] -or
 $equip.Condition.Chunk.Type.Chunk.Inverted.ToString() -notin @('False','0') -or
 $equip.Condition.Chunk.Type.Chunk.IsPlayer.ToString() -notin @('True','1')){throw 'Wrong native equipped condition'}
function Put($g,$n){Add-RedHandle $g.Nodes $n}
function Link($g,$a,$as,$b,$bs='In'){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $a) $as) (Get-QuestSocket (Get-QuestNode $g $b) $bs))}
function Fact($name,$value){return (New-FactCondition $name $value ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))}
function Logic($operation){$c=[WolvenKit.RED4.Types.questLogicalCondition]::new();$c.Operation=[Enum]::Parse([WolvenKit.RED4.Types.Enums+questLogicalOperation],$operation);return $c}
function Pause($id,$condition){$n=(Get-QuestNode $old.RootChunk.Graph.Chunk 11).DeepCopy();$n.Id=[uint16]$id;foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()};Set-RedHandleProperty $n Condition $condition;return $n}

# Native re-equip loop stays inside one cuttable parent. A takeover cuts both
# pending equip admission and the active native ambient child, without rearming.
$loop=[WolvenKit.RED4.Types.questGraphDefinition]::new()
Put $loop (New-InputNode 0 'In1')
Put $loop $equip
Put $loop (New-SetFactNode 13 'PTFRSKIP_SC3_Active' 1)
Put $loop $ambient
Put $loop (New-SetFactNode 14 'PTFRSKIP_SC3_Active' 0)
Link $loop 0 Out 12
Link $loop 12 Out 13
Link $loop 13 Out 3 In1
Link $loop 3 TurnOff 14
Link $loop 14 Out 12
$lifecycle=[WolvenKit.RED4.Types.questPhaseNodeDefinition]::new();$lifecycle.Id=[uint16]10
[void](New-QuestSocket $lifecycle 'In1' ([WolvenKit.RED4.Types.Enums+questSocketType]::Input))
[void](New-QuestSocket $lifecycle 'CutDestination' ([WolvenKit.RED4.Types.Enums+questSocketType]::CutDestination))
Set-RedHandleProperty $lifecycle PhaseGraph $loop

$guard=Logic 'AND'
$facts=[ordered]@{
 PostTowerFreeRoamActive=1;PTFRP0_DR13=1;q307_active=0;q307_done=1;
 q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;
 PTFRBASE_Suspended=0;q305_johnny_scene_active=0;q115_point_of_no_return=0;
 PTFRSKIP_SC3_Request=1;PTFRSKIP_SC3_Claimed=0;PTFRSKIP_SC3_Entered=0;
 PTFRSKIP_SC3_Stop=0;PTFRSKIP_SC3_Stopped=0;
 PTFRS23_MQ007_Issued=0;PTFRS23_MQ007_RESUME_Issued=0
}
foreach($f in $facts.Keys){Add-RedHandle $guard.Conditions (Fact $f $facts[$f])}
$oldRetired=Logic 'OR'
Add-RedHandle $oldRetired.Conditions (Fact 'PTFRSKIP_Ambient_Stopped' 1)
$neverEntered=Logic 'AND'
foreach($p in @(@('PTFRSKIP_Ambient_Claimed',0),@('PTFRSKIP_Ambient_Entered',0),@('PTFRSKIP_Ambient_Request',0),@('PTFRSKIP_Ambient_Stop',1))){Add-RedHandle $neverEntered.Conditions (Fact $p[0] $p[1])}
Add-RedHandle $oldRetired.Conditions $neverEntered
Add-RedHandle $guard.Conditions $oldRetired

$g=[WolvenKit.RED4.Types.questGraphDefinition]::new()
Put $g (New-InputNode 0 'In1')
Put $g (New-SetFactNode 1 'PTFRSKIP_SC3_Ready' 1)
Put $g (Pause 2 $guard)
Put $g (New-SetFactNode 3 'PTFRSKIP_SC3_Claimed' 1)
Put $g (New-SetFactNode 4 'PTFRSKIP_SC3_Request' 0)
Put $g (New-SetFactNode 5 'PTFRSKIP_SC3_Ready' 0)
Put $g (New-SetFactNode 6 'PTFRSKIP_SC3_Entered' 1)
Put $g $lifecycle
Put $g (Pause 11 (Fact 'PTFRSKIP_SC3_Stop' 1))
$cut=[WolvenKit.RED4.Types.questCutControlNodeDefinition]::new();$cut.Id=[uint16]12
foreach($s in @(@('In','Input'),@('Out','Output'),@('CutSource','CutSource'))){[void](New-QuestSocket $cut $s[0] ([Enum]::Parse([WolvenKit.RED4.Types.Enums+questSocketType],$s[1])))}
Put $g $cut
Put $g (New-SetFactNode 15 'PTFRSKIP_SC3_Active' 0)
Put $g (New-SetFactNode 13 'PTFRSKIP_SC3_Stopped' 1)
Put $g (New-OutputNode 14 'Out')
Link $g 0 Out 1;Link $g 1 Out 2;Link $g 2 Out 3;Link $g 3 Out 4
Link $g 4 Out 5;Link $g 5 Out 6;Link $g 6 Out 10 In1;Link $g 6 Out 11
Link $g 11 Out 12;Link $g 12 CutSource 10 CutDestination
Link $g 12 Out 15;Link $g 15 Out 13;Link $g 13 Out 14
$root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new()
$root.CookingPlatform=[WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC
Set-RedHandleProperty $root Graph $g
$file=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$file.RootChunk=$root
$relative='towercontinued\skippy_ambient_sc3\skippy_ambient_owner.questphase'
$dest=Join-Path $out ('source\'+$relative)
[void][IO.Directory]::CreateDirectory((Split-Path $dest -Parent))
Write-Cr2wFile $file $dest
$read=Read-Cr2wFile $dest
Export-Cr2wJson $read (Join-Path $out 'owner_readback_01.json')
Export-Cr2wJson $file (Join-Path $out 'owner_prewrite_01.json')
if((Get-FileHash -LiteralPath $nativePath).Hash -cne $nativeHash -or (Get-FileHash -LiteralPath $oldPath).Hash -cne $oldHash){throw 'Source input changed'}
$proof=[ordered]@{status='SC3_OWNER_SERIALIZED';resource=$relative;sha256=(Get-FileHash -LiteralPath $dest).Hash;native_sha256=$nativeHash;old_sha256=$oldHash;root_guards=$facts;root_edges=@(Get-GraphEdges $read.RootChunk.Graph.Chunk);loop_edges=@(Get-GraphEdges (Get-QuestNode $read.RootChunk.Graph.Chunk 10).PhaseGraph.Chunk);game_writes=0;save_writes=0}
[IO.File]::WriteAllText((Join-Path $out 'owner_proof_01.json'),($proof|ConvertTo-Json -Depth 30)+"`n",[Text.UTF8Encoding]::new($false))
$proof|ConvertTo-Json -Depth 30
