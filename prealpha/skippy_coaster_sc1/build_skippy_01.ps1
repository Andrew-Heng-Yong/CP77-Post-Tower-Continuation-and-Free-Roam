# Build a private, ambient-only Skippy owner. This does not install it.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$out=Join-Path $PSScriptRoot 'candidate_06'
if(Test-Path -LiteralPath $out){throw 'Preserve candidate; use successor'}
[void][IO.Directory]::CreateDirectory($out)
$nativePath=Join-Path $ws 'research/activity_state_r3/native_sources/raw/base/quest/minor_quests/mq007/mq007.questphase'
$nativeHash=(Get-FileHash -LiteralPath $nativePath -Algorithm SHA256).Hash
$native=Read-Cr2wFile $nativePath
$ambient=(Get-QuestNode $native.RootChunk.Graph.Chunk 3)
if($ambient.PhaseInstancePrefabs.Count -ne 1 -or $ambient.PhaseInstancePrefabs[0].PrefabNodeRef.ToString() -cne '#mq007_pr_oneliners_screen'){throw 'Native Skippy ambient owner changed'}
$expectedRefs=@('base\quest\minor_quests\mq007\phases\mq007_gameplay_comments.questphase','base\quest\minor_quests\mq007\phases\mq007_expression_facts_reset.questphase')
$nativeJson=Join-Path $ws 'research/activity_state_r3/native_sources/json/base/quest/minor_quests/mq007/mq007.questphase.json'
$sourceText=[IO.File]::ReadAllText($nativeJson)
foreach($ref in $expectedRefs){if(!$sourceText.Contains($ref.Replace('\','\\'))){throw "Native ambient dependency missing $ref"}}
$ambient.Id=[uint16]10
foreach($s in $ambient.Sockets){$s.Chunk.Connections.Clear()}
$fullRef='$/03_night_city/#c_heywood/vista_del_rey/hvdr_03/hvdr_03_questdesign_prefabXYPFG2Y/#mq007_pr_oneliners_screen'
$ambient.PhaseInstancePrefabs[0].PrefabNodeRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($fullRef)
$template=Read-Cr2wFile (Join-Path $ws 'prealpha/world_workspots_ww1/candidate_02/source/towercontinued/world_workspots_ww1/ce_pac_cvi_116_owner.questphase')
$pauseTemplate=Get-QuestNode $template.RootChunk.Graph.Chunk 2
function Put($g,$n){Add-RedHandle $g.Nodes $n}
function Link($g,$a,$as,$b,$bs='In'){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $a) $as) (Get-QuestSocket (Get-QuestNode $g $b) $bs))}
function Pause($id,$condition){$n=$pauseTemplate.DeepCopy();$n.Id=[uint16]$id;foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()};Set-RedHandleProperty $n Condition $condition;return $n}
$facts=[ordered]@{
 PostTowerFreeRoamActive=1;PTFRP0_DR13=1;q307_active=0;q307_done=1;
 q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;
 PTFRBASE_Suspended=0;q305_johnny_scene_active=0;q115_point_of_no_return=0;
 PTFRSKIP_Ambient_Request=1;PTFRSKIP_Ambient_Claimed=0;
 PTFRSKIP_Ambient_Entered=0;PTFRSKIP_Ambient_Stop=0;
 PTFRS23_MQ007_Issued=0;PTFRS23_MQ007_RESUME_Issued=0
}
$guard=[WolvenKit.RED4.Types.questLogicalCondition]::new()
$guard.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
foreach($f in $facts.Keys){Add-RedHandle $guard.Conditions (New-FactCondition $f $facts[$f] ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))}
$nativeInventory=(Get-QuestNode $native.RootChunk.Graph.Chunk 11).Condition.Chunk
if($nativeInventory -isnot [WolvenKit.RED4.Types.questObjectCondition] -or
   $nativeInventory.Type.Chunk -isnot [WolvenKit.RED4.Types.questInventory_ConditionType] -or
   $nativeInventory.Type.Chunk.Quantity.ToString() -cne '1' -or
   $nativeInventory.Type.Chunk.ComparisonType.ToString() -cne 'GreaterOrEqual') {throw 'Native Skippy ownership condition changed'}
