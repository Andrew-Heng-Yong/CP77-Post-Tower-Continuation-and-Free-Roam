param(
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$WolvenKitRoot = 'C:\Users\Ayong\Documents\WolvenKit-8.20.0'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -WolvenKitRoot $WolvenKitRoot -HelpersOnly
$src = Join-Path $WorkspaceRoot 'archive\b0_h10_living\source'
$out = Join-Path $WorkspaceRoot 'build\B0_H10_Living'
$val = Join-Path $WorkspaceRoot 'research\b0_h10_living\validation'
$gatePath = 'towercontinued\b0_h10_living\manual_gate.questphase'
$ownerPath = 'towercontinued\b0_h10_living\living_owner.questphase'
$paths = @($gatePath, $ownerPath) | Sort-Object
$name = 'TowerContinued_B0_H10_Living.archive'
$prefix = 'PTFRB0H10L_'
New-Item -ItemType Directory -Force -Path $src,$out,$val | Out-Null

# Read only the exact existing research copies; never run an old builder.
$normalPath = Join-Path $WorkspaceRoot 'research\b0_missing_content\h10_owners\raw\base\quest\minor_quests\mq000\phases\mq000_vs_apartment_decorations.questphase'
$normal = Read-Cr2wFile $normalPath
$entry = @($normal.RootChunk.PhasePrefabs | Where-Object { $_.PrefabNodeRef.ToString() -eq '#vs_apartment_arch_living' })
if ($entry.Count -ne 1) { throw 'Living ownership entry is not unique.' }
$parentPath = Join-Path $WorkspaceRoot 'research\q307_extracted\raw\ep1\quest\ep1.quest'
$parent = Read-Cr2wFile $parentPath
$parentGraph = $parent.RootChunk.Graph.Chunk
$start = Get-QuestNode $parentGraph 1
if ($start.GetType().Name -ne 'questStartNodeDefinition') { throw 'EP1 registration anchor changed.' }
[void](Get-QuestSocket $start 'Out')
$basePath = Join-Path $WorkspaceRoot 'research\q307_extracted\raw\base\quest\cyberpunk2077.questphase'
$base = Read-Cr2wFile $basePath
$pauseTemplate = Get-QuestNode $base.RootChunk.Graph.Chunk 106
if ($pauseTemplate.GetType().Name -ne 'questPauseConditionNodeDefinition') { throw 'Pause precedent changed.' }
$sourceHashes = @{}
foreach ($p in @($normalPath,$parentPath,$basePath)) { $sourceHashes[$p] = (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash }

function Put($g,$n) { Add-RedHandle $g.Nodes $n }
function Link($g,$a,$sock,$b,$destSocket='In') {
    [void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $a) $sock) (Get-QuestSocket (Get-QuestNode $g $b) $destSocket))
}
function Pause($id,$fact,$value) {
    $n = $pauseTemplate.DeepCopy(); $n.Id=[uint16]$id
    foreach ($s in $n.Sockets) { $s.Chunk.Connections.Clear() }
    Set-RedHandleProperty $n Condition (New-FactCondition $fact $value ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
    return $n
}
function PhaseFile($g) {
    $root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new()
    $root.CookingPlatform=[WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC
    Set-RedHandleProperty $root Graph $g
    $file=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new(); $file.RootChunk=$root
    return $file
}
$guardFacts = [ordered]@{
    PostTowerFreeRoamActive=1; PTFRP0_DR13=1; q307_active=0; q307_done=1
    q307_finished=1; q307_2079=1; q307_main_game_killed=1
    PTFRB0H10_Claimed=1; PTFRB0H10_OwnerEntered=1
    PTFRB0H10L_Claimed=0; PTFRB0H10L_OwnerEntered=0; PTFRB0H10L_Hold=0
}
$guard=[WolvenKit.RED4.Types.questLogicalCondition]::new()
$guard.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
foreach ($f in $guardFacts.Keys) { Add-RedHandle $guard.Conditions (New-FactCondition $f $guardFacts[$f] ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal)) }

$gate=[WolvenKit.RED4.Types.questGraphDefinition]::new()
Put $gate (New-InputNode 0 'In1')
Put $gate (New-SetFactNode 1 ($prefix+'Ready') 1)
Put $gate (Pause 2 ($prefix+'Request') 1)
Put $gate (New-SetFactNode 3 ($prefix+'Request') 0)
Put $gate (New-ConditionNode 4 $guard)
Put $gate (New-SetFactNode 5 ($prefix+'Claimed') 1)
Put $gate (New-SetFactNode 6 ($prefix+'Ready') 0)
$phase=[WolvenKit.RED4.Types.questPhaseNodeDefinition]::new(); $phase.Id=[uint16]7
$rp=[WolvenKit.RED4.Types.ResourcePath]::op_Implicit($ownerPath)
$phase.PhaseResource=[System.Activator]::CreateInstance($phase.GetType().GetProperty('PhaseResource').PropertyType,[object[]]@($rp))
[void](New-QuestSocket $phase 'CutDestination' ([WolvenKit.RED4.Types.Enums+questSocketType]::CutDestination))
[void](New-QuestSocket $phase 'In1' ([WolvenKit.RED4.Types.Enums+questSocketType]::Input))
Put $gate $phase
Put $gate (New-SetFactNode 8 ($prefix+'Rejected') 1)
Link $gate 0 Out 1; Link $gate 1 Out 2; Link $gate 2 Out 3; Link $gate 3 Out 4
Link $gate 4 True 5; Link $gate 5 Out 6; Link $gate 6 Out 7 In1
Link $gate 4 False 8; Link $gate 8 Out 2
$gateFile=PhaseFile $gate

$owner=[WolvenKit.RED4.Types.questGraphDefinition]::new()
Put $owner (New-InputNode 0 'In1')
Put $owner (New-SetFactNode 1 ($prefix+'OwnerEntered') 1)
# No writer or public command exists for Hold; no terminating output/retry loop.
Put $owner (Pause 2 ($prefix+'Hold') 1)
Link $owner 0 Out 1; Link $owner 1 Out 2
$ownerFile=PhaseFile $owner
$ownerFile.RootChunk.PhasePrefabs.Add($entry[0].DeepCopy())
Write-Cr2wFile $gateFile (Join-Path $src $gatePath)
Write-Cr2wFile $ownerFile (Join-Path $src $ownerPath)

# Inspect the serialized files, not just the in-memory construction.
$checks=@{}
foreach ($path in $paths) {
    $f=Read-Cr2wFile (Join-Path $src $path)
    $g=$f.RootChunk.Graph.Chunk
    $key=if($path -eq $gatePath){'gate'}else{'owner'}
    Export-Cr2wJson $f (Join-Path $val ($key+'.json'))
    $checks[$key]=[ordered]@{nodes=$g.Nodes.Count; edges=@(Get-GraphEdges $g); prefabs=@($f.RootChunk.PhasePrefabs | ForEach-Object {$_.PrefabNodeRef.ToString()})}
    if ($f.EmbeddedFiles.Count -ne 0 -or $f.RootChunk.InplacePhases.Count -ne 0) { throw 'Unexpected embedded/inplace content.' }
}
if ($checks.gate.nodes -ne 9 -or $checks.gate.prefabs.Count -ne 0 -or $checks.owner.nodes -ne 3 -or $checks.owner.prefabs.Count -ne 1 -or $checks.owner.prefabs[0] -ne '#vs_apartment_arch_living') { throw 'Scope/count mismatch.' }
$expectedGate=@('0.Out -> 1.In','1.Out -> 2.In','2.Out -> 3.In','3.Out -> 4.In','4.True -> 5.In','5.Out -> 6.In','6.Out -> 7.In1','4.False -> 8.In','8.Out -> 2.In') | Sort-Object
if (@(Compare-Object $expectedGate $checks.gate.edges).Count -or @(Compare-Object @('0.Out -> 1.In','1.Out -> 2.In') $checks.owner.edges).Count) { throw 'Unexpected execution edges.' }
foreach ($p in $sourceHashes.Keys) { if ((Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash -ne $sourceHashes[$p]) { throw 'Research input changed.' } }

# Match ArchiveXL's CRC16 registration ID and reject a vanilla node collision.
$crc=65535
foreach ($byte in [Text.Encoding]::UTF8.GetBytes($gatePath+':1')) {
    $x=($crc -shr 8) -bxor $byte; $x=$x -bxor ($x -shr 4)
    $crc=(($crc -shl 8) -bxor ($x -shl 12) -bxor ($x -shl 5) -bxor $x) -band 65535
}
if (@($parentGraph.Nodes | Where-Object { $_.Chunk.Id.ToString() -eq "$crc" }).Count) { throw 'ArchiveXL ID collides with EP1 vanilla node.' }
$actual=@(Get-ChildItem -LiteralPath $src -Recurse -File | ForEach-Object {[IO.Path]::GetRelativePath($src,$_.FullName)} | Sort-Object)
if (@(Compare-Object $paths $actual).Count) { throw 'Unexpected archive source file.' }
$hs=[WolvenKit.Common.Services.HashService]::new(); $hs.Load()
$stream=[IO.File]::Create((Join-Path $out $name))
try {
    $writer=[WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())
    if (-not $writer.WriteArchive([IO.DirectoryInfo]::new($src),$stream)) { throw 'Archive writer failed.' }
} finally { $stream.Dispose() }
$reader=[WolvenKit.RED4.Archive.IO.ArchiveReader]::new(); $arc=$null
if ($reader.ReadArchive((Join-Path $out $name),$hs,[ref]$arc).ToString() -ne 'NoError') { throw 'Archive did not reopen.' }
$packed=@($arc.Files.Values | ForEach-Object {$_.Name} | Sort-Object)
if ($packed.Count -ne 2 -or @(Compare-Object $paths $packed).Count) { throw 'Archive scope mismatch.' }
foreach ($e in $arc.Files.Values) {
    $memory=[IO.MemoryStream]::new()
    try {
        $e.Extract($memory)
        $unpacked=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($memory.ToArray()))
        if ($unpacked -ne (Get-FileHash -LiteralPath (Join-Path $src $e.Name) -Algorithm SHA256).Hash) { throw 'Packed resource differs from validated source.' }
    } finally { $memory.Dispose() }
}
Copy-Item -LiteralPath (Join-Path $WorkspaceRoot ('archive\b0_h10_living\'+$name+'.xl')) -Destination (Join-Path $out ($name+'.xl'))
$manifest=[ordered]@{status='STATIC_BUILD_PASS_RUNTIME_UNTESTED';archive=$name;sha256=(Get-FileHash -LiteralPath (Join-Path $out $name) -Algorithm SHA256).Hash;resources=$packed;registration_parent='ep1\quest\ep1.quest';registration_anchor=1;registration_id=$crc;native_guard=$guardFacts;graphs=$checks;vanilla_replacements=@();unrelated_prefabs=@();input_hashes=$sourceHashes}
[IO.File]::WriteAllText((Join-Path $val 'build_manifest.json'),($manifest | ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
$manifest | ConvertTo-Json -Depth 6
