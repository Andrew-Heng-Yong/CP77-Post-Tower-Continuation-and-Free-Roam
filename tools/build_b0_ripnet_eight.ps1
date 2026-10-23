param(
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$WolvenKitRoot = 'C:\Users\Ayong\Documents\WolvenKit-8.20.0'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -WolvenKitRoot $WolvenKitRoot -HelpersOnly

# This is an opt-in eight-site development cohort, not all ripperdocs/netrunners.
# The exclusions and their reasons are documented in the assessment.
$specs = @(
    [pscustomobject]@{Name='rip_dtn'; Id='cct_dtn_ripdoc_01'; Outer=8; Phase=8; Distance=12; Radius=50; Close=3; CloseRadius=12; Far=7; Socket='cct_dtn_ripdoc_01_start'; Gate='cct_dtn_ripdoc_01_default_on'; Prefix='PTFRB0RIPDTN_'; X=-2412.15503; Y=395.014343; Z=11.6871052},
    [pscustomobject]@{Name='net_rey'; Id='hey_rey_netrunner_01'; Outer=7; Phase=11; Distance=16; Radius=50; Close=4; CloseRadius=12; Far=10; Socket='hey_rey_netrunner_01_start'; Gate='hey_rey_netrunner_01_default_on'; Prefix='PTFRB0NETREY_'; X=-854.184631; Y=-387.527466; Z=8.53456116},
    [pscustomobject]@{Name='net_cvi'; Id='pac_cvi_techstore_01'; Outer=5; Phase=9; Distance=14; Radius=50; Close=4; CloseRadius=12; Far=9; Socket='Start 0'; Gate='pac_cvi_techstore_01'; Prefix='PTFRB0NETCVI_'; X=-1908.16333; Y=-1924.15247; Z=49.3091621},
    [pscustomobject]@{Name='rip_wwd'; Id='pac_wwd_ripdoc_01'; Outer=4; Phase=11; Distance=17; Radius=50; Close=4; CloseRadius=12; Far=7; Socket='Start 0'; Gate='pac_wwd_ripdoc_01_default_on'; Prefix='PTFRB0RIPWWD_'; X=-2606.36035; Y=-2501.31787; Z=17.8600025},
    [pscustomobject]@{Name='rip_arr'; Id='std_arr_ripperdoc_01'; Outer=11; Phase=10; Distance=15; Radius=49; Close=2; CloseRadius=6; Far=11; Socket='std_arr_ripperdoc_01'; Gate='std_arr_ripperdoc_01_default_on'; Prefix='PTFRB0RIPARR_'; X=-1066.00159; Y=-1270.50366; Z=11.456399},
    [pscustomobject]@{Name='rip_rcr'; Id='#std_rcr_ripperdoc_01'; Outer=10; Phase=11; Distance=15; Radius=50; Close=3; CloseRadius=12; Far=12; Socket='std_rcr_ripperdoc_01'; Gate='std_rcr_ripperdoc_01_default_on'; Prefix='PTFRB0RIPRCR_'; X=585.669678; Y=-2180.27417; Z=42.3900032},
    [pscustomobject]@{Name='rip_hil'; Id='wbr_hil_ripdoc_01'; Outer=6; Phase=8; Distance=12; Radius=50; Close=3; CloseRadius=12; Far=10; Socket='wbr_hil_ripdoc_01_start'; Gate='wbr_hil_ripdoc_01_default_on'; Prefix='PTFRB0RIPHIL_'; X=-41.7054405; Y=-53.5234756; Z=7.18342638},
    [pscustomobject]@{Name='rip_jpn'; Id='wbr_jpn_ripdoc_01'; Outer=16; Phase=8; Distance=12; Radius=50; Close=9; CloseRadius=12; Far=22; Socket='wbr_jpn_ripdoc_01_start'; Gate='wbr_jpn_ripdoc_01_default_on'; Prefix='PTFRB0RIPJPN_'; X=-707.342529; Y=868.738647; Z=11.8164492}
)
$inventory = Get-Content -LiteralPath (Join-Path $WorkspaceRoot 'research\b0_vendor_rollout\regional_vendor_inventory.json') -Raw | ConvertFrom-Json
$audit = Get-Content -LiteralPath (Join-Path $WorkspaceRoot 'research\b0_vendor_rollout\vendor_template_audit.json') -Raw | ConvertFrom-Json
$basePath = Join-Path $WorkspaceRoot 'research\q307_extracted\raw\base\quest\cyberpunk2077.questphase'
$inputs = [System.Collections.Generic.List[string]]::new(); $inputs.Add($basePath)
$resolved = @()
foreach ($spec in $specs) {
    $matches = @($inventory | Where-Object { @($_.spawn_activate).Count -eq 1 -and $_.spawn_activate[0].entry -eq $spec.Id })
    if ($matches.Count -ne 1) { throw "Expected one regional owner: $($spec.Id)" }
    $row=$matches[0]
    $shape=@($audit | Where-Object { $_.scene -eq $row.scene })
    if ($shape.Count -ne 1 -or -not $shape[0].structural_candidate -or
        $row.graph -ne ('root/node'+$spec.Outer+'/node'+$spec.Phase) -or
        $row.spawn_deactivate[0].entry -ne $spec.Id) { throw "Source shape changed: $($spec.Name)" }
    $vendorPath=Join-Path $WorkspaceRoot ('research\b0_vendor_rollout\regional_sources\raw\'+$row.source)
    $scenePath=Join-Path $WorkspaceRoot ('research\b0_vendor_rollout\regional_scene_sources\raw\'+$row.scene)
    foreach ($path in @($vendorPath,$scenePath)) {
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Missing source: $path" }
        if (-not $inputs.Contains($path)) { $inputs.Add($path) }
    }
    $resolved += [pscustomobject]@{Spec=$spec;Row=$row;VendorPath=$vendorPath;ScenePath=$scenePath}
}
$inputHashes=@{}; foreach ($path in $inputs) { $inputHashes[$path]=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash }
$source=Join-Path $WorkspaceRoot 'archive\b0_ripnet_eight\source'
$output=Join-Path $WorkspaceRoot 'build\B0_RipNetEight'
$validation=Join-Path $WorkspaceRoot 'research\b0_ripnet_eight\validation'
New-Item -ItemType Directory -Force -Path $source,$output,$validation | Out-Null
$base=Read-Cr2wFile $basePath
$packedPaths=[System.Collections.Generic.List[string]]::new()
$guardRecords=[ordered]@{}
$siteRecords=[System.Collections.Generic.List[object]]::new()
foreach ($entry in $resolved) {
    $spec=$entry.Spec; $row=$entry.Row
    $vendor=Read-Cr2wFile $entry.VendorPath
    $branch=(Get-QuestNode $vendor.RootChunk.Graph.Chunk $spec.Outer).PhaseGraph.Chunk
    $phaseTemplate=Get-QuestNode $branch $spec.Phase
    $distanceTemplate=Get-QuestNode $branch $spec.Distance
    $inner=$phaseTemplate.PhaseGraph.Chunk
    $scene=Get-QuestNode $inner $row.scene_node
    $spawn=Get-QuestNode $inner $row.spawn_activate[0].node
    $despawn=Get-QuestNode $inner $row.spawn_deactivate[0].node
    $close=Get-QuestNode $inner $spec.Close
    $far=Get-QuestNode $inner $spec.Far
    $inputsInner=@($inner.Nodes | Where-Object {$_.Chunk.GetType().Name -eq 'questInputNodeDefinition'})
    $outputsInner=@($inner.Nodes | Where-Object {$_.Chunk.GetType().Name -eq 'questOutputNodeDefinition'})
    if ($branch.Nodes.Count -ne 7 -or $inner.Nodes.Count -ne 7 -or
        $inputsInner.Count -ne 1 -or $outputsInner.Count -ne 1 -or
        $phaseTemplate.GetType().Name -ne 'questPhaseNodeDefinition' -or
        $distanceTemplate.Condition.Chunk.Type.Chunk.ComparisonType.ToString() -ne 'Less' -or
        $distanceTemplate.Condition.Chunk.Type.Chunk.DistanceDefinition2.Chunk.DistanceValue.ToString() -ne [string]$spec.Radius -or
        $close.Condition.Chunk.Type.Chunk.ComparisonType.ToString() -ne 'Less' -or
        $close.Condition.Chunk.Type.Chunk.DistanceDefinition2.Chunk.DistanceValue.ToString() -ne [string]$spec.CloseRadius -or
        $far.Condition.Chunk.Type.Chunk.ComparisonType.ToString() -ne 'Greater' -or
        $far.Condition.Chunk.Type.Chunk.DistanceDefinition2.Chunk.DistanceValue.ToString() -ne '50' -or
        $spawn.Actions.Count -ne 1 -or $despawn.Actions.Count -ne 1 -or
        $spawn.Actions[0].Type.Chunk.Action.ToString() -ne 'Activate' -or
        $despawn.Actions[0].Type.Chunk.Action.ToString() -ne 'Deactivate' -or
        $spawn.Actions[0].Type.Chunk.Reference.ToString() -ne $row.spawn_activate[0].reference -or
        $despawn.Actions[0].Type.Chunk.Reference.ToString() -ne $row.spawn_deactivate[0].reference -or
        $spawn.Actions[0].Type.Chunk.EntryName.ToString() -ne $spec.Id -or
        $despawn.Actions[0].Type.Chunk.EntryName.ToString() -ne $spec.Id -or
        $spawn.Actions[0].Type.Chunk.PhaseName.ToString() -ne $row.spawn_activate[0].phase -or
        $despawn.Actions[0].Type.Chunk.PhaseName.ToString() -ne $row.spawn_deactivate[0].phase -or
        $scene.SceneFile.DepotPath.ToString() -ne $row.scene -or
        $scene.SceneLocation.NodeRef.ToString() -ne $row.scene_location) {
        throw "Native actor/scene/distance leaf changed: $($spec.Name)"
    }
    [void](Get-QuestSocket $scene $spec.Socket)
    $guards=[ordered]@{
        PostTowerFreeRoamActive=1;PTFRP0_DR13=1;q307_active=0;q307_done=1
        q307_finished=1;q307_2079=1;q307_main_game_killed=1
        q305_johnny_scene_active=0;q115_point_of_no_return=0;q000_done=1
    }
    $guards[$spec.Gate]=1; $guards[$spec.Prefix+'Enabled']=1
    $guardRecords[$spec.Name]=$guards
    $condition=[WolvenKit.RED4.Types.questLogicalCondition]::new()
    $condition.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
    foreach ($fact in $guards.Keys) {
        Add-RedHandle $condition.Conditions (New-FactCondition $fact $guards[$fact] ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
    }
    $graph=[WolvenKit.RED4.Types.questGraphDefinition]::new()
    function Put($node) { Add-RedHandle $graph.Nodes $node }
    function Link($from,$socket,$to,$dest='In') {
        [void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $graph $from) $socket) (Get-QuestSocket (Get-QuestNode $graph $to) $dest))
    }
    Put (New-InputNode 0 'In1')
    Put (New-SetFactNode 1 ($spec.Prefix+'Ready') 1)
    $guard=(Get-QuestNode $base.RootChunk.Graph.Chunk 106).DeepCopy();$guard.Id=[uint16]2
    foreach ($socket in $guard.Sockets) { $socket.Chunk.Connections.Clear() }
    Set-RedHandleProperty $guard Condition $condition
    Put $guard
    $distance=$distanceTemplate.DeepCopy();$distance.Id=[uint16]3
    foreach ($socket in $distance.Sockets) { $socket.Chunk.Connections.Clear() }
    Put $distance
    Put (New-SetFactNode 4 ($spec.Prefix+'Near') 1)
    $phase=$phaseTemplate.DeepCopy();$phase.Id=[uint16]5
    foreach ($socket in $phase.Sockets) { $socket.Chunk.Connections.Clear() }
    $innerCopy=$phase.PhaseGraph.Chunk
    foreach ($nodeHandle in $innerCopy.Nodes) {
        foreach ($socket in $nodeHandle.Chunk.Sockets) { $socket.Chunk.Connections.Clear() }
    }
    foreach ($marker in @(
        [pscustomobject]@{Id=100;Suffix='SpawnActionOut'},
        [pscustomobject]@{Id=101;Suffix='ActorDistanceGate'},
        [pscustomobject]@{Id=102;Suffix='ExitWatchArmed'},
        [pscustomobject]@{Id=103;Suffix='DespawnActionOut'})) {
        Add-RedHandle $innerCopy.Nodes (New-SetFactNode $marker.Id ($spec.Prefix+$marker.Suffix) 1)
    }
    Set-RedHandleProperty (Get-QuestNode $innerCopy $spec.Far) Condition (New-FactCondition ($spec.Prefix+'Far') 1 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
    function LinkInner($from,$socket,$to,$dest='In') {
        [void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $innerCopy $from) $socket) (Get-QuestSocket (Get-QuestNode $innerCopy $to) $dest))
    }
    $inputId=[int]$inputsInner[0].Chunk.Id.ToString(); $outputId=[int]$outputsInner[0].Chunk.Id.ToString()
    LinkInner $inputId Out $row.spawn_activate[0].node
    LinkInner $inputId Out 102; LinkInner 102 Out $spec.Far
    LinkInner $row.spawn_activate[0].node Out 100; LinkInner 100 Out $spec.Close
    LinkInner $spec.Close Out 101; LinkInner 101 Out $row.scene_node $spec.Socket
    LinkInner $spec.Far Out $row.spawn_deactivate[0].node
    LinkInner $row.spawn_deactivate[0].node Out 103; LinkInner 103 Out $outputId
    Put $phase
    Put (New-SetFactNode 6 ($spec.Prefix+'Departed') 1)
    Put (New-SetFactNode 7 ($spec.Prefix+'Near') 0)
    $rearm=(Get-QuestNode $base.RootChunk.Graph.Chunk 106).DeepCopy();$rearm.Id=[uint16]8
    foreach ($socket in $rearm.Sockets) { $socket.Chunk.Connections.Clear() }
    Set-RedHandleProperty $rearm Condition (New-FactCondition ($spec.Prefix+'Far') 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
    Put $rearm
    Link 0 Out 1;Link 1 Out 2;Link 2 Out 3;Link 3 Out 4;Link 4 Out 5 In1
    Link 5 Out1 6;Link 6 Out 7;Link 7 Out 8;Link 8 Out 2
    $root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new()
    $root.CookingPlatform=[WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC
    Set-RedHandleProperty $root Graph $graph
    $resource=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$resource.RootChunk=$root
    $depot='towercontinued\b0_ripnet_eight\'+$spec.Name+'_owner.questphase'
    Write-Cr2wFile $resource (Join-Path $source $depot)
    Export-Cr2wJson (Read-Cr2wFile (Join-Path $source $depot)) (Join-Path $validation ($spec.Name+'_owner.questphase.json'))
    $packedPaths.Add($depot)
    $siteRecords.Add([ordered]@{name=$spec.Name;id=$spec.Id;scene=$row.scene;marker=$row.scene_location;gate=$spec.Gate
        prefix=$spec.Prefix;x=$spec.X;y=$spec.Y;z=$spec.Z;outer_radius=$spec.Radius;close_radius=$spec.CloseRadius
        scene_socket=$spec.Socket;spawn=$row.spawn_activate[0];despawn=$row.spawn_deactivate[0]})
}
foreach ($path in $inputs) {
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $inputHashes[$path]) { throw "Reviewed input changed: $path" }
}
$actual=@(Get-ChildItem -LiteralPath $source -File -Recurse | ForEach-Object {[IO.Path]::GetRelativePath($source,$_.FullName)})
if (@(Compare-Object ($actual | Sort-Object) ($packedPaths | Sort-Object)).Count) { throw 'Unexpected eight-site source manifest' }
$hashService=[WolvenKit.Common.Services.HashService]::new();$hashService.Load()
$archivePath=Join-Path $output 'TowerContinued_B0_RipNetEight.archive'
$stream=[IO.File]::Create($archivePath)
try {
    $writer=[WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hashService,[WolvenKit.SerilogWrapper]::new())
    if (-not $writer.WriteArchive([IO.DirectoryInfo]::new($source),$stream)) { throw 'Archive write failed' }
} finally { $stream.Dispose() }
$reader=[WolvenKit.RED4.Archive.IO.ArchiveReader]::new();$archive=$null
if ($reader.ReadArchive($archivePath,$hashService,[ref]$archive).ToString() -ne 'NoError') { throw 'Archive did not reopen' }
$packed=@($archive.Files.Values | ForEach-Object {$_.Name})
if (@(Compare-Object ($packed | Sort-Object) ($packedPaths | Sort-Object)).Count) { throw 'Archive manifest mismatch' }
foreach ($item in $archive.Files.Values) {
    $memory=[IO.MemoryStream]::new()
    try {
        $item.Extract($memory)
        if ([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($memory.ToArray())) -ne
            (Get-FileHash -LiteralPath (Join-Path $source $item.Name) -Algorithm SHA256).Hash) { throw "Packed bytes differ: $($item.Name)" }
    } finally { $memory.Dispose() }
}
$manifest=[ordered]@{
    status='STATIC_EXPERIMENTAL_NOT_INSTALLED';archive='TowerContinued_B0_RipNetEight.archive'
    sha256=(Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash
    resources=$packed;source_hashes=$inputHashes;sites=@($siteRecords);guard_facts=$guardRecords
    vanilla_replacements=@();enable_facts=@($specs | ForEach-Object {$_.Prefix+'Enabled'})
    exclusions=@('Special/outcome-sensitive ripperdocs and netrunners','wat_kab_ripperdoc_03','wbr_jpn_netrun_01 unresolved marker')
    known_limits=@('Opt-in eight-site cohort only','Far exit uses a development position flag','No profile-safety or save/reload claim','Live baseline required per site')
}
[IO.File]::WriteAllText((Join-Path $validation 'build_manifest.json'),($manifest | ConvertTo-Json -Depth 12),[Text.UTF8Encoding]::new($false))
$manifest | ConvertTo-Json -Depth 12