Add-RedHandle $guard.Conditions $nativeInventory.DeepCopy()
$g=[WolvenKit.RED4.Types.questGraphDefinition]::new()
Put $g (New-InputNode 0 'In1')
Put $g (New-SetFactNode 1 'PTFRSKIP_Ambient_Ready' 1)
Put $g (Pause 2 $guard)
Put $g (New-SetFactNode 3 'PTFRSKIP_Ambient_Claimed' 1)
Put $g (New-SetFactNode 4 'PTFRSKIP_Ambient_Request' 0)
Put $g (New-SetFactNode 5 'PTFRSKIP_Ambient_Ready' 0)
Put $g (New-SetFactNode 6 'PTFRSKIP_Ambient_Entered' 1)
Put $g $ambient
Put $g (Pause 11 (New-FactCondition 'PTFRSKIP_Ambient_Stop' 1 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal)))
$cut=[WolvenKit.RED4.Types.questCutControlNodeDefinition]::new();$cut.Id=[uint16]12
foreach($s in @(@('In','Input'),@('Out','Output'),@('CutSource','CutSource'))){[void](New-QuestSocket $cut $s[0] ([Enum]::Parse([WolvenKit.RED4.Types.Enums+questSocketType],$s[1])))}
Put $g $cut
Put $g (New-SetFactNode 13 'PTFRSKIP_Ambient_Stopped' 1)
Put $g (New-OutputNode 14 'Out')
Link $g 0 Out 1;Link $g 1 Out 2;Link $g 2 Out 3;Link $g 3 Out 4
Link $g 4 Out 5;Link $g 5 Out 6;Link $g 6 Out 10 In1
Link $g 6 Out 11;Link $g 11 Out 12;Link $g 12 CutSource 10 CutDestination
Link $g 12 Out 13;Link $g 10 TurnOff 13 In;Link $g 13 Out 14
$root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new()
$root.CookingPlatform=[WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC
Set-RedHandleProperty $root Graph $g
$file=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$file.RootChunk=$root
$relative='towercontinued\skippy_ambient_sc1\skippy_ambient_owner.questphase'
$dest=Join-Path $out ('source\'+$relative)
[void][IO.Directory]::CreateDirectory((Split-Path $dest -Parent))
Write-Cr2wFile $file $dest
$read=Read-Cr2wFile $dest
Export-Cr2wJson $read (Join-Path $out 'skippy_owner_readback_01.json')
$owner=Get-QuestNode $read.RootChunk.Graph.Chunk 10
if($read.RootChunk.Graph.Chunk.Nodes.Count -ne 12 -or $owner.PhaseInstancePrefabs.Count -ne 1 -or $owner.PhaseInstancePrefabs[0].PrefabNodeRef.ToString() -cne $fullRef){throw 'Skippy owner readback failed'}
if((Get-FileHash -LiteralPath $nativePath -Algorithm SHA256).Hash -cne $nativeHash){throw 'Native source changed'}
$proof=[ordered]@{status='SKIPPY_AMBIENT_OWNER_BUILT_NOT_PACKED';resource=$relative;sha256=(Get-FileHash -LiteralPath $dest).Hash;native_sha256=$nativeHash;native_source=$nativePath;native_node=3;prefab=$fullRef;guard=$facts;outer_edges=@(Get-GraphEdges $read.RootChunk.Graph.Chunk);game_writes=0;save_writes=0}
[IO.File]::WriteAllText((Join-Path $out 'skippy_owner_proof_01.json'),($proof|ConvertTo-Json -Depth 30)+"`n",[Text.UTF8Encoding]::new($false))
@{status=$proof.status;nodes=$read.RootChunk.Graph.Chunk.Nodes.Count;edges=$proof.outer_edges.Count}|ConvertTo-Json
