param(
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$WolvenKitRoot = 'C:\Users\Ayong\Documents\WolvenKit-8.20.0'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -WolvenKitRoot $WolvenKitRoot -HelpersOnly

$src = Join-Path $WorkspaceRoot 'archive\b0_h10_architecture\source'
$out = Join-Path $WorkspaceRoot 'build\B0_H10_Architecture'
$val = Join-Path $WorkspaceRoot 'research\b0_h10_architecture\validation'
$name = 'TowerContinued_B0_H10_Architecture.archive'
New-Item -ItemType Directory -Force -Path $src,$out,$val | Out-Null

$normalPath = Join-Path $WorkspaceRoot 'research\b0_missing_content\h10_owners\raw\base\quest\minor_quests\mq000\phases\mq000_vs_apartment_decorations.questphase'
$parentPath = Join-Path $WorkspaceRoot 'research\q307_extracted\raw\ep1\quest\ep1.quest'
$basePath = Join-Path $WorkspaceRoot 'research\q307_extracted\raw\base\quest\cyberpunk2077.questphase'
$normal = Read-Cr2wFile $normalPath
$parent = Read-Cr2wFile $parentPath
$base = Read-Cr2wFile $basePath
$parentGraph = $parent.RootChunk.Graph.Chunk
$start = Get-QuestNode $parentGraph 1
if ($start.GetType().Name -ne 'questStartNodeDefinition') { throw 'EP1 registration anchor changed.' }
[void](Get-QuestSocket $start 'Out')
$pauseTemplate = Get-QuestNode $base.RootChunk.Graph.Chunk 106
if ($pauseTemplate.GetType().Name -ne 'questPauseConditionNodeDefinition') { throw 'Pause precedent changed.' }

$sources = @($normalPath,$parentPath,$basePath)
$sourceHashes = @{}
foreach ($p in $sources) { $sourceHashes[$p] = (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash }
$targets = @(
    [ordered]@{ key='entrance'; prefix='PTFRB0H10A_E_'; prefab='#vs_apartment_arch_entrance'; depends=@() },
    [ordered]@{ key='bedroom'; prefix='PTFRB0H10A_B_'; prefab='#vs_apartment_arch_bedroom'; depends=@('PTFRB0H10A_E_Claimed','PTFRB0H10A_E_OwnerEntered') },
    [ordered]@{ key='bathroom'; prefix='PTFRB0H10A_W_'; prefab='#vs_apartment_arch_bathroom'; depends=@('PTFRB0H10A_B_Claimed','PTFRB0H10A_B_OwnerEntered') }
)
$paths = [System.Collections.Generic.List[string]]::new()
$expected = @{}
$guards = @{}
$registrations = @{}

function Put($g,$n) { Add-RedHandle $g.Nodes $n }
function Link($g,$a,$sock,$b,$destSocket='In') {
    [void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $a) $sock) (Get-QuestSocket (Get-QuestNode $g $b) $destSocket))
}
function Pause($id,$fact,$value) {
    $n = $pauseTemplate.DeepCopy(); $n.Id = [uint16]$id
    foreach ($s in $n.Sockets) { $s.Chunk.Connections.Clear() }
    Set-RedHandleProperty $n Condition (New-FactCondition $fact $value ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
    return $n
}
function PhaseFile($g) {
    $root = [WolvenKit.RED4.Types.questQuestPhaseResource]::new()
    $root.CookingPlatform = [WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC
    Set-RedHandleProperty $root Graph $g
    $file = [WolvenKit.RED4.Archive.CR2W.CR2WFile]::new(); $file.RootChunk = $root
    return $file
}
function RegistrationId($phasePath) {
    $crc = 65535
    foreach ($byte in [Text.Encoding]::UTF8.GetBytes($phasePath+':1')) {
        $x = ($crc -shr 8) -bxor $byte; $x = $x -bxor ($x -shr 4)
        $crc = (($crc -shl 8) -bxor ($x -shl 12) -bxor ($x -shl 5) -bxor $x) -band 65535
    }
    return $crc
}

foreach ($target in $targets) {
    $key = $target.key
    $prefix = $target.prefix
    $gatePath = "towercontinued\b0_h10_architecture\${key}_gate.questphase"
    $ownerPath = "towercontinued\b0_h10_architecture\${key}_owner.questphase"
    $paths.Add($gatePath); $paths.Add($ownerPath)
    $entry = @($normal.RootChunk.PhasePrefabs | Where-Object { $_.PrefabNodeRef.ToString() -eq $target.prefab })
    if ($entry.Count -ne 1) { throw "Owner entry not unique: $($target.prefab)" }

    $guardFacts = [ordered]@{
        PostTowerFreeRoamActive=1; PTFRP0_DR13=1; q307_active=0; q307_done=1
        q307_finished=1; q307_2079=1; q307_main_game_killed=1
        PTFRB0H10_Claimed=1; PTFRB0H10_OwnerEntered=1
        PTFRB0H10L_Claimed=1; PTFRB0H10L_OwnerEntered=1
    }
    foreach ($dep in $target.depends) { $guardFacts[$dep] = 1 }
    $guardFacts[$prefix+'Claimed'] = 0
    $guardFacts[$prefix+'OwnerEntered'] = 0
    $guardFacts[$prefix+'Hold'] = 0
    $guards[$key] = $guardFacts
    $guard = [WolvenKit.RED4.Types.questLogicalCondition]::new()
    $guard.Operation = [WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
    foreach ($f in $guardFacts.Keys) {
        Add-RedHandle $guard.Conditions (New-FactCondition $f $guardFacts[$f] ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
    }

    $gate = [WolvenKit.RED4.Types.questGraphDefinition]::new()
    Put $gate (New-InputNode 0 'In1')
    Put $gate (New-SetFactNode 1 ($prefix+'Ready') 1)
    Put $gate (Pause 2 ($prefix+'Request') 1)
    Put $gate (New-SetFactNode 3 ($prefix+'Request') 0)
    Put $gate (New-ConditionNode 4 $guard)
    Put $gate (New-SetFactNode 5 ($prefix+'Claimed') 1)
    Put $gate (New-SetFactNode 6 ($prefix+'Ready') 0)
    $phase = [WolvenKit.RED4.Types.questPhaseNodeDefinition]::new(); $phase.Id = [uint16]7
    $rp = [WolvenKit.RED4.Types.ResourcePath]::op_Implicit($ownerPath)
    $phase.PhaseResource = [System.Activator]::CreateInstance($phase.GetType().GetProperty('PhaseResource').PropertyType,[object[]]@($rp))
    [void](New-QuestSocket $phase 'CutDestination' ([WolvenKit.RED4.Types.Enums+questSocketType]::CutDestination))
    [void](New-QuestSocket $phase 'In1' ([WolvenKit.RED4.Types.Enums+questSocketType]::Input))
    Put $gate $phase
    Put $gate (New-SetFactNode 8 ($prefix+'Rejected') 1)
    Link $gate 0 Out 1; Link $gate 1 Out 2; Link $gate 2 Out 3; Link $gate 3 Out 4
    Link $gate 4 True 5; Link $gate 5 Out 6; Link $gate 6 Out 7 In1
    Link $gate 4 False 8; Link $gate 8 Out 2

    $owner = [WolvenKit.RED4.Types.questGraphDefinition]::new()
    Put $owner (New-InputNode 0 'In1')
    Put $owner (New-SetFactNode 1 ($prefix+'OwnerEntered') 1)
    Put $owner (Pause 2 ($prefix+'Hold') 1)
    Link $owner 0 Out 1; Link $owner 1 Out 2
    $ownerFile = PhaseFile $owner
    $ownerFile.RootChunk.PhasePrefabs.Add($entry[0].DeepCopy())
    Write-Cr2wFile (PhaseFile $gate) (Join-Path $src $gatePath)
    Write-Cr2wFile $ownerFile (Join-Path $src $ownerPath)

    foreach ($record in @(@{path=$gatePath;label='gate';count=9;prefabs=0},@{path=$ownerPath;label='owner';count=3;prefabs=1})) {
        $f = Read-Cr2wFile (Join-Path $src $record.path)
        $g = $f.RootChunk.Graph.Chunk
        if ($g.Nodes.Count -ne $record.count -or $f.RootChunk.PhasePrefabs.Count -ne $record.prefabs -or $f.EmbeddedFiles.Count -ne 0 -or $f.RootChunk.InplacePhases.Count -ne 0) { throw "Serialized scope mismatch: $($record.path)" }
        if ($record.label -eq 'owner' -and $f.RootChunk.PhasePrefabs[0].PrefabNodeRef.ToString() -ne $target.prefab) { throw "Wrong prefab: $key" }
        Export-Cr2wJson $f (Join-Path $val ($key+'_'+$record.label+'.json'))
        $expected[$key+'_'+$record.label] = [ordered]@{nodes=$g.Nodes.Count;edges=@(Get-GraphEdges $g);prefabs=@($f.RootChunk.PhasePrefabs | ForEach-Object {$_.PrefabNodeRef.ToString()})}
    }
    $id = RegistrationId $gatePath
    if (@($parentGraph.Nodes | Where-Object { $_.Chunk.Id.ToString() -eq "$id" }).Count -or $id -in @(9908,19904) -or $id -in @($registrations.Values)) { throw "ArchiveXL ID collision: $key $id" }
    $registrations[$key] = $id
}

$expectedGate = @('0.Out -> 1.In','1.Out -> 2.In','2.Out -> 3.In','3.Out -> 4.In','4.True -> 5.In','5.Out -> 6.In','6.Out -> 7.In1','4.False -> 8.In','8.Out -> 2.In') | Sort-Object
foreach ($target in $targets) {
    $key = $target.key
    if (@(Compare-Object $expectedGate $expected[$key+'_gate'].edges).Count -or @(Compare-Object @('0.Out -> 1.In','1.Out -> 2.In') $expected[$key+'_owner'].edges).Count) { throw "Unexpected edges: $key" }
}
foreach ($p in $sources) { if ((Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash -ne $sourceHashes[$p]) { throw 'Research input changed.' } }
$actual = @(Get-ChildItem -LiteralPath $src -Recurse -File | ForEach-Object {[IO.Path]::GetRelativePath($src,$_.FullName)} | Sort-Object)
if (@(Compare-Object @($paths | Sort-Object) $actual).Count) { throw 'Unexpected archive source file.' }

$hs = [WolvenKit.Common.Services.HashService]::new(); $hs.Load()
$stream = [IO.File]::Create((Join-Path $out $name))
try {
    $writer = [WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())
    if (-not $writer.WriteArchive([IO.DirectoryInfo]::new($src),$stream)) { throw 'Archive writer failed.' }
} finally { $stream.Dispose() }
$reader = [WolvenKit.RED4.Archive.IO.ArchiveReader]::new(); $arc = $null
if ($reader.ReadArchive((Join-Path $out $name),$hs,[ref]$arc).ToString() -ne 'NoError') { throw 'Archive did not reopen.' }
$packed = @($arc.Files.Values | ForEach-Object {$_.Name} | Sort-Object)
if ($packed.Count -ne 6 -or @(Compare-Object @($paths | Sort-Object) $packed).Count) { throw 'Archive contents mismatch.' }
foreach ($e in $arc.Files.Values) {
    $memory = [IO.MemoryStream]::new()
    try {
        $e.Extract($memory)
        $digest = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($memory.ToArray()))
        if ($digest -ne (Get-FileHash -LiteralPath (Join-Path $src $e.Name) -Algorithm SHA256).Hash) { throw 'Packed resource differs from source.' }
    } finally { $memory.Dispose() }
}
Copy-Item -LiteralPath (Join-Path $WorkspaceRoot ('archive\b0_h10_architecture\'+$name+'.xl')) -Destination (Join-Path $out ($name+'.xl'))
$manifest = [ordered]@{status='STATIC_BUILD_PASS_RUNTIME_UNTESTED';archive=$name;sha256=(Get-FileHash -LiteralPath (Join-Path $out $name) -Algorithm SHA256).Hash;resources=$packed;registration_parent='ep1\quest\ep1.quest';registration_anchor=1;registration_ids=$registrations;guards=$guards;graphs=$expected;vanilla_replacements=@();input_hashes=$sourceHashes}
[IO.File]::WriteAllText((Join-Path $val 'build_manifest.json'),($manifest | ConvertTo-Json -Depth 12),[Text.UTF8Encoding]::new($false))
$manifest | ConvertTo-Json -Depth 5
