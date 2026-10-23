param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),[string]$WolvenKitRoot='C:\Users\Ayong\Documents\WolvenKit-8.20.0',[ValidateSet('Variants','OrdinaryBars','CPZFood02')][string]$CohortKind='Variants')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -WolvenKitRoot $WolvenKitRoot -HelpersOnly
$scope=if($CohortKind -eq 'OrdinaryBars'){'b0_ordinary_bars'}else{'b0_vendor_variants'}
$package=if($CohortKind -eq 'OrdinaryBars'){'B0_OrdinaryBars'}else{'B0_VendorVariants'}
$modeFact=if($CohortKind -eq 'OrdinaryBars'){'PTFRB0BAR_Mode'}else{'PTFRB0VV_Mode'}
$count=if($CohortKind -eq 'OrdinaryBars'){4}else{6}
if($CohortKind -eq 'CPZFood02'){$scope='b0_cpz_food02';$package='B0_CPZFood02';$modeFact='PTFRB0CPZF2_Mode';$count=1}
$cohortPath=Join-Path $WorkspaceRoot "research\$scope\cohort.json"
$cohort=Get-Content -LiteralPath $cohortPath -Raw | ConvertFrom-Json
if($cohort.sites.Count -ne $count){throw 'Unexpected cohort'}
$source=Join-Path $WorkspaceRoot "archive\$scope\source"
$output=Join-Path $WorkspaceRoot "build\$package"
$validation=Join-Path $WorkspaceRoot "research\$scope\validation"
New-Item -ItemType Directory -Force -Path $source,$output,$validation | Out-Null
$base=Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\q307_extracted\raw\base\quest\cyberpunk2077.questphase')
$packedPaths=[Collections.Generic.List[string]]::new()
$common=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;q307_active=0;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q305_johnny_scene_active=0;q115_point_of_no_return=0;q000_done=1}
$common[$modeFact]=1
function Pause($id,$condition){
    $n=(Get-QuestNode $base.RootChunk.Graph.Chunk 106).DeepCopy();$n.Id=[uint16]$id
    foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()}
    Set-RedHandleProperty $n Condition $condition
    return $n
}
function Increment($id,$fact){$n=New-SetFactNode $id $fact 1;$n.Type.Chunk.SetExactValue=$false;return $n}
foreach($spec in $cohort.sites){
    $vp=Join-Path $WorkspaceRoot ('research\b0_vendor_rollout\regional_sources\raw\'+$spec.source)
    $sp=Join-Path $WorkspaceRoot ('research\b0_vendor_rollout\'+$spec.scene_group+'\raw\'+$spec.scene)
    if((Get-FileHash -LiteralPath $vp).Hash -ne $spec.source_sha256 -or (Get-FileHash -LiteralPath $sp).Hash -ne $spec.scene_sha256){throw "Audited source changed: $($spec.id)"}
    $vendor=Read-Cr2wFile $vp
    $branch=(Get-QuestNode $vendor.RootChunk.Graph.Chunk $spec.outer).PhaseGraph.Chunk
    $phaseTemplate=Get-QuestNode $branch $spec.phase
    $inner=$phaseTemplate.PhaseGraph.Chunk
    if($inner.Nodes.Count -ne 7){throw 'Unexpected shape'}
    $originalScene=Get-QuestNode $inner $spec.scene_node
    if($originalScene.SceneFile.DepotPath.ToString() -ne $spec.scene -or $originalScene.SceneLocation.NodeRef.ToString() -ne $spec.scene_marker){throw 'Scene identity changed'}
    [void](Get-QuestSocket $originalScene $spec.scene_socket)
    $prefix=$spec.prefix
    $guard=[WolvenKit.RED4.Types.questLogicalCondition]::new();$guard.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
    foreach($fact in $common.Keys){Add-RedHandle $guard.Conditions (New-FactCondition $fact $common[$fact] ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))}
    Add-RedHandle $guard.Conditions (New-FactCondition ($prefix+'Enabled') 1 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
    Add-RedHandle $guard.Conditions (New-FactCondition $spec.gate 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Greater))
    $graph=[WolvenKit.RED4.Types.questGraphDefinition]::new()
    function Put($n){Add-RedHandle $graph.Nodes $n}
    function Link($a,$out,$b,$in='In'){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $graph $a) $out) (Get-QuestSocket (Get-QuestNode $graph $b) $in))}
    Put (New-InputNode 0 'In1');Put (New-SetFactNode 1 ($prefix+'Ready') 1)
    Put (Pause 2 $guard)
    $distance=(Get-QuestNode $branch $spec.outer_distance.node).DeepCopy();$distance.Id=[uint16]3
    foreach($s in $distance.Sockets){$s.Chunk.Connections.Clear()};Put $distance
    Put (New-SetFactNode 4 ($prefix+'Near') 1)
    $phase=$phaseTemplate.DeepCopy();$phase.Id=[uint16]5
    foreach($s in $phase.Sockets){$s.Chunk.Connections.Clear()}
    $innerCopy=$phase.PhaseGraph.Chunk
    if($CohortKind -eq 'CPZFood02'){
        # The compiled scene marker has a _duplicate suffix absent from the
        # original leaf's short reference. Correct only our copied scene node.
        (Get-QuestNode $innerCopy $spec.scene_node).SceneLocation.NodeRef=[WolvenKit.RED4.Types.NodeRef]$spec.resolved_scene_marker
    }
    foreach($n in $innerCopy.Nodes){foreach($s in $n.Chunk.Sockets){$s.Chunk.Connections.Clear()}}
    foreach($mark in @(@(100,'SpawnActionOut'),@(101,'ActorDistanceGate'),@(102,'ExitWatchArmed'),@(103,'DespawnActionOut'))){Add-RedHandle $innerCopy.Nodes (New-SetFactNode $mark[0] ($prefix+$mark[1]) 1)}
    Set-RedHandleProperty (Get-QuestNode $innerCopy $spec.far.node) Condition (New-FactCondition ($prefix+'Far') 1 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
    function InnerLink($a,$out,$b,$in='In'){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $innerCopy $a) $out) (Get-QuestSocket (Get-QuestNode $innerCopy $b) $in))}
    InnerLink $spec.input Out $spec.spawn.node;InnerLink $spec.input Out 102;InnerLink 102 Out $spec.far.node
    InnerLink $spec.spawn.node Out 100;InnerLink 100 Out $spec.close.node;InnerLink $spec.close.node Out 101
    InnerLink 101 Out $spec.scene_node $spec.scene_socket
    InnerLink $spec.far.node Out $spec.despawn.node;InnerLink $spec.despawn.node Out 103;InnerLink 103 Out $spec.output
    if($null -ne $spec.setup_node){
        $setup=(Get-QuestNode $branch $spec.setup_node).DeepCopy();$setup.Id=[uint16]12
        foreach($socket in $setup.Sockets){$socket.Chunk.Connections.Clear()}
        Put $setup
    }
    Put $phase;Put (New-SetFactNode 6 ($prefix+'Departed') 1);Put (New-SetFactNode 7 ($prefix+'Near') 0)
    Put (Pause 8 (New-FactCondition ($prefix+'Far') 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal)))
    # A stopped owner may still be waiting on its approach condition. Recheck
    # eligibility at the actual crossing, before any spawn or scene execution.
    Put (New-ConditionNode 9 ($guard.DeepCopy()))
    Put (Increment 10 ($prefix+'Entries'));Put (Increment 11 ($prefix+'Exits'))
    Link 0 Out 1;Link 1 Out 2;Link 2 Out 3;Link 3 Out 9;Link 9 True 4;Link 9 False 2
    Link 4 Out 10
    if($null -ne $spec.setup_node){Link 10 Out 12;Link 12 Out 5 In1}else{Link 10 Out 5 In1}
    Link 5 Out1 6;Link 6 Out 11;Link 11 Out 7;Link 7 Out 8;Link 8 Out 2
    $root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();$root.CookingPlatform=[WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC
    Set-RedHandleProperty $root Graph $graph
    $resource=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$resource.RootChunk=$root
    $depot='towercontinued\'+$scope+'\'+$spec.id+'.questphase'
    Write-Cr2wFile $resource (Join-Path $source $depot)
    Export-Cr2wJson (Read-Cr2wFile (Join-Path $source $depot)) (Join-Path $validation ($spec.id+'.questphase.json'))
    $packedPaths.Add($depot)
}
$actual=@(Get-ChildItem -LiteralPath $source -File -Recurse | ForEach-Object {[IO.Path]::GetRelativePath($source,$_.FullName)})
if(@(Compare-Object ($actual | Sort-Object) ($packedPaths | Sort-Object)).Count){throw 'Unexpected source manifest'}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$archivePath=Join-Path $output "TowerContinued_$package.archive"
$stream=[IO.File]::Create($archivePath)
try {if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Pack failed'}} finally {$stream.Dispose()}
$packed=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archivePath,$hs,[ref]$packed).ToString() -ne 'NoError'){throw 'Pack read failed'}
$names=@($packed.Files.Values | ForEach-Object Name)
if(@(Compare-Object ($names | Sort-Object) ($packedPaths | Sort-Object)).Count){throw 'Packed scope changed'}
foreach($entry in $packed.Files.Values){
    $m=[IO.MemoryStream]::new()
    try{$entry.Extract($m);if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($m.ToArray())) -ne (Get-FileHash -LiteralPath (Join-Path $source $entry.Name)).Hash){throw 'Packed bytes differ'}}finally{$m.Dispose()}
}
$xl=[Collections.Generic.List[string]]::new();$xl.Add('quest:');$xl.Add('  phases:')
foreach($depot in $packedPaths){foreach($line in @("    - path: $depot",'      parent: ep1\quest\ep1.quest','      input:','        node: [1]','        socket: Out')){$xl.Add($line)}}
[IO.File]::WriteAllText((Join-Path $WorkspaceRoot "archive\$scope\TowerContinued_$package.archive.xl"),($xl -join "`n")+"`n",[Text.UTF8Encoding]::new($false))
$manifest=[ordered]@{status='BUILT_AUTOMATIC_CANDIDATE_NOT_LIVE_VALIDATED';resources=$names;archive="TowerContinued_$package.archive";sha256=(Get-FileHash -LiteralPath $archivePath).Hash;cohort_sha256=(Get-FileHash -LiteralPath $cohortPath).Hash;common_guards=$common;scene_replacements=@();vanilla_replacements=@();new_sites=$cohort.sites.Count;dialogue='Complete original scene references retained';additional_guard='Recheck mode, Enabled, local gate and Tower immediately after distance crossing'}
[IO.File]::WriteAllText((Join-Path $validation 'build_manifest.json'),($manifest | ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
[pscustomobject]@{status=$manifest.status;new_sites=$cohort.sites.Count;scene_replacements=0;sha256=$manifest.sha256}
