param(
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$WolvenKitRoot = 'C:\Users\Ayong\Documents\WolvenKit-8.20.0'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -WolvenKitRoot $WolvenKitRoot -HelpersOnly
$fb = 'base\quest\main_quests\epilogue\final_boards.questphase'
$qb = 'ep1\quest\main_quests\q307\phases\q307_ending_board.questphase'
$out = Join-Path $WorkspaceRoot 'build\Phase2B_P0'
$src = Join-Path $WorkspaceRoot 'archive\phase2b_p0_source'
$val = Join-Path $WorkspaceRoot 'research\phase2b_p0\validation'
$archiveName = 'TowerContinued_Phase2B_P0_DirectReturn.archive'
New-Item -ItemType Directory -Force -Path $src,$out,$val | Out-Null
$paths = @{
    final = Join-Path $WorkspaceRoot ('research\phase2a\pristine\' + $fb)
    board = Join-Path $WorkspaceRoot ('research\q307_extracted\raw\' + $qb)
}
$files = @{ final = Read-Cr2wFile $paths.final; board = Read-Cr2wFile $paths.board }
$original = @{ final = Read-Cr2wFile $paths.final; board = Read-Cr2wFile $paths.board }
$graphs = @{ final = $files.final.RootChunk.Graph.Chunk; board = $files.board.RootChunk.Graph.Chunk }
$p305 = Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\one_more_gig_extracted\raw\ep1\quest\main_quests\q305\phases\q305_08_border_crossing.questphase')
$credits = $p305.RootChunk.Graph.Chunk.Nodes[12].Chunk.PhaseGraph.Chunk
$cleanup = (Get-QuestNode $credits 33).PhaseGraph.Chunk
$setup = (Get-QuestNode $graphs.board 2).PhaseGraph.Chunk
$restrictionNames = @('NoMovement','BlockDeviceInteractions','NoPhotoMode','NoRadialMenus','NoTimeSkip','NoWorldInteractions') | ForEach-Object { 'GameplayRestriction.' + $_ }
$restrictionTemplate = Get-QuestNode $cleanup 19
$setupRestrictions = (Get-QuestNode $setup 18).Type.Chunk
if ($setupRestrictions.Source.ToString() -ne 'finalboards' -or $setupRestrictions.Action.ToString() -ne 'AddRestriction') { throw 'Unexpected Tower restriction owner/action' }
for ($i=0; $i -lt 6; $i++) {
    $expectedId = [WolvenKit.RED4.Types.TweakDBID]::op_Implicit($restrictionNames[$i])
    if ($expectedId -ne $setupRestrictions.RestrictionIDs[$i] -or $expectedId -ne $restrictionTemplate.Type.Chunk.RestrictionIDs[$i]) { throw "Restriction mismatch: $($restrictionNames[$i])" }
}
if ($setupRestrictions.RestrictionIDs.Count -ne 6) { throw 'Unexpected restriction count' }
$tokenTemplate = Get-QuestNode $setup 19
if ($tokenTemplate.Type.Chunk.Subtype.Chunk.Source.ToString() -ne 'finalboards' -or $tokenTemplate.Type.Chunk.Subtype.Chunk.Action.ToString() -ne 'Block') { throw 'Unexpected content source/action' }
$script:events = [System.Collections.Generic.List[object]]::new()
$script:edits = @{}
foreach ($key in @('final','board')) { $script:edits[$key] = [System.Collections.Generic.List[string]]::new() }
function Put($g,$node) {
    if (@($g.Nodes | Where-Object {$_.Chunk.Id.ToString() -eq $node.Id.ToString()}).Count) { throw "Duplicate node $($node.Id)" }
    Add-RedHandle $g.Nodes $node
    return $node
}
function Copy-Node($g,$template,[int]$id) {
    $n=$template.DeepCopy(); $n.Id=[uint16]$id
    foreach($s in $n.Sockets) { $s.Chunk.Connections.Clear() }
    return Put $g $n
}
function Link($g,[int]$a,[string]$aSocket,[int]$b,[string]$bSocket='In') {
    [void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $a) $aSocket) (Get-QuestSocket (Get-QuestNode $g $b) $bSocket))
}
function Unlink($g,[int]$a,[string]$aSocket,[int]$b,[string]$bSocket='In') {
    $s=Get-QuestSocket (Get-QuestNode $g $a) $aSocket; $d=Get-QuestSocket (Get-QuestNode $g $b) $bSocket
    $found=@($s.Connections | Where-Object {[object]::ReferenceEquals($_.Chunk.Destination.Chunk,$d)})
    if($found.Count -ne 1) { throw 'Unexpected edge to splice' }
    $c=$found[0].Chunk
    foreach($sock in @($s,$d)) { for($i=$sock.Connections.Count-1;$i -ge 0;$i--) { if([object]::ReferenceEquals($sock.Connections[$i].Chunk,$c)) { $sock.Connections.RemoveAt($i) } } }
}
function Mark([string]$key,[int]$id,[string]$event,[string]$label) {
    $fact='PTFRP0_'+$event
    $n=Put $graphs[$key] (New-SetFactNode $id $fact 1)
    $script:events.Add([ordered]@{fact=$fact;event=$event;label=$label;resource=$(if($key -eq 'board'){$qb}else{$fb});node=$id})
    return $n
}
function Guard($g,[int]$id,[bool]$armed) {
    $logic=[WolvenKit.RED4.Types.questLogicalCondition]::new()
    $logic.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
    foreach($f in @('q307_done','q307_finished','q307_2079')) { Add-RedHandle $logic.Conditions (New-FactCondition $f 1 ([WolvenKit.RED4.Types.Enums+EComparisonType]::GreaterOrEqual)) }
    foreach($f in @('q307_active','PostTowerFreeRoamActive')) { Add-RedHandle $logic.Conditions (New-FactCondition $f 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal)) }
    if($armed) { Add-RedHandle $logic.Conditions (New-FactCondition 'PTFRP0_DR02' 1 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal)) }
    return Put $g (New-ConditionNode $id $logic)
}
function Delay($g,[int]$id) {
    $n=Copy-Node $g (Get-QuestNode $graphs.board 11) $id
    $t=$n.Condition.Chunk.Type.Chunk
    if($t.GetType().Name -ne 'questRealtimeDelay_ConditionType') { throw 'Delay precedent changed' }
    $t.Hours=[uint32]0;$t.Minutes=[uint32]0;$t.Seconds=[uint32]0;$t.Miliseconds=[uint32]100
    return $n
}
# Q307-only start marker. Existing input fanout is untouched.
$g=$graphs.board
[void](Mark board 100 'DR03' 'Q307 ending-board input reached')
Link $g 0 Out 100
# Clone q305 inline credits node 46 verbatim (except id/socket connections).
[void](Guard $g 101 $false)
[void](Mark board 102 'DR01' 'Q307 completion guard passed')
$route=Copy-Node $g (Get-QuestNode $credits 46) 103
if($route.Type.Chunk.LoadPointOfNoReturnSave.ToString() -ne 'False') { throw 'Destination precedent not false' }
[void](Mark board 104 'DR02' 'LoadPonRSave(false) action returned')
[void](Mark board 105 'GUARD_FAILED' 'Q307 guard failed; vanilla route preserved')
foreach($dest in @(@(5,'In1'),@(21,'In'))) { Unlink $g 13 Out $dest[0] $dest[1] }
Link $g 13 Out 101
Link $g 101 True 102; Link $g 102 Out 103; Link $g 103 Out 104
Link $g 101 False 105
foreach($tail in @(104,105)) { Link $g $tail Out 5 In1; Link $g $tail Out 21 }
$edits.board.Add('13.Out -> 5.In1');$edits.board.Add('13.Out -> 21.In')
# Shared graph: pre-entry marker on the Q307-only incoming branch.
$g=$graphs.final
[void](Mark final 100 'DR04' 'Immediately before shared node27.In (graph-level entry)')
Unlink $g 53 Out1 27
Link $g 53 Out1 100; Link $g 100 Out 27
$edits.final.Add('53.Out1 -> 27.In')
# Preserve the exact original 27.Out -> 28.In edge. Parallel branch is guarded.
[void](Guard $g 101 $true)
Link $g 27 Out 101
[void](Mark final 102 'DR05' 'Guarded node27.Out traversed')
[void](Mark final 103 'DR06' 'Waiting for credits teardown')
Link $g 101 True 102; Link $g 102 Out 103
$rolling=(Get-QuestNode $graphs.board 13).Condition.Chunk
if($rolling.Type.Chunk.GetType().Name -ne 'questCreditsRolling_ConditionType') { throw 'Rolling condition changed' }
[void](Put $g (New-ConditionNode 104 ($rolling.DeepCopy())))
[void](Delay $g 105)
[void](Delay $g 106)
[void](Put $g (New-ConditionNode 107 ($rolling.DeepCopy())))
[void](Guard $g 108 $true)
Link $g 103 Out 104; Link $g 104 True 105; Link $g 105 Out 104
Link $g 104 False 106; Link $g 106 Out 107; Link $g 107 True 105; Link $g 107 False 108
[void](Mark final 109 'DR07' 'Rolling false rechecked; guard still valid')
Link $g 108 True 109
[void](Mark final 110 'DR08' 'Tier1 requested next')
Link $g 109 Out 110
[void](Copy-Node $g (Get-QuestNode $cleanup 21) 111); Link $g 110 Out 111
[void](Mark final 112 'DR09' 'Tier1 returned; show player requested next')
Link $g 111 Out 112
[void](Copy-Node $g (Get-QuestNode $cleanup 15) 113); Link $g 112 Out 113
[void](Mark final 114 'DR10' 'Show player returned; six-ID restriction removal starts')
Link $g 113 Out 114
$tail=114
for($i=0;$i -lt 6;$i++) {
    $id=115+2*$i
    $n=Copy-Node $g $restrictionTemplate $id
    $n.Type.Chunk.Source='finalboards';$n.Type.Chunk.RestrictionIDs.Clear()
    [void]$n.Type.Chunk.RestrictionIDs.Add($setupRestrictions.RestrictionIDs[$i])
    Link $g $tail Out $id
    [void](Mark final ($id+1) ('DR11_'+($i+1)) ('RemoveRestriction returned: '+$restrictionNames[$i]))
    Link $g $id Out ($id+1);$tail=$id+1
}
[void](Mark final 127 'DR12' 'Release finalboards content blocker requested next')
Link $g $tail Out 127
$unblock=Copy-Node $g $tokenTemplate 128
$unblock.Type.Chunk.Subtype.Chunk.Action=[WolvenKit.RED4.Types.Enums+questBlockAction]::Unblock
Link $g 127 Out 128
[void](Put $g (New-SetFactNode 129 'PostTowerFreeRoamActive' 1));Link $g 128 Out 129
[void](Mark final 130 'DR13' 'Content action returned; PostTowerFreeRoamActive set')
Link $g 129 Out 130
# No terminal phase output, timeout fallback, root restart, world teleport, or media writes.
$reports=@()
foreach($key in @('board','final')) {
    $depot=if($key -eq 'board'){$qb}else{$fb}
    $path=Join-Path $src $depot
    Write-Cr2wFile $files[$key] $path
    $cooked=Read-Cr2wFile $path; $cg=$cooked.RootChunk.Graph.Chunk
    if($cooked.MetaData.Version -ne 195) { throw 'CR2W version mismatch' }
    $before=$original[$key].RootChunk.Graph.Chunk
    foreach($h in $before.Nodes) {
        $id=[int]::Parse($h.Chunk.Id.ToString())
        if((Get-NodeWithoutConnectionsJson $h.Chunk) -ne (Get-NodeWithoutConnectionsJson (Get-QuestNode $cg $id))) { throw "Vanilla $key node $id properties changed" }
    }
    $beforeEdges=@(Get-GraphEdges $before);$afterEdges=@(Get-GraphEdges $cg)
    $removed=@($beforeEdges | Where-Object {$_ -notin $afterEdges})
    if(@(Compare-Object @($edits[$key]) $removed).Count) { throw 'Unexpected removed vanilla edge' }
    foreach($edge in (Get-GraphEdges $graphs[$key])) { Assert-ContainsExactlyOnce $afterEdges $edge $key }
    if($key -eq 'final') { Assert-ContainsExactlyOnce $afterEdges '27.Out -> 28.In' $key }
    # Every socket connection must name a socket owned by this graph and be reciprocal.
    $sockets=@($cg.Nodes | ForEach-Object {$_.Chunk.Sockets} | ForEach-Object {$_.Chunk})
    foreach($s in $sockets) { foreach($h in $s.Connections) {
        $c=$h.Chunk
        if(@($sockets | Where-Object {[object]::ReferenceEquals($_,$c.Source.Chunk)}).Count -ne 1 -or @($sockets | Where-Object {[object]::ReferenceEquals($_,$c.Destination.Chunk)}).Count -ne 1) { throw 'Dangling socket' }
        foreach($end in @($c.Source.Chunk,$c.Destination.Chunk)) { if(@($end.Connections | Where-Object {[object]::ReferenceEquals($_.Chunk,$c)}).Count -ne 1) { throw 'Nonreciprocal edge' } }
    } }
    Export-Cr2wJson $original[$key] (Join-Path $val "$key.original.json")
    Export-Cr2wJson $cooked (Join-Path $val "$key.patched.json")
    $reports+=@{resource=$depot;originalSha256=(Get-FileHash $paths[$key]).Hash;patchedSha256=(Get-FileHash $path).Hash;removedEdges=$removed;addedEdges=@($afterEdges | Where-Object {$_ -notin $beforeEdges});originalNodes=$before.Nodes.Count;patchedNodes=$cg.Nodes.Count}
}
$expected=@($fb,$qb)|Sort-Object
$actual=@(Get-ChildItem $src -Recurse -File | ForEach-Object {[IO.Path]::GetRelativePath($src,$_.FullName)} | Sort-Object)
if(@(Compare-Object $expected $actual).Count) { throw 'Unexpected archive source contents' }
$hashService=[WolvenKit.Common.Services.HashService]::new();$hashService.Load()
$path=Join-Path $out $archiveName
$stream=[IO.File]::Create($path)
try { $writer=[WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hashService,[WolvenKit.SerilogWrapper]::new());if(-not $writer.WriteArchive([IO.DirectoryInfo]::new($src),$stream)){throw 'Archive write failed'} } finally {$stream.Dispose()}
$ar=[WolvenKit.RED4.Archive.IO.ArchiveReader]::new();$packed=$null
if($ar.ReadArchive($path,$hashService,[ref]$packed).ToString() -ne 'NoError'){throw 'Archive reopen failed'}
$packedPaths=@($packed.Files.Values | ForEach-Object {$_.Name} | Sort-Object)
if(@(Compare-Object $expected $packedPaths).Count){throw 'Unexpected packed contents'}
foreach($entry in $packed.Files.Values){
    $ms=[IO.MemoryStream]::new();try{$entry.Extract($ms);$raw=[IO.File]::ReadAllBytes((Join-Path $src $entry.Name));if([Convert]::ToBase64String($ms.ToArray()) -ne [Convert]::ToBase64String($raw)){throw 'Packed resource byte mismatch'}}finally{$ms.Dispose()}
}
$manifest=[ordered]@{buildStatus='resource-validation-passed';archive=$path;sha256=(Get-FileHash $path).Hash;resources=$packedPaths;graphs=$reports;events=@($events);restrictions=$restrictionNames;runtimeValidated=$false;wait='CreditsRolling false twice separated by 100ms; True loops; no timeout';nativeSourceEvidence='research/phase2b_p0/native';loggerRequired=$true}
[IO.File]::WriteAllText((Join-Path $val 'build_manifest.json'),($manifest|ConvertTo-Json -Depth 12))
$loggerSource=Join-Path $WorkspaceRoot 'diagnostics\PTFR_Phase2B_P0'
New-Item -ItemType Directory -Force -Path $loggerSource | Out-Null
[IO.File]::WriteAllText((Join-Path $loggerSource 'events.json'),(@($events)|ConvertTo-Json -Depth 5))
$loggerTarget=Join-Path $out 'PTFR_Phase2B_P0'
New-Item -ItemType Directory -Force -Path $loggerTarget | Out-Null
foreach($name in @('init.lua','events.json')) {
    Copy-Item -LiteralPath (Join-Path $loggerSource $name) -Destination (Join-Path $loggerTarget $name)
    if((Get-FileHash (Join-Path $loggerSource $name)).Hash -ne (Get-FileHash (Join-Path $loggerTarget $name)).Hash) { throw 'Logger copy mismatch' }
}
if(@(Get-ChildItem $loggerTarget -File).Count -ne 2) { throw 'Unexpected logger files' }
$manifest | ConvertTo-Json -Depth 4
