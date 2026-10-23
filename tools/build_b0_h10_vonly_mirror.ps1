param(
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$WolvenKitRoot = 'C:\Users\Ayong\Documents\WolvenKit-8.20.0'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -WolvenKitRoot $WolvenKitRoot -HelpersOnly

$sourceScene = Join-Path $WorkspaceRoot 'research\b0_h10_generalization\extracted_interactions\raw\base\quest\minor_quests\mq000\scenes\mq000_01_apartment.scene'
$sourcePhase = Join-Path $WorkspaceRoot 'research\b0_h10_generalization\extracted\raw\base\quest\minor_quests\mq000\phases\mq000_vs_apartment_interactions.questphase'
$sourceBase = Join-Path $WorkspaceRoot 'research\q307_extracted\raw\base\quest\cyberpunk2077.questphase'
$sceneDepot = 'towercontinued\b0_h10_vonly_mirror\h10_v_mirror.scene'
$gateDepot = 'towercontinued\b0_h10_vonly_mirror\manual_gate.questphase'
$archiveName = 'TowerContinued_B0_H10_VOnlyMirror.archive'
$src = Join-Path $WorkspaceRoot 'archive\b0_h10_vonly_mirror\source'
$out = Join-Path $WorkspaceRoot 'build\B0_H10_VOnlyMirror'
$val = Join-Path $WorkspaceRoot 'research\b0_h10_vonly_mirror\validation'
New-Item -ItemType Directory -Force -Path $src,$out,$val | Out-Null
$inputs = @($sourceScene,$sourcePhase,$sourceBase)
$inputHashes = @{}
foreach ($p in $inputs) { $inputHashes[$p] = (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash }

$scene = Read-Cr2wFile $sourceScene
# The copied apartment scene declares shower and TV look-at props as
# spawn-on-start. They are unrelated to the mirror entry and must stay inert.
$expectedProps = @('shower','tv_lookat')
$actualProps = @($scene.RootChunk.Props | ForEach-Object { $_.PropName.ToString() } | Sort-Object)
if (@(Compare-Object $expectedProps $actualProps).Count) { throw 'Vanilla prop inventory changed' }
foreach ($prop in $scene.RootChunk.Props) { $prop.SpawnDespawnParams.SpawnOnStart = $false }
$nodes = $scene.RootChunk.SceneGraph.Chunk.Graph
function SceneNode([int]$id) {
    $matches = @($nodes | Where-Object { $_.Chunk.NodeId.Id.ToString() -eq "$id" })
    if ($matches.Count -ne 1) { throw "Scene node $id is not unique" }
    return $matches[0].Chunk
}
function EditDest([int]$id,[int]$socket,[int]$from,[int]$to) {
    $ds = (SceneNode $id).OutputSockets[$socket].Destinations
    $matches = @($ds | Where-Object { $_.NodeId.Id.ToString() -eq "$from" })
    if ($matches.Count -ne 1) { throw "Expected one scene edge $id/$socket->$from" }
    $matches[0].NodeId.Id = [WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]$to)
}
function DropDest([int]$id,[int]$socket,[int]$target) {
    $ds = (SceneNode $id).OutputSockets[$socket].Destinations
    $indices = @(for ($i=0; $i -lt $ds.Count; $i++) { if ($ds[$i].NodeId.Id.ToString() -eq "$target") { $i } })
    if ($indices.Count -ne 1) { throw "Expected one removable scene edge $id/$socket->$target" }
    $ds.RemoveAt($indices[0])
}

# The original pre-Relic mirror branch is 982.True -> 386. Enter that V-body
# selector directly, without reading or writing q101_done or mq055 facts.
EditDest 220 0 1586 386
# Skip the mq055 date/partner choice tree; retain authored V animation,
# mirror device/variant, player workspot, and the Leave choice.
EditDest 222 0 1418 1270
DropDest 220 0 1624
DropDest 226 0 1125
DropDest 226 0 1246
# Cleanup the V mirror actor directly, without reading/writing johnny_mirror.
EditDest 226 0 1000 397
# Keep the locally balanced mirror-blinders reset, but no mq055 fact reset.
DropDest 1051 0 1414
# Original Leave returns to the apartment hub and clears a Johnny sickness
# effect in parallel. End this derivative after the authored five-second
# cleanup delay; neither old-story branch belongs to a V-only action.
$endEdge = (SceneNode 242).OutputSockets[0].Destinations[0].DeepCopy()
DropDest 242 0 509
$johnnyEffectNode = (SceneNode 1084).QuestNode.Chunk.Type.Chunk.Subtype.Chunk
if ($johnnyEffectNode.GetType().Name -ne 'questCharacterManagerParameters_SetStatusEffect') { throw 'Expected Johnny status-effect cleanup precedent changed' }
DropDest 242 0 1084
$endEdge.NodeId.Id = [WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]2)
(SceneNode 242).OutputSockets[0].Destinations.Add($endEdge)

