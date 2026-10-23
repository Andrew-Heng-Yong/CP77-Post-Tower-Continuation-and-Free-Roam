param(
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$WolvenKitRoot = 'C:\Users\Ayong\Documents\WolvenKit-8.20.0',
    [switch]$Automatic,
    [switch]$RedDirtOnly
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($RedDirtOnly -and $Automatic) { throw 'Red Dirt C5 is opt-in only' }
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -WolvenKitRoot $WolvenKitRoot -HelpersOnly

# C3/C4 use ordinary leaves without extra story facts. The opt-in Red Dirt
# variant retains its additional scene-local sq011 choice condition. Coyote is C2.
$siteIds = if ($RedDirtOnly) { @(42) } else { @(5,8,21,22,23,25,26,27,28,29,30,31,32,33,34,35,36,38,39,40,41,43,44,49,63) }
$excluded = [ordered]@{
    '4'='scene reads sq029_stash'; '13'='relationship home; nonstandard scene';
    '14'='Peralez story interior'; '15'='nonstandard leaf'
    '16'='ending penthouse and nonstandard leaf'; '17'='Sunset ending staging'
    '18'='no world trigger descriptor'; '19'='Konpeki story interior';
    '20'='relationship home; nonstandard scene'
    '42'='scene reads sq011_mirror_off'; '48'='already restored by C2'
}
if ($RedDirtOnly) { $excluded = [ordered]@{ 'all-other-sites'='single-site opt-in scope' } }
$version = if ($RedDirtOnly) { 'c5_red_dirt' } elseif ($Automatic) { 'c4' } else { 'c3' }
$src = Join-Path $WorkspaceRoot ("archive\b0_ordinary_mirrors_$version\source")
$out = Join-Path $WorkspaceRoot ("build\OrdinaryMirrors_"+$version.ToUpperInvariant())
$val = Join-Path $WorkspaceRoot ("research\b0_mirror_rollout\validation_$version")
$archiveName = 'TowerContinued_OrdinaryMirrors_'+$version.ToUpperInvariant()+'.archive'
$mirrorPath = Join-Path $WorkspaceRoot 'research\b0_mirror_investigation\extracted\raw\base\open_world\scenes\mirrors\mirror_interactions_control.questphase'
$basePath = Join-Path $WorkspaceRoot 'research\q307_extracted\raw\base\quest\cyberpunk2077.questphase'
$parentPath = Join-Path $WorkspaceRoot 'research\q307_extracted\raw\ep1\quest\ep1.quest'
$vanillaRoot = Join-Path $WorkspaceRoot 'research\b0_mirror_rollout\vanilla_ordinary\raw'
$mirror = Read-Cr2wFile $mirrorPath
$base = Read-Cr2wFile $basePath
$parent = Read-Cr2wFile $parentPath
$outer = (Get-QuestNode $mirror.RootChunk.Graph.Chunk 42).PhaseGraph.Chunk
$pauseTemplate = Get-QuestNode $base.RootChunk.Graph.Chunk 106
$combat = (Get-QuestNode $outer 57).Condition.Chunk.DeepCopy()
if ($combat.Type.Chunk.GetType().Name -ne 'questCharacterCombat_ConditionType') { throw 'Vanilla combat guard changed' }
$combat.Type.Chunk.Inverted = $true
New-Item -ItemType Directory -Force -Path $src,$out,$val | Out-Null

function Put($graph,$node) { Add-RedHandle $graph.Nodes $node }
function Link($graph,$from,$socket,$to,$dest='In') {
    [void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $graph $from) $socket) (Get-QuestSocket (Get-QuestNode $graph $to) $dest))
}
function SetCount($id,$name) {
    $node = New-SetFactNode $id $name 1
    $node.Type.Chunk.SetExactValue = $false
    return $node
}
function Pause($id,$condition) {
    $node = $pauseTemplate.DeepCopy(); $node.Id = [uint16]$id
    foreach ($socket in $node.Sockets) { $socket.Chunk.Connections.Clear() }
    Set-RedHandleProperty $node Condition $condition
    return $node
}
function PhaseFile($graph) {
    $root = [WolvenKit.RED4.Types.questQuestPhaseResource]::new()
    $root.CookingPlatform = [WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC
    Set-RedHandleProperty $root Graph $graph
    $file = [WolvenKit.RED4.Archive.CR2W.CR2WFile]::new(); $file.RootChunk = $root
    return $file
}
function Guard($entry) {
    $condition = [WolvenKit.RED4.Types.questLogicalCondition]::new()
    $condition.Operation = [WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
    foreach ($item in $script:guardFacts.GetEnumerator()) {
        Add-RedHandle $condition.Conditions (New-FactCondition $item.Key $item.Value ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
    }
    if ($null -ne $entry) { Add-RedHandle $condition.Conditions $entry.DeepCopy() }
    Add-RedHandle $condition.Conditions $script:combat.DeepCopy()
    return $condition
}
$guardFacts = [ordered]@{
    PostTowerFreeRoamActive=1; PTFRP0_DR13=1; q307_active=0; q307_done=1
    q307_finished=1; q307_2079=1; q307_main_game_killed=1
    q305_johnny_scene_active=0; mirror_interaction_disabled=0
    q115_point_of_no_return=0
}
if ($RedDirtOnly) {
    $guardFacts['PTFRBM42_Enabled'] = 1
    $guardFacts['PTFRBASE_Suspended'] = 0
    $guardFacts['PTFRBM42_Interrupted'] = 0
    # Exact vanilla Look gate, including its trailing space. Never write it.
    $guardFacts['sq011_mirror_off '] = 0
}
elseif (-not $Automatic) { $guardFacts['PTFRBM_Enabled'] = 1 }
$records = [System.Collections.Generic.List[object]]::new()
$resources = [System.Collections.Generic.List[string]]::new()
$ids = [System.Collections.Generic.HashSet[int]]::new()
$xlLines = [System.Collections.Generic.List[string]]::new()
$xlLines.Add($(if ($RedDirtOnly) {
    '# Opt-in single Red Dirt mirror; preserve original sq011 choice gate.'
} elseif ($Automatic) {
    '# Automatic post-Tower ordinary mirror cohort; excludes story/ending sites and Coyote C2.'
} else {
    '# Opt-in post-Tower ordinary mirror cohort; excludes story/ending sites and Coyote C2.'
}))
$xlLines.Add('quest:')
$xlLines.Add('  phases:')
$script:block = $null
foreach ($siteId in $siteIds) {
    $leaf = (Get-QuestNode $outer $siteId).PhaseGraph.Chunk
    if ($leaf.Nodes.Count -ne 4) { throw "Site ${siteId}: nonstandard leaf" }
    $templateScene = @($leaf.Nodes | Where-Object {$_.Chunk.GetType().Name -eq 'questSceneNodeDefinition'})
    $pauses = @($leaf.Nodes | Where-Object {$_.Chunk.GetType().Name -eq 'questPauseConditionNodeDefinition'})
    if ($templateScene.Count -ne 1 -or $pauses.Count -ne 2) { throw "Site ${siteId}: shape changed" }
    $templateScene = $templateScene[0].Chunk
    $entry = @($pauses | Where-Object {$_.Chunk.Condition.Chunk.GetType().Name -eq 'questTriggerCondition'})
    $delay = @($pauses | Where-Object {$_.Chunk.Condition.Chunk.GetType().Name -eq 'questTimeCondition'})
    if ($entry.Count -ne 1 -or $delay.Count -ne 1) { throw "Site ${siteId}: entry/delay changed" }
    $entry = $entry[0].Chunk.Condition.Chunk.DeepCopy()
    $delay = $delay[0].Chunk
    if ($entry.Type.ToString() -ne 'IsInside' -or $delay.Condition.Chunk.Type.Chunk.Seconds.ToString() -ne '1') {
        throw "Site ${siteId}: nonstandard timing or entry"
    }
    $sceneRef = $templateScene.SceneFile.DepotPath.ToString()
    $marker = $templateScene.SceneLocation.NodeRef.ToString()
    $prefabRef = $marker.Replace('#mirror_sm_','#mirror_')
    $prefab = @($mirror.RootChunk.PhasePrefabs | Where-Object {$_.PrefabNodeRef.ToString() -eq $prefabRef})
    if ($prefab.Count -ne 1) { throw "Site ${siteId}: prefab $prefabRef not unique" }
    $sectorName = $null
    # The audit mapped these single-trigger Quest sectors by exact prefab.
    $blockJson = Join-Path $WorkspaceRoot 'research\phase2b_p4\staging_scan\ep1_1_nightcity\json\base\worlds\03_night_city\_compiled\default\blocks\all.streamingblock.json'
    if ($null -eq $script:block) { $script:block = Get-Content -LiteralPath $blockJson -Raw | ConvertFrom-Json }
    $descriptor = @($script:block.Data.RootChunk.descriptors | Where-Object {$_.questPrefabNodeRef.'$value' -like "*/$prefabRef"})
    if ($descriptor.Count -ne 1) { throw "Site ${siteId}: descriptor not unique" }
    $sectorName = $descriptor[0].data.DepotPath.'$value'
    $sector = Read-Cr2wFile (Join-Path $vanillaRoot $sectorName)
    if ($sector.RootChunk.Nodes.Count -ne 1 -or $sector.RootChunk.Nodes[0].Chunk.GetType().Name -ne 'worldTriggerAreaNode') {
        throw "Site ${siteId}: sector not one vanilla trigger"
    }
    $fullTrigger = $sector.RootChunk.NodeData.Data[0].QuestPrefabRefHash.ToString()
    if (-not $fullTrigger.EndsWith('/'+$entry.TriggerAreaRef.ToString())) { throw "Site ${siteId}: trigger mismatch" }
    $entry.TriggerAreaRef = [WolvenKit.RED4.Types.NodeRef]::op_Implicit($fullTrigger)
    $exitCondition = $entry.DeepCopy(); $exitCondition.Type = [WolvenKit.RED4.Types.Enums+questTriggerConditionType]::IsOutside
    $scene = Read-Cr2wFile (Join-Path $vanillaRoot $sceneRef)
    if ($scene.RootChunk.SceneGraph.Chunk.Graph.Count -ne 37) {
        throw "Site ${siteId}: scene is not the reviewed 37-node ordinary shape"
    }
    if ($RedDirtOnly) {
        if ($siteId -ne 42 -or $sceneRef -ne 'base\open_world\scenes\mirrors\mirror_scene_red_dirt.scene') {
            throw 'Red Dirt C5 source changed'
        }
        $originalSceneJson = Join-Path $WorkspaceRoot 'research\b0_mirror_rollout\vanilla_ordinary\json\base\open_world\scenes\mirrors\mirror_scene_red_dirt.scene.json'
        $originalSceneText = [IO.File]::ReadAllText($originalSceneJson)
        if ($originalSceneText -notmatch '"factName": "sq011_mirror_off "' -or
            $originalSceneText -notmatch '"factName": "mirror_interactions_facials"') {
            throw 'Red Dirt original choice facts changed'
        }
        Export-Cr2wJson -File $scene -Path (Join-Path $val 'red_dirt_original.scene.json')
    }
    $exits = @($scene.RootChunk.SceneGraph.Chunk.Graph | Where-Object {
        if ($_.Chunk.GetType().Name -ne 'scnQuestNode') { return $false }
        $q = $_.Chunk.QuestNode.Chunk
        if ($q.GetType().Name -ne 'questPauseConditionNodeDefinition') { return $false }
        if ($q.Condition.Chunk.GetType().Name -ne 'questTriggerCondition') { return $false }
        return $q.Condition.Chunk.Type.ToString() -eq 'IsOutside' -and
            $q.Condition.Chunk.TriggerAreaRef.ToString() -eq ($fullTrigger.Split('/')[-1])
    })
    if ($exits.Count -ne 1) { throw "Site ${siteId}: scene exit not unique ($($exits.Count))" }
    $exits[0].Chunk.QuestNode.Chunk.Condition.Chunk.TriggerAreaRef = [WolvenKit.RED4.Types.NodeRef]::op_Implicit($fullTrigger)
    $stem = ('m{0:D2}' -f $siteId)
    $prefix = 'PTFRBM'+('00'+$siteId).Substring(('00'+$siteId).Length-2)+'_'
    $gateDepot = "towercontinued\ordinary_mirrors_$version\$stem`_gate.questphase"
    $ownerDepot = "towercontinued\ordinary_mirrors_$version\$stem`_owner.questphase"
    $sceneDepot = "towercontinued\ordinary_mirrors_$version\$stem.scene"
    $gate = [WolvenKit.RED4.Types.questGraphDefinition]::new()
    Put $gate (New-InputNode 0 'In1')
    Put $gate (Pause 1 (Guard $null))
    $child = [WolvenKit.RED4.Types.questPhaseNodeDefinition]::new(); $child.Id = [uint16]2
    $rp = [WolvenKit.RED4.Types.ResourcePath]::op_Implicit($ownerDepot)
    $child.PhaseResource = [Activator]::CreateInstance($child.GetType().GetProperty('PhaseResource').PropertyType,[object[]]@($rp))
    [void](New-QuestSocket $child 'CutDestination' ([WolvenKit.RED4.Types.Enums+questSocketType]::CutDestination))
    [void](New-QuestSocket $child 'In1' ([WolvenKit.RED4.Types.Enums+questSocketType]::Input))
    Put $gate $child
    Link $gate 0 Out 1; Link $gate 1 Out 2 In1
    $gateFile = PhaseFile $gate
    $owner = [WolvenKit.RED4.Types.questGraphDefinition]::new()
    Put $owner (New-InputNode 0 'In1')
    Put $owner (Pause 1 (Guard $entry))
    Put $owner (New-SetFactNode 2 ($prefix+'Active') 1)
    Put $owner (SetCount 3 ($prefix+'Requests'))
    $sceneNode = $templateScene.DeepCopy(); $sceneNode.Id = [uint16]4
    foreach ($socket in $sceneNode.Sockets) { $socket.Chunk.Connections.Clear() }
    $sceneResource = [WolvenKit.RED4.Types.ResourcePath]::op_Implicit($sceneDepot)
    $sceneNode.SceneFile = [Activator]::CreateInstance($sceneNode.GetType().GetProperty('SceneFile').PropertyType,[object[]]@($sceneResource))
    Put $owner $sceneNode
    Put $owner (New-SetFactNode 5 ($prefix+'Active') 0)
    Put $owner (SetCount 6 ($prefix+'Returns'))
    $rearm = $delay.DeepCopy(); $rearm.Id = [uint16]7
    foreach ($socket in $rearm.Sockets) { $socket.Chunk.Connections.Clear() }
    Put $owner $rearm
    Put $owner (New-SetFactNode 8 ($prefix+'Active') 0)
    Put $owner (SetCount 9 ($prefix+'Interrupted'))
    Put $owner (Pause 10 $exitCondition)
    Link $owner 0 Out 1; Link $owner 1 Out 2; Link $owner 2 Out 3
    Link $owner 3 Out 4 mirror_interaction
    Link $owner 4 mirror_interaction_out 5; Link $owner 5 Out 6
    Link $owner 6 Out 7; Link $owner 7 Out 1
    Link $owner 4 'Default INT' 8; Link $owner 8 Out 9
    Link $owner 9 Out 10; Link $owner 10 Out 7
    $ownerFile = PhaseFile $owner
    $ownerFile.RootChunk.PhasePrefabs.Add($prefab[0].DeepCopy())
    Write-Cr2wFile $gateFile (Join-Path $src $gateDepot)
    Write-Cr2wFile $ownerFile (Join-Path $src $ownerDepot)
    Write-Cr2wFile $scene (Join-Path $src $sceneDepot)
    $gateCheck = Read-Cr2wFile (Join-Path $src $gateDepot)
    $ownerCheck = Read-Cr2wFile (Join-Path $src $ownerDepot)
    $sceneCheck = Read-Cr2wFile (Join-Path $src $sceneDepot)
    if ($RedDirtOnly) {
        Export-Cr2wJson -File $gateCheck -Path (Join-Path $val 'gate.json')
        Export-Cr2wJson -File $ownerCheck -Path (Join-Path $val 'owner.json')
        Export-Cr2wJson -File $sceneCheck -Path (Join-Path $val 'red_dirt_candidate.scene.json')
    }
    if ($gateCheck.RootChunk.Graph.Chunk.Nodes.Count -ne 3 -or
        $ownerCheck.RootChunk.Graph.Chunk.Nodes.Count -ne 11 -or
        $ownerCheck.RootChunk.PhasePrefabs.Count -ne 1 -or
        $ownerCheck.RootChunk.PhasePrefabs[0].PrefabNodeRef.ToString() -ne $prefabRef -or
        $sceneCheck.RootChunk.SceneGraph.Chunk.Graph.Count -ne $scene.RootChunk.SceneGraph.Chunk.Graph.Count) {
        throw "Site ${siteId}: round-trip structure mismatch"
    }
    $changedExit = @($sceneCheck.RootChunk.SceneGraph.Chunk.Graph | Where-Object {
        if ($_.Chunk.GetType().Name -ne 'scnQuestNode') { return $false }
        $q = $_.Chunk.QuestNode.Chunk
        if ($q.GetType().Name -ne 'questPauseConditionNodeDefinition') { return $false }
        if ($q.Condition.Chunk.GetType().Name -ne 'questTriggerCondition') { return $false }
        return $q.Condition.Chunk.Type.ToString() -eq 'IsOutside' -and
            $q.Condition.Chunk.TriggerAreaRef.ToString() -eq $fullTrigger
    })
    if ($changedExit.Count -ne 1) { throw "Site ${siteId}: scene exit did not survive round-trip" }
    foreach ($node in $ownerCheck.RootChunk.Graph.Chunk.Nodes) {
        if ($node.Chunk.GetType().Name -eq 'questFactsDBManagerNodeDefinition' -and
            -not $node.Chunk.Type.Chunk.FactName.ToString().StartsWith($prefix)) {
            throw "Site ${siteId}: non-mod fact writer found"
        }
    }
    foreach ($resource in @($gateDepot,$ownerDepot,$sceneDepot)) { $resources.Add($resource) }
    $crc = 65535
    foreach ($byte in [Text.Encoding]::UTF8.GetBytes($gateDepot+':1')) {
        $x = ($crc -shr 8) -bxor $byte; $x = $x -bxor ($x -shr 4)
        $crc = (($crc -shl 8) -bxor ($x -shl 12) -bxor ($x -shl 5) -bxor $x) -band 65535
    }
    if (-not $ids.Add($crc) -or @($parent.RootChunk.Graph.Chunk.Nodes | Where-Object {$_.Chunk.Id.ToString() -eq "$crc"}).Count) {
        throw "Site ${siteId}: ArchiveXL ID collision $crc"
    }
    $xlLines.Add("    - path: $gateDepot")
    $xlLines.Add('      parent: ep1\quest\ep1.quest')
    $xlLines.Add('      input:')
    $xlLines.Add('        node: [1]')
    $xlLines.Add('        socket: Out')
    $records.Add([pscustomobject]@{id=$siteId; prefab=$prefabRef; trigger=$fullTrigger; scene=$sceneRef;
        sector=$sectorName; registration_id=$crc; scene_nodes=$scene.RootChunk.SceneGraph.Chunk.Graph.Count})
}
$expected = @($resources | Sort-Object)
$actual = @(Get-ChildItem -LiteralPath $src -Recurse -File | ForEach-Object {[IO.Path]::GetRelativePath($src,$_.FullName)} | Sort-Object)
if (@(Compare-Object $expected $actual).Count) { throw 'Unexpected source resource manifest' }
$xlPath = Join-Path $WorkspaceRoot ("archive\b0_ordinary_mirrors_$version\"+$archiveName+'.xl')
[IO.File]::WriteAllLines($xlPath,$xlLines,[Text.UTF8Encoding]::new($false))
$hashService = [WolvenKit.Common.Services.HashService]::new(); $hashService.Load()
$archivePath = Join-Path $out $archiveName
$stream = [IO.File]::Create($archivePath)
try {
    $writer = [WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hashService,[WolvenKit.SerilogWrapper]::new())
    if (-not $writer.WriteArchive([IO.DirectoryInfo]::new($src),$stream)) { throw 'Archive write failed' }
} finally { $stream.Dispose() }
$reader = [WolvenKit.RED4.Archive.IO.ArchiveReader]::new(); $archive = $null
if ($reader.ReadArchive($archivePath,$hashService,[ref]$archive).ToString() -ne 'NoError') { throw 'Archive reopen failed' }
$packed = @($archive.Files.Values | ForEach-Object {$_.Name} | Sort-Object)
if (@(Compare-Object $expected $packed).Count) { throw 'Archive manifest mismatch' }
Copy-Item -LiteralPath $xlPath -Destination (Join-Path $out ($archiveName+'.xl'))
$manifest = [ordered]@{status='WORKSPACE_ONLY_UNINSTALLED'; archive=$archiveName;
    sha256=(Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash;
    automatic=[bool]$Automatic; opt_in_fact=$(if ($RedDirtOnly) {'PTFRBM42_Enabled'} elseif ($Automatic) {$null} else {'PTFRBM_Enabled'});
    sites=@($records); excluded=$excluded;
    resources=$packed; vanilla_replacements=@(); runtime_writes='PTFRBM_* facts only'}
[IO.File]::WriteAllText((Join-Path $val 'build_manifest.json'),($manifest | ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
$manifest | ConvertTo-Json -Depth 4
