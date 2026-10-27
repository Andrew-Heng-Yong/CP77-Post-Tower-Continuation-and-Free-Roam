# Workspace-only native prefab ownership prototype. No pack/install/game writes.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ws = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$out = Join-Path $PSScriptRoot 'candidate_02'
if (Test-Path -LiteralPath $out) { throw 'Use a successor; do not overwrite evidence.' }
New-Item -ItemType Directory -Path $out | Out-Null
$nativePath = Join-Path $ws 'diagnostics/world_npc_idle_20261026_01/combat_owners/base_open_world_combat_events_pacifica_coastview_ce_pac_cvi_phase.questphase'
$nativeHash = (Get-FileHash -LiteralPath $nativePath).Hash
$native = Read-Cr2wFile $nativePath
$nativeOwner = Get-QuestNode (Get-QuestNode $native.RootChunk.Graph.Chunk 28).PhaseGraph.Chunk 18
if ($nativeOwner.PhaseInstancePrefabs.Count -ne 1 -or $nativeOwner.PhaseInstancePrefabs[0].PrefabNodeRef.ToString() -cne '#ce_pac_cvi_116') { throw 'Native prefab scope changed' }
$prefix = 'PTFRWW1_CVI116_'
$fullRef = '$/03_night_city/c_pacifica/coastview/cvi_ce_prefabMZQN2IY/#ce_pac_cvi_116'
$template = Read-Cr2wFile (Join-Path $ws 'prealpha/coaster_jean_jc1/candidate_01/archive_source/towercontinued/sidejobs_s30/entries/mq006_rollercoaster.questphase')
$pauseTemplate = Get-QuestNode $template.RootChunk.Graph.Chunk 65003
function Put($g,$n) { Add-RedHandle $g.Nodes $n }
function Link($g,$a,$b,$inputName='In') { [void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $a) 'Out') (Get-QuestSocket (Get-QuestNode $g $b) $inputName)) }
function Pause($id,$condition) {
  $node=$pauseTemplate.DeepCopy(); $node.Id=[uint16]$id
  foreach($socket in $node.Sockets){$socket.Chunk.Connections.Clear()}
  Set-RedHandleProperty $node Condition $condition
  return $node
}
$facts=[ordered]@{
  PostTowerFreeRoamActive=1; PTFRP0_DR13=1; q307_active=0; q307_done=1;
  q307_finished=1; q307_2079=1; q307_main_game_killed=1; q307_ep1_killed=1;
  PTFRBASE_Suspended=0; q305_johnny_scene_active=0; q115_point_of_no_return=0;
  q000_done=1; PTFRWW1_CVI116_Request=1; PTFRWW1_CVI116_Claimed=0;
  PTFRWW1_CVI116_Entered=0; PTFRWW1_CVI116_Hold=0
}
$guard=[WolvenKit.RED4.Types.questLogicalCondition]::new()
$guard.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
foreach($f in $facts.Keys){Add-RedHandle $guard.Conditions (New-FactCondition $f $facts[$f] ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))}
$inner=[WolvenKit.RED4.Types.questGraphDefinition]::new()
Put $inner (New-InputNode 0 'In1')
Put $inner (New-SetFactNode 1 ($prefix+'Entered') 1)
Put $inner (Pause 2 (New-FactCondition ($prefix+'Hold') 1 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal)))
Link $inner 0 1; Link $inner 1 2
# Preserve native prefab membership, but never retain the native spawn/reset loop.
$owner=[WolvenKit.RED4.Types.questPhaseNodeDefinition]::new(); $owner.Id=[uint16]6
$prefab=$nativeOwner.PhaseInstancePrefabs[0].DeepCopy()
$prefab.PrefabNodeRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($fullRef)
$owner.PhaseInstancePrefabs.Add($prefab)
Set-RedHandleProperty $owner PhaseGraph $inner
[void](New-QuestSocket $owner 'CutDestination' ([WolvenKit.RED4.Types.Enums+questSocketType]::CutDestination))
[void](New-QuestSocket $owner 'In1' ([WolvenKit.RED4.Types.Enums+questSocketType]::Input))
$outer=[WolvenKit.RED4.Types.questGraphDefinition]::new()
Put $outer (New-InputNode 0 'In1')
Put $outer (New-SetFactNode 1 ($prefix+'Ready') 1)
Put $outer (Pause 2 $guard)
Put $outer (New-SetFactNode 3 ($prefix+'Claimed') 1)
Put $outer (New-SetFactNode 4 ($prefix+'Request') 0)
Put $outer (New-SetFactNode 5 ($prefix+'Ready') 0)
Put $outer $owner
Link $outer 0 1; Link $outer 1 2; Link $outer 2 3; Link $outer 3 4; Link $outer 4 5; Link $outer 5 6 'In1'
$root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new()
$root.CookingPlatform=[WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC
Set-RedHandleProperty $root Graph $outer
$file=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$file.RootChunk=$root
$relative='towercontinued\world_workspots_ww1\ce_pac_cvi_116_owner.questphase'
$destination=Join-Path $out ('source\'+$relative)
New-Item -ItemType Directory -Force -Path (Split-Path $destination -Parent) | Out-Null
Write-Cr2wFile $file $destination
$read=Read-Cr2wFile $destination
Export-Cr2wJson $read (Join-Path $out 'owner_readback_01.json')
$readOwner=Get-QuestNode $read.RootChunk.Graph.Chunk 6
if ($read.RootChunk.PhasePrefabs.Count -ne 0 -or $read.RootChunk.Graph.Chunk.Nodes.Count -ne 7 -or $readOwner.PhaseInstancePrefabs.Count -ne 1 -or $readOwner.PhaseGraph.Chunk.Nodes.Count -ne 3) {throw 'Readback structure mismatch'}
if ($readOwner.PhaseInstancePrefabs[0].PrefabNodeRef.ToString() -cne $fullRef) {throw 'Readback prefab mismatch'}
if ((Get-FileHash -LiteralPath $nativePath).Hash -cne $nativeHash) {throw 'Native source changed'}
$proof=[ordered]@{
  status='WORKSPACE_ONLY_EXACT_GROUP_OWNER_PROTOTYPE_NOT_INSTALLED';resource=$relative;
  sha256=(Get-FileHash -LiteralPath $destination).Hash;
  original_prefab=$fullRef;native_source=$nativePath;native_sha256=$nativeHash;
  original_owner='root/28/18';native_guard=$facts;
  outer_edges=@(Get-GraphEdges $read.RootChunk.Graph.Chunk);
  inner_edges=@(Get-GraphEdges $readOwner.PhaseGraph.Chunk);
  game_writes=0;save_writes=0;installed_paths_added=0;
  limitations=@('Not registered in ArchiveXL or packed','No runtime driver installed','Rendering and AI recovery unproven','Broader groups are not admitted')
}
[IO.File]::WriteAllText((Join-Path $out 'owner_assessment_01.json'),($proof|ConvertTo-Json -Depth 15),[Text.UTF8Encoding]::new($false))
$proof|ConvertTo-Json -Depth 6
