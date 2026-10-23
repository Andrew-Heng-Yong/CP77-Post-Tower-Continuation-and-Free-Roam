param(
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$WolvenKitRoot = 'C:\Users\Ayong\Documents\WolvenKit-8.20.0'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -WolvenKitRoot $WolvenKitRoot -HelpersOnly

# Workspace-only shadow witness. No scenes, global fact writes, installation,
# or changes to the v5/v6 rollback. Reuse the proven H10 two-phase ownership form.
$src = Join-Path $WorkspaceRoot 'archive\b0_afterlife_trigger_audit\source'
$out = Join-Path $WorkspaceRoot 'build\Afterlife_TriggerAudit_A1'
$val = Join-Path $WorkspaceRoot 'research\b0_afterlife_native_audit\validation_a1'
$gateDepot = 'towercontinued\afterlife_trigger_audit_a1\gate.questphase'
$ownerDepot = 'towercontinued\afterlife_trigger_audit_a1\trigger_owner.questphase'
$archiveName = 'TowerContinued_Afterlife_TriggerAudit.archive'
$prefix = 'PTFRALMA1_'
$fullTrigger = '$/03_night_city/c_watson/little_china/#loc_q103_afterlife/#loc_q103_afterlife_openworld/#mirror_scene_afterlife/#mirror_tr_afterlife'
$mirrorPath = Join-Path $WorkspaceRoot 'research\b0_mirror_investigation\extracted\raw\base\open_world\scenes\mirrors\mirror_interactions_control.questphase'
$basePath = Join-Path $WorkspaceRoot 'research\q307_extracted\raw\base\quest\cyberpunk2077.questphase'
$parentPath = Join-Path $WorkspaceRoot 'research\q307_extracted\raw\ep1\quest\ep1.quest'
$sectorPath = Join-Path $WorkspaceRoot 'research\b0_afterlife_native_audit\trigger_owner\basegame_3_nightcity\raw\base\worlds\03_night_city\_compiled\default\quest_9e8d73fad623f1b1.streamingsector'
$hashes = @{}
foreach ($path in @($mirrorPath,$basePath,$parentPath,$sectorPath)) {
    $hashes[$path] = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
}
$mirror = Read-Cr2wFile $mirrorPath
$base = Read-Cr2wFile $basePath
$parent = Read-Cr2wFile $parentPath
$sector = Read-Cr2wFile $sectorPath
$nodeTypes = @($sector.RootChunk.Nodes | ForEach-Object {$_.Chunk.GetType().Name} | Sort-Object)
if (@(Compare-Object $nodeTypes @('worldStaticOccluderMeshNode','worldTriggerAreaNode')).Count) { throw 'Reviewed two-node trigger sector changed' }
$prefab = @($mirror.RootChunk.PhasePrefabs | Where-Object {$_.PrefabNodeRef.ToString() -eq '#mirror_scene_afterlife'})
if ($prefab.Count -ne 1) { throw 'Afterlife prefab entry is not unique' }
$outer = (Get-QuestNode $mirror.RootChunk.Graph.Chunk 42).PhaseGraph.Chunk
$leaf = (Get-QuestNode $outer 11).PhaseGraph.Chunk
$trigger = (Get-QuestNode $leaf 3).Condition.Chunk.DeepCopy()
if ($trigger.GetType().Name -ne 'questTriggerCondition' -or $trigger.TriggerAreaRef.ToString() -ne '#mirror_tr_afterlife') { throw 'Native Afterlife trigger precedent changed' }
$trigger.TriggerAreaRef = [WolvenKit.RED4.Types.NodeRef]::op_Implicit($fullTrigger)
$pauseTemplate = Get-QuestNode $base.RootChunk.Graph.Chunk 106
if ($pauseTemplate.GetType().Name -ne 'questPauseConditionNodeDefinition') { throw 'Pause precedent changed' }
$combat = (Get-QuestNode $outer 57).Condition.Chunk.DeepCopy()
if ($combat.Type.Chunk.GetType().Name -ne 'questCharacterCombat_ConditionType') { throw 'Native combat precedent changed' }
$combat.Type.Chunk.Inverted = $true
# Verify native additive fact-writing precedent instead of inventing a counter.
$increment = @($outer.Nodes | Where-Object {
    $_.Chunk.GetType().Name -eq 'questFactsDBManagerNodeDefinition' -and
    $_.Chunk.Type.Chunk.GetType().Name -eq 'questSetVar_NodeType' -and
    $_.Chunk.Type.Chunk.SetExactValue.ToString() -eq 'False'
})
if ($increment.Count -lt 1) { throw 'Vanilla increment precedent missing' }
New-Item -ItemType Directory -Force -Path $src,$out,$val | Out-Null
function Put($g,$n) { Add-RedHandle $g.Nodes $n }
function Link($g,$a,$socket,$b,$dest='In') {
    [void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $a) $socket) (Get-QuestSocket (Get-QuestNode $g $b) $dest))
}
function Count($id,$name) {
    $n = New-SetFactNode $id ($prefix+$name) 1
    $n.Type.Chunk.SetExactValue = $false
    return $n
}
function Pause($id,$condition) {
    $n = $pauseTemplate.DeepCopy(); $n.Id = [uint16]$id
    foreach ($s in $n.Sockets) { $s.Chunk.Connections.Clear() }
    Set-RedHandleProperty $n Condition $condition
    return $n
}
function Trigger($kind) {
    $c = $trigger.DeepCopy()
    $c.Type = [WolvenKit.RED4.Types.Enums+questTriggerConditionType]::$kind
    return $c
}
function PhaseFile($g) {
    $root = [WolvenKit.RED4.Types.questQuestPhaseResource]::new()
    $root.CookingPlatform = [WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC
    Set-RedHandleProperty $root Graph $g
    $f = [WolvenKit.RED4.Archive.CR2W.CR2WFile]::new(); $f.RootChunk = $root
    return $f
}
$guardFacts = [ordered]@{
    PostTowerFreeRoamActive=1; PTFRP0_DR13=1; q307_active=0; q307_done=1
    q307_finished=1; q307_2079=1; q307_main_game_killed=1
    q305_johnny_scene_active=0; mirror_interaction_disabled=0; q115_point_of_no_return=0
    PTFRB0ALM_Enabled=1; PTFRB0ALM_Interrupted=0; PTFRALMA1_Requested=1
}
$guard = [WolvenKit.RED4.Types.questLogicalCondition]::new()
$guard.Operation = [WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
foreach ($fact in $guardFacts.Keys) { Add-RedHandle $guard.Conditions (New-FactCondition $fact $guardFacts[$fact] ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal)) }
Add-RedHandle $guard.Conditions $combat
$gate = [WolvenKit.RED4.Types.questGraphDefinition]::new()
Put $gate (New-InputNode 0 'In1')
Put $gate (Count 1 'Boot')
Put $gate (Pause 2 $guard)
Put $gate (Count 3 'Guard')
$child = [WolvenKit.RED4.Types.questPhaseNodeDefinition]::new(); $child.Id = [uint16]4
$rp = [WolvenKit.RED4.Types.ResourcePath]::op_Implicit($ownerDepot)
$child.PhaseResource = [Activator]::CreateInstance($child.GetType().GetProperty('PhaseResource').PropertyType,[object[]]@($rp))
[void](New-QuestSocket $child 'CutDestination' ([WolvenKit.RED4.Types.Enums+questSocketType]::CutDestination))
[void](New-QuestSocket $child 'In1' ([WolvenKit.RED4.Types.Enums+questSocketType]::Input))
Put $gate $child
Link $gate 0 Out 1; Link $gate 1 Out 2; Link $gate 2 Out 3; Link $gate 3 Out 4 In1
$gateFile = PhaseFile $gate

# Start outside: a preexisting IsInside state cannot masquerade as a crossing.
# Owner marks child execution, NOT proof of streaming completion/registration.
$owner = [WolvenKit.RED4.Types.questGraphDefinition]::new()
Put $owner (New-InputNode 0 'In1')
Put $owner (Count 1 'Owner')
Put $owner (Pause 2 (Trigger 'IsOutside'))
Put $owner (Count 3 'Outside')
Put $owner (Pause 4 (Trigger 'IsInside'))
Put $owner (Count 5 'Inside')
Put $owner (Pause 6 (Trigger 'IsOutside'))
Put $owner (Count 7 'Exits')
Link $owner 0 Out 1; Link $owner 1 Out 2; Link $owner 2 Out 3; Link $owner 3 Out 4
Link $owner 4 Out 5; Link $owner 5 Out 6; Link $owner 6 Out 7; Link $owner 7 Out 4
$ownerFile = PhaseFile $owner
# Exactly the vanilla owner entry, with all other controller prefabs omitted.
$ownerFile.RootChunk.PhasePrefabs.Add($prefab[0].DeepCopy())
Write-Cr2wFile $gateFile (Join-Path $src $gateDepot)
Write-Cr2wFile $ownerFile (Join-Path $src $ownerDepot)
$checks = @{}
foreach ($path in @($gateDepot,$ownerDepot)) {
    $f = Read-Cr2wFile (Join-Path $src $path)
    $key = if ($path -eq $gateDepot) {'gate'} else {'owner'}
    Export-Cr2wJson $f (Join-Path $val ($key+'.json'))
    $checks[$key] = @{nodes=$f.RootChunk.Graph.Chunk.Nodes.Count; edges=@(Get-GraphEdges $f.RootChunk.Graph.Chunk); prefabs=@($f.RootChunk.PhasePrefabs | ForEach-Object {$_.PrefabNodeRef.ToString()})}
    if ($f.EmbeddedFiles.Count -or $f.RootChunk.InplacePhases.Count) { throw 'Unexpected embedded content' }
    foreach ($h in $f.RootChunk.Graph.Chunk.Nodes) {
        $n = $h.Chunk
        if ($n.GetType().Name -eq 'questSceneNodeDefinition') { throw 'Shadow audit must not own a scene' }
        if ($n.GetType().Name -eq 'questFactsDBManagerNodeDefinition') {
            if (-not $n.Type.Chunk.FactName.ToString().StartsWith($prefix) -or $n.Type.Chunk.SetExactValue.ToString() -ne 'False') { throw 'Only fresh additive audit counters may be written' }
        }
    }
}
if ($checks.gate.nodes -ne 5 -or $checks.gate.prefabs.Count -ne 0 -or $checks.owner.nodes -ne 8 -or $checks.owner.prefabs.Count -ne 1 -or $checks.owner.prefabs[0] -ne '#mirror_scene_afterlife') { throw 'Unexpected graph/prefab scope' }
$gateEdges = @('0.Out -> 1.In','1.Out -> 2.In','2.Out -> 3.In','3.Out -> 4.In1')
$ownerEdges = @('0.Out -> 1.In','1.Out -> 2.In','2.Out -> 3.In','3.Out -> 4.In','4.Out -> 5.In','5.Out -> 6.In','6.Out -> 7.In','7.Out -> 4.In')
if (@(Compare-Object $gateEdges $checks.gate.edges).Count -or @(Compare-Object $ownerEdges $checks.owner.edges).Count) { throw 'Unexpected graph edges' }
foreach ($path in $hashes.Keys) { if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $hashes[$path]) { throw 'Research input modified' } }
$crc = 65535
foreach ($b in [Text.Encoding]::UTF8.GetBytes($gateDepot+':1')) {
    $x = ($crc -shr 8) -bxor $b; $x = $x -bxor ($x -shr 4)
    $crc = (($crc -shl 8) -bxor ($x -shl 12) -bxor ($x -shl 5) -bxor $x) -band 65535
}
if (@($parent.RootChunk.Graph.Chunk.Nodes | Where-Object {$_.Chunk.Id.ToString() -eq "$crc"}).Count) { throw 'ArchiveXL ID collides with vanilla EP1 node' }
$paths = @($gateDepot,$ownerDepot) | Sort-Object
$actual = @(Get-ChildItem -LiteralPath $src -Recurse -File | ForEach-Object {[IO.Path]::GetRelativePath($src,$_.FullName)} | Sort-Object)
if (@(Compare-Object $paths $actual).Count) { throw 'Unexpected archive source content' }
$hs = [WolvenKit.Common.Services.HashService]::new(); $hs.Load()
$archivePath = Join-Path $out $archiveName
$stream = [IO.File]::Create($archivePath)
try {
    $writer = [WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())
    if (-not $writer.WriteArchive([IO.DirectoryInfo]::new($src),$stream)) { throw 'Archive write failed' }
} finally { $stream.Dispose() }
$reader = [WolvenKit.RED4.Archive.IO.ArchiveReader]::new(); $arc = $null
if ($reader.ReadArchive($archivePath,$hs,[ref]$arc).ToString() -ne 'NoError') { throw 'Archive reopen failed' }
$packed = @($arc.Files.Values | ForEach-Object {$_.Name} | Sort-Object)
if (@(Compare-Object $paths $packed).Count) { throw 'Archive manifest mismatch' }
foreach ($entry in $arc.Files.Values) {
    $memory = [IO.MemoryStream]::new()
    try {
        $entry.Extract($memory)
        if ([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($memory.ToArray())) -ne (Get-FileHash -LiteralPath (Join-Path $src $entry.Name) -Algorithm SHA256).Hash) { throw 'Archive bytes differ' }
    } finally { $memory.Dispose() }
}
Copy-Item -LiteralPath (Join-Path $WorkspaceRoot ('archive\b0_afterlife_trigger_audit\'+$archiveName+'.xl')) -Destination (Join-Path $out ($archiveName+'.xl'))
$manifest = [ordered]@{
    status='WORKSPACE_ONLY_STATIC_PASS_NOT_INSTALLED_RUNTIME_UNTESTED'; archive=$archiveName
    sha256=(Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash
    resources=$packed; registration_id=$crc; guard_facts=$guardFacts; native_combat='inverted vanilla player combat'
    trigger=$fullTrigger; graphs=$checks; input_hashes=$hashes
    scene_owners=0; vanilla_replacements=@(); runtime_writes='PTFRALMA1_* counters only'
    limitation='Owner counter acknowledges graph entry, not a streaming callback. Inside/Exits are native condition witnesses, not raw callback instrumentation.'
}
[IO.File]::WriteAllText((Join-Path $val 'build_manifest.json'),($manifest | ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
$manifest | ConvertTo-Json -Depth 6
