param(
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$WolvenKitRoot = 'C:\Users\Ayong\Documents\WolvenKit-8.20.0'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -WolvenKitRoot $WolvenKitRoot -HelpersOnly
$vendorDepot='base\open_world\vendors\westbrook\japantown\japantown_vendors.questphase'
$sceneDepot='base\open_world\vendors\westbrook\japantown\wbr_jpn_netrun_01\wbr_jpn_netrun_01.scene'
$vendorPath=Join-Path $WorkspaceRoot ('research\b0_vendor_rollout\regional_sources\raw\'+$vendorDepot)
$scenePath=Join-Path $WorkspaceRoot ('research\b0_vendor_rollout\regional_scene_sources\raw\'+$sceneDepot)
$basePath=Join-Path $WorkspaceRoot 'research\q307_extracted\raw\base\quest\cyberpunk2077.questphase'
$inputs=@($vendorPath,$scenePath,$basePath)
$hashes=@{};foreach($path in $inputs){if(-not(Test-Path -LiteralPath $path -PathType Leaf)){throw "Missing input: $path"};$hashes[$path]=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash}
$source=Join-Path $WorkspaceRoot 'archive\b0_jpn_netrunner01\source'
$output=Join-Path $WorkspaceRoot 'build\B0_JpnNetrunner01'
$validation=Join-Path $WorkspaceRoot 'research\b0_jpn_netrunner01\validation'
New-Item -ItemType Directory -Force -Path $source,$output,$validation | Out-Null
$vendor=Read-Cr2wFile $vendorPath;$base=Read-Cr2wFile $basePath
$branch=(Get-QuestNode $vendor.RootChunk.Graph.Chunk 15).PhaseGraph.Chunk
$phaseTemplate=Get-QuestNode $branch 8
$distanceTemplate=Get-QuestNode $branch 12
$inner=$phaseTemplate.PhaseGraph.Chunk
$spawn=Get-QuestNode $inner 19;$despawn=Get-QuestNode $inner 20
$scene=Get-QuestNode $inner 18;$close=Get-QuestNode $inner 9;$far=Get-QuestNode $inner 21
if($branch.Nodes.Count -ne 7 -or $inner.Nodes.Count -ne 7 -or
   $distanceTemplate.Condition.Chunk.Type.Chunk.ComparisonType.ToString() -ne 'Less' -or
   $distanceTemplate.Condition.Chunk.Type.Chunk.DistanceDefinition2.Chunk.DistanceValue.ToString() -ne '50' -or
   $close.Condition.Chunk.Type.Chunk.ComparisonType.ToString() -ne 'Less' -or
   $close.Condition.Chunk.Type.Chunk.DistanceDefinition2.Chunk.DistanceValue.ToString() -ne '12' -or
   $far.Condition.Chunk.Type.Chunk.ComparisonType.ToString() -ne 'Greater' -or
   $far.Condition.Chunk.Type.Chunk.DistanceDefinition2.Chunk.DistanceValue.ToString() -ne '50' -or
   $scene.SceneFile.DepotPath.ToString() -ne $sceneDepot -or
   $scene.SceneLocation.NodeRef.ToString() -ne '#wbr_sm_jpn_netrun_01' -or
   $spawn.Actions.Count -ne 1 -or $despawn.Actions.Count -ne 1 -or
   $spawn.Actions[0].Type.Chunk.Action.ToString() -ne 'Activate' -or
   $despawn.Actions[0].Type.Chunk.Action.ToString() -ne 'Deactivate' -or
   $spawn.Actions[0].Type.Chunk.Reference.ToString() -ne '#wbr_jpn_netrun_01' -or
   $despawn.Actions[0].Type.Chunk.Reference.ToString() -ne '#wbr_jpn_netrun_01' -or
   $spawn.Actions[0].Type.Chunk.EntryName.ToString() -ne 'wbr_jpn_netrun_01' -or
   $despawn.Actions[0].Type.Chunk.EntryName.ToString() -ne 'wbr_jpn_netrun_01' -or
   $spawn.Actions[0].Type.Chunk.PhaseName.ToString() -ne 'None' -or
   $despawn.Actions[0].Type.Chunk.PhaseName.ToString() -ne 'None'){
   throw 'Japantown netrunner 01 vanilla owner changed'
}
[void](Get-QuestSocket $scene 'wbr_jpn_netrun_01_start')
$prefix='PTFRB0JPNNET1_'
$guards=[ordered]@{
    PostTowerFreeRoamActive=1;PTFRP0_DR13=1;q307_active=0;q307_done=1
    q307_finished=1;q307_2079=1;q307_main_game_killed=1
    q305_johnny_scene_active=0;q115_point_of_no_return=0;q000_done=1
    wbr_jpn_netrun_01_default_on=1;PTFRB0JPNNET1_Enabled=1
}
$condition=[WolvenKit.RED4.Types.questLogicalCondition]::new()
$condition.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
foreach($fact in $guards.Keys){Add-RedHandle $condition.Conditions (New-FactCondition $fact $guards[$fact] ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))}
$graph=[WolvenKit.RED4.Types.questGraphDefinition]::new()
function Put($node){Add-RedHandle $graph.Nodes $node}
function Link($from,$socket,$to,$dest='In'){
    [void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $graph $from) $socket) (Get-QuestSocket (Get-QuestNode $graph $to) $dest))
}
Put (New-InputNode 0 'In1')
Put (New-SetFactNode 1 ($prefix+'Ready') 1)
$guard=(Get-QuestNode $base.RootChunk.Graph.Chunk 106).DeepCopy();$guard.Id=[uint16]2
foreach($socket in $guard.Sockets){$socket.Chunk.Connections.Clear()}
Set-RedHandleProperty $guard Condition $condition;Put $guard
$distance=$distanceTemplate.DeepCopy();$distance.Id=[uint16]3
foreach($socket in $distance.Sockets){$socket.Chunk.Connections.Clear()};Put $distance
Put (New-SetFactNode 4 ($prefix+'Near') 1)
$phase=$phaseTemplate.DeepCopy();$phase.Id=[uint16]5
foreach($socket in $phase.Sockets){$socket.Chunk.Connections.Clear()}
$innerCopy=$phase.PhaseGraph.Chunk
foreach($nodeHandle in $innerCopy.Nodes){foreach($socket in $nodeHandle.Chunk.Sockets){$socket.Chunk.Connections.Clear()}}
foreach($marker in @(
    [pscustomobject]@{Id=100;Suffix='SpawnActionOut'},
    [pscustomobject]@{Id=101;Suffix='ActorDistanceGate'},
    [pscustomobject]@{Id=102;Suffix='ExitWatchArmed'},
    [pscustomobject]@{Id=103;Suffix='DespawnActionOut'})){
    Add-RedHandle $innerCopy.Nodes (New-SetFactNode $marker.Id ($prefix+$marker.Suffix) 1)
}
Set-RedHandleProperty (Get-QuestNode $innerCopy 21) Condition (New-FactCondition ($prefix+'Far') 1 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
function LinkInner($from,$socket,$to,$dest='In'){
    [void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $innerCopy $from) $socket) (Get-QuestSocket (Get-QuestNode $innerCopy $to) $dest))
}
LinkInner 5 Out 19;LinkInner 5 Out 102;LinkInner 102 Out 21
LinkInner 19 Out 100;LinkInner 100 Out 9;LinkInner 9 Out 101
LinkInner 101 Out 18 'wbr_jpn_netrun_01_start'
LinkInner 21 Out 20;LinkInner 20 Out 103;LinkInner 103 Out 6
Put $phase
Put (New-SetFactNode 6 ($prefix+'Departed') 1)
Put (New-SetFactNode 7 ($prefix+'Near') 0)
$rearm=(Get-QuestNode $base.RootChunk.Graph.Chunk 106).DeepCopy();$rearm.Id=[uint16]8
foreach($socket in $rearm.Sockets){$socket.Chunk.Connections.Clear()}
Set-RedHandleProperty $rearm Condition (New-FactCondition ($prefix+'Far') 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
Put $rearm
Link 0 Out 1;Link 1 Out 2;Link 2 Out 3;Link 3 Out 4;Link 4 Out 5 In1
Link 5 Out1 6;Link 6 Out 7;Link 7 Out 8;Link 8 Out 2
$root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new()
$root.CookingPlatform=[WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC
Set-RedHandleProperty $root Graph $graph
$resource=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$resource.RootChunk=$root
$depot='towercontinued\b0_jpn_netrunner01\owner.questphase'
Write-Cr2wFile $resource (Join-Path $source $depot)
Export-Cr2wJson (Read-Cr2wFile (Join-Path $source $depot)) (Join-Path $validation 'owner.questphase.json')
foreach($path in $inputs){if((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $hashes[$path]){throw "Reviewed input changed: $path"}}
$actual=@(Get-ChildItem -LiteralPath $source -File -Recurse | ForEach-Object {[IO.Path]::GetRelativePath($source,$_.FullName)})
if($actual.Count -ne 1 -or $actual[0] -ne $depot){throw 'Unexpected source manifest'}
$hashService=[WolvenKit.Common.Services.HashService]::new();$hashService.Load()
$archivePath=Join-Path $output 'TowerContinued_B0_JpnNetrunner01.archive'
$stream=[IO.File]::Create($archivePath)
try{$writer=[WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hashService,[WolvenKit.SerilogWrapper]::new());if(-not $writer.WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Archive write failed'}}finally{$stream.Dispose()}
$reader=[WolvenKit.RED4.Archive.IO.ArchiveReader]::new();$archive=$null
if($reader.ReadArchive($archivePath,$hashService,[ref]$archive).ToString() -ne 'NoError'){throw 'Archive did not reopen'}
$packed=@($archive.Files.Values | ForEach-Object {$_.Name})
if($packed.Count -ne 1 -or $packed[0] -ne $depot){throw 'Archive manifest mismatch'}
$memory=[IO.MemoryStream]::new();try{$archive.Files.Values[0].Extract($memory);if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($memory.ToArray())) -ne (Get-FileHash -LiteralPath (Join-Path $source $depot) -Algorithm SHA256).Hash){throw 'Packed bytes differ'}}finally{$memory.Dispose()}
$manifest=[ordered]@{
    status='STATIC_EXPERIMENTAL_NOT_INSTALLED';archive='TowerContinued_B0_JpnNetrunner01.archive'
    sha256=(Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash
    resources=$packed;source_hashes=$hashes;guard_facts=$guards
    scene=$sceneDepot;scene_marker='#wbr_sm_jpn_netrun_01';marker_position=@(-354.645905,1366.60144,42.1621017)
    vanilla_replacements=@();enable_fact=$prefix+'Enabled'
    known_limits=@('One Japantown netrunner actor and scene only','Far exit uses development position flag','No baseline or live service test','No save/reload claim')
}
[IO.File]::WriteAllText((Join-Path $validation 'build_manifest.json'),($manifest | ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
$manifest | ConvertTo-Json -Depth 10