$scenePath = Join-Path $src $sceneDepot
Write-Cr2wFile $scene $scenePath
$sceneCheck = Read-Cr2wFile $scenePath
Export-Cr2wJson $sceneCheck (Join-Path $val 'h10_v_mirror.scene.json')

$vanillaPhase = Read-Cr2wFile $sourcePhase
$base = Read-Cr2wFile $sourceBase
$pauseTemplate = Get-QuestNode $base.RootChunk.Graph.Chunk 106
$sceneTemplate = Get-QuestNode $vanillaPhase.RootChunk.Graph.Chunk 2
$deletionTemplate = Get-QuestNode $vanillaPhase.RootChunk.Graph.Chunk 21
$prefix = 'PTFRB0H10M_'
function Pause([int]$id,[string]$fact,[int]$value) {
    $n=$pauseTemplate.DeepCopy();$n.Id=[uint16]$id
    foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()}
    Set-RedHandleProperty $n Condition (New-FactCondition $fact $value ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
    return $n
}
function Put($g,$n) { Add-RedHandle $g.Nodes $n }
function Link($g,$a,$socket,$b,$dest='In') {
    [void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $a) $socket) (Get-QuestSocket (Get-QuestNode $g $b) $dest))
}
$guardFacts = [ordered]@{
    PostTowerFreeRoamActive=1; PTFRP0_DR13=1; q307_active=0; q307_done=1;
    q307_finished=1; q307_2079=1; q307_main_game_killed=1;
    q305_johnny_scene_active=0;
    PTFRB0H10_Claimed=1; PTFRB0H10_OwnerEntered=1;
    PTFRB0H10L_Claimed=1; PTFRB0H10L_OwnerEntered=1;
    PTFRB0H10A_E_Claimed=1; PTFRB0H10A_E_OwnerEntered=1;
    PTFRB0H10A_B_Claimed=1; PTFRB0H10A_B_OwnerEntered=1;
    PTFRB0H10A_W_Claimed=1; PTFRB0H10A_W_OwnerEntered=1;
    PTFRB0H10M_Active=0
}
$condition = [WolvenKit.RED4.Types.questLogicalCondition]::new()
$condition.Operation = [WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
foreach ($f in $guardFacts.Keys) { Add-RedHandle $condition.Conditions (New-FactCondition $f $guardFacts[$f] ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal)) }
# Retain only the original H10 player-inside trigger and no-incoming-call
# conditions; omit apartment/story progression facts from the original gate.
$h10Gate = (Get-QuestNode $vanillaPhase.RootChunk.Graph.Chunk 19).Condition.Chunk
$h10Trigger = @($h10Gate.Conditions | Where-Object { $_.Chunk.GetType().Name -eq 'questTriggerCondition' })
$noIncomingCall = @($h10Gate.Conditions | Where-Object { $_.Chunk.GetType().Name -eq 'questUICondition' })
if ($h10Trigger.Count -ne 1 -or $noIncomingCall.Count -ne 1) { throw 'Vanilla H10 context gate shape changed' }
Add-RedHandle $condition.Conditions $h10Trigger[0].Chunk.DeepCopy()
Add-RedHandle $condition.Conditions $noIncomingCall[0].Chunk.DeepCopy()
$graph = [WolvenKit.RED4.Types.questGraphDefinition]::new()
Put $graph (New-InputNode 0 'In1')
Put $graph (New-SetFactNode 1 ($prefix+'Ready') 1)
Put $graph (Pause 2 ($prefix+'Request') 1)
Put $graph (New-SetFactNode 3 ($prefix+'Request') 0)
Put $graph (New-ConditionNode 4 $condition)
Put $graph (New-SetFactNode 5 ($prefix+'Rejected') 1)
Put $graph (New-SetFactNode 6 ($prefix+'Active') 1)
$sceneNode=$sceneTemplate.DeepCopy();$sceneNode.Id=[uint16]7
foreach($s in $sceneNode.Sockets){$s.Chunk.Connections.Clear()}
$sceneResourcePath=[WolvenKit.RED4.Types.ResourcePath]::op_Implicit($sceneDepot)
$sceneNode.SceneFile=[Activator]::CreateInstance($sceneNode.GetType().GetProperty('SceneFile').PropertyType,[object[]]@($sceneResourcePath))
Put $graph $sceneNode
$del=$deletionTemplate.DeepCopy();$del.Id=[uint16]8
foreach($s in $del.Sockets){$s.Chunk.Connections.Clear()}
Put $graph $del
Put $graph (New-SetFactNode 9 ($prefix+'Active') 0)
Put $graph (New-SetFactNode 10 ($prefix+'Completed') 1)
Put $graph (New-SetFactNode 11 ($prefix+'Ready') 1)
Put $graph (New-SetFactNode 12 ($prefix+'Interrupted') 1)
Link $graph 0 Out 1; Link $graph 1 Out 2; Link $graph 2 Out 3; Link $graph 3 Out 4
Link $graph 4 False 5; Link $graph 5 Out 2
Link $graph 4 True 6; Link $graph 6 Out 7 in_mirror
Link $graph 7 out 8; Link $graph 8 Out 9; Link $graph 9 Out 10; Link $graph 10 Out 11; Link $graph 11 Out 2
Link $graph 7 'Default INT' 12
$root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new()
$root.CookingPlatform=[WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC
Set-RedHandleProperty $root Graph $graph
$gate=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$gate.RootChunk=$root
$gatePath=Join-Path $src $gateDepot
Write-Cr2wFile $gate $gatePath
$gateCheck=Read-Cr2wFile $gatePath
Export-Cr2wJson $gateCheck (Join-Path $val 'manual_gate.questphase.json')

foreach($p in $inputs){if((Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash -ne $inputHashes[$p]){throw 'Vanilla source changed'}}
$allowed=@($gateDepot,$sceneDepot)|Sort-Object
$actual=@(Get-ChildItem -LiteralPath $src -File -Recurse|ForEach-Object{[IO.Path]::GetRelativePath($src,$_.FullName)}|Sort-Object)
if(@(Compare-Object $allowed $actual).Count){throw 'Unexpected source file'}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$stream=[IO.File]::Create((Join-Path $out $archiveName))
try{$writer=[WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new());if(-not $writer.WriteArchive([IO.DirectoryInfo]::new($src),$stream)){throw 'Archive write failed'}}finally{$stream.Dispose()}
$reader=[WolvenKit.RED4.Archive.IO.ArchiveReader]::new();$arc=$null
if($reader.ReadArchive((Join-Path $out $archiveName),$hs,[ref]$arc).ToString() -ne 'NoError'){throw 'Archive did not reopen'}
$packed=@($arc.Files.Values|ForEach-Object{$_.Name}|Sort-Object)
if(@(Compare-Object $allowed $packed).Count){throw 'Archive manifest mismatch'}
foreach($e in $arc.Files.Values){$ms=[IO.MemoryStream]::new();try{$e.Extract($ms);$hash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($ms.ToArray()));if($hash -ne (Get-FileHash -LiteralPath (Join-Path $src $e.Name) -Algorithm SHA256).Hash){throw "Packed bytes differ: $($e.Name)"}}finally{$ms.Dispose()}}
$manifest=[ordered]@{status='BLOCKED_DO_NOT_INSTALL';blocker='Default INT has no proven local resource cleanup';additional_preflight_unknown='Live H10 scene marker and mirror device/variant resolution';archive=$archiveName;sha256=(Get-FileHash -LiteralPath (Join-Path $out $archiveName) -Algorithm SHA256).Hash;resources=$packed;source_hashes=$inputHashes;guard_facts=$guardFacts;vanilla_replacements=@();scene_entry='in_mirror';manual_fact=$prefix+'Request'}
[IO.File]::WriteAllText((Join-Path $val 'build_manifest.json'),($manifest|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
$manifest|ConvertTo-Json -Depth 8
