param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),[string]$WolvenKitRoot='C:\Users\Ayong\Documents\WolvenKit-8.20.0')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -WolvenKitRoot $WolvenKitRoot -HelpersOnly
$research=Join-Path $WorkspaceRoot 'research\b0_deferred_ordinary'
$sites=Get-Content (Join-Path $research 'sites.json') -Raw | ConvertFrom-Json
$audit=Get-Content (Join-Path $research 'owner_slices.json') -Raw | ConvertFrom-Json
$source=Join-Path $WorkspaceRoot 'archive\b0_deferred_ordinary\source'
$out=Join-Path $WorkspaceRoot 'build\B0_DeferredOrdinary'
$val=Join-Path $research 'validation'
New-Item -ItemType Directory -Force -Path $source,$out,$val | Out-Null
$base=Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\q307_extracted\raw\base\quest\cyberpunk2077.questphase')
$common=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;q307_active=0;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q305_johnny_scene_active=0;q115_point_of_no_return=0;q000_done=1}
function GraphAt($root,[string]$route){$g=$root.Graph.Chunk;foreach($part in ($route -split '/' | Select-Object -Skip 1)){$g=(Get-QuestNode $g ([int]$part.Substring(4))).PhaseGraph.Chunk};return $g}
function ClearSockets($node){foreach($s in $node.Sockets){$s.Chunk.Connections.Clear()}}
function Pause($id,$condition){$n=(Get-QuestNode $base.RootChunk.Graph.Chunk 106).DeepCopy();$n.Id=[uint16]$id;ClearSockets $n;Set-RedHandleProperty $n Condition $condition;return $n}
function AddLink($graph,$from,$socket,$to,$dest='In'){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $graph $from) $socket) (Get-QuestSocket (Get-QuestNode $graph $to) $dest))}
function Rewire($graph,$evidence){foreach($n in $graph.Nodes){ClearSockets $n.Chunk};foreach($e in $evidence.edges){AddLink $graph $e.source_node_id $e.source_socket $e.destination_node_id $e.destination_socket}}
function Increment($id,$fact){$n=New-SetFactNode $id $fact 1;$n.Type.Chunk.SetExactValue=$false;return $n}
$paths=[Collections.Generic.List[string]]::new();$hashes=@{}
foreach($s in $sites){
    $raw=Join-Path $WorkspaceRoot $s.owner_raw;$json=Join-Path $WorkspaceRoot $s.owner_json
    if((Get-FileHash $json).Hash -ne $audit.($s.key).sha256){throw 'Audited owner changed'}
    foreach($p in @($raw,$json,(Join-Path $WorkspaceRoot $s.scene_json))){$hashes[$p]=(Get-FileHash $p).Hash}
    $vendor=Read-Cr2wFile $raw
    $phase=(Get-QuestNode (GraphAt $vendor.RootChunk $s.parent_route) $s.phase).DeepCopy()
    $phase.Id=[uint16]5;ClearSockets $phase
    $outer=$phase.PhaseGraph.Chunk
    $inner=(Get-QuestNode $outer $s.inner_phase).PhaseGraph.Chunk
    Rewire $outer $audit.($s.key).graphs.($s.outer_route)
    Rewire $inner $audit.($s.key).graphs.($s.outer_route+'/node'+$s.inner_phase)
    if((Get-QuestNode $inner $s.scene_node).SceneFile.DepotPath.ToString() -ne $s.scene){throw 'Scene mismatch'}
    Set-RedHandleProperty (Get-QuestNode $outer $s.far) Condition (New-FactCondition ($s.prefix+'Far') 1 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
    # Preserve every original child edge, inserting only a request counter.
    $close=Get-QuestNode $inner $s.close;$scene=Get-QuestNode $inner $s.scene_node
    (Get-QuestSocket $close Out).Connections.Clear();(Get-QuestSocket $scene $s.scene_socket).Connections.Clear()
    Add-RedHandle $inner.Nodes (Increment 201 ($s.prefix+'SceneRequests'))
    AddLink $inner $s.close Out 201;AddLink $inner 201 Out $s.scene_node $s.scene_socket
    $guard=[WolvenKit.RED4.Types.questLogicalCondition]::new();$guard.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
    foreach($f in $common.Keys){Add-RedHandle $guard.Conditions (New-FactCondition $f $common[$f] ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))}
    Add-RedHandle $guard.Conditions (New-FactCondition ($s.prefix+'Enabled') 1 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
    foreach($f in @($s.gate)+@($s.extra_positive_gates)){Add-RedHandle $guard.Conditions (New-FactCondition $f 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Greater))}
    if($s.key -eq 'netrunner02'){
        # Same q305 journal exclusion as vanilla, without restarting its root.
        $journal=(Get-QuestNode $vendor.RootChunk.Graph.Chunk 68).Condition.Chunk
        foreach($c in $journal.Conditions){$notActive=$c.Chunk.DeepCopy();$notActive.Type.Chunk.Inverted=$true;Add-RedHandle $guard.Conditions $notActive}
        $watch=(Get-QuestNode $vendor.RootChunk.Graph.Chunk 68).DeepCopy();$watch.Id=[uint16]202;ClearSockets $watch
        Add-RedHandle $outer.Nodes $watch;AddLink $outer $s.input Out 202;AddLink $outer 202 Out $s.despawn
    }
    $g=[WolvenKit.RED4.Types.questGraphDefinition]::new()
    foreach($n in @((New-InputNode 0 'In1'),(New-SetFactNode 1 ($s.prefix+'Ready') 1),(Pause 2 $guard),
        (Pause 3 (New-FactCondition ($s.prefix+'Approach') 1 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))),
        (New-SetFactNode 4 ($s.prefix+'Near') 1),$phase,(New-SetFactNode 7 ($s.prefix+'Near') 0),
        (Pause 8 (New-FactCondition ($s.prefix+'Approach') 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))),
        (New-ConditionNode 9 ($guard.DeepCopy())),(Increment 10 ($s.prefix+'Entries')),(Increment 11 ($s.prefix+'Exits')))){Add-RedHandle $g.Nodes $n}
    foreach($e in @(@(0,'Out',1,'In'),@(1,'Out',2,'In'),@(2,'Out',3,'In'),@(3,'Out',9,'In'),@(9,'True',4,'In'),@(9,'False',2,'In'),@(4,'Out',10,'In'),@(10,'Out',5,'In1'),@(5,'Out1',11,'In'),@(11,'Out',7,'In'),@(7,'Out',8,'In'),@(8,'Out',2,'In'))){AddLink $g $e[0] $e[1] $e[2] $e[3]}
    $root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();$root.CookingPlatform=[WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC;Set-RedHandleProperty $root Graph $g
    $resource=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$resource.RootChunk=$root
    $depot='towercontinued\b0_deferred_ordinary\'+$s.key+'.questphase';$paths.Add($depot)
    Write-Cr2wFile $resource (Join-Path $source $depot)
    Export-Cr2wJson (Read-Cr2wFile (Join-Path $source $depot)) (Join-Path $val ($s.key+'.questphase.json'))
}
foreach($p in $hashes.Keys){if((Get-FileHash $p).Hash -ne $hashes[$p]){throw 'Source changed during build'}}
$actual=@(Get-ChildItem $source -Recurse -File | ForEach-Object {[IO.Path]::GetRelativePath($source,$_.FullName)})
if(@(Compare-Object ($paths|Sort-Object) ($actual|Sort-Object)).Count){throw 'Unexpected package scope'}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$archive=Join-Path $out 'TowerContinued_B0_DeferredOrdinary.archive';$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -ne 'NoError'){throw 'Archive readback failed'}
if($packed.Files.Count -ne 2){throw 'Unexpected archive entries'}
foreach($entry in $packed.Files.Values){$m=[IO.MemoryStream]::new();try{$entry.Extract($m);if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($m.ToArray())) -ne (Get-FileHash (Join-Path $source $entry.Name)).Hash){throw 'Archive bytes changed'}}finally{$m.Dispose()}}
$xl=@('quest:','  phases:');foreach($p in $paths){$xl+=@("    - path: $p",'      parent: ep1\quest\ep1.quest','      input:','        node: [1]','        socket: Out')}
[IO.File]::WriteAllText((Join-Path $WorkspaceRoot 'archive\b0_deferred_ordinary\TowerContinued_B0_DeferredOrdinary.archive.xl'),($xl -join "`n")+"`n")
$report=[ordered]@{status='BUILT_NOT_LIVE_TESTED';archive=$archive;sha256=(Get-FileHash $archive).Hash;resources=$paths.ToArray();source_hashes=$hashes;common_guards=$common;vanilla_replacements=@();scene_replacements=@();market_initialization_replayed=$false}
[IO.File]::WriteAllText((Join-Path $val 'build_manifest.json'),($report | ConvertTo-Json -Depth 8))
$report | ConvertTo-Json -Depth 4
