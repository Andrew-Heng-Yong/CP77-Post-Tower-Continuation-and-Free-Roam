param([string]$Name='cook_01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$WorkspaceRoot=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $WorkspaceRoot 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $WorkspaceRoot 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
. (Join-Path $WorkspaceRoot 'tools/shark_b7_2_helpers.ps1')
$helpers=Get-Content (Join-Path $WorkspaceRoot 'tools/build_fresh_gigs_b5.ps1') -Raw
$start=$helpers.IndexOf('function ClearB5(')
. ([scriptblock]::Create($helpers.Substring($start,$helpers.IndexOf('$allRoots=@{};')-$start)))
$work=Join-Path $PSScriptRoot 'work'
$out=Join-Path $work $Name
if ($Name -cnotmatch '^cook_\d+$' -or (Test-Path $out)) { throw 'Fresh cook required' }
$null=New-Item -ItemType Directory $out
function Json($path) { Get-Content -LiteralPath $path -Raw | ConvertFrom-Json -AsHashtable -Depth 100 }
$contract=Json (Join-Path $work 'contract_02.json')
$source=Json (Join-Path $work 'sources_01/providers.json')
$extra=Json (Join-Path $work 'extra_01/providers.json')
$prefix='towercontinued\paradise\'
$records=[Collections.Generic.List[object]]::new()
function SaveResource($file,$depot) {
    $raw=Join-Path $out ('source/'+$depot)
    $back=Join-Path $out ('readback/'+$depot+'.json')
    foreach ($path in @($raw,$back)) { $null=New-Item -ItemType Directory -Path (Split-Path $path -Parent) -Force }
    Write-Cr2wFile $file $raw
    Export-Cr2wJson (Read-Cr2wFile $raw) $back
    $records.Add(@{depot=$depot;raw=$raw;sha256=(Get-FileHash $raw).Hash;json=$back;json_sha256=(Get-FileHash $back).Hash})
}
function CookJson($path,$depot) {
    $text=[IO.File]::ReadAllText($path)
    $dto=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Deserialize([WolvenKit.Common.Conversion.RedFileDto],$text,[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())
    $f=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$f.RootChunk=$dto.Data.RootChunk
    if (@(($text | ConvertFrom-Json -AsHashtable -Depth 100).Data.EmbeddedFiles).Count -gt 0) {throw "Embedded data requires binding $depot"}
    SaveResource $f $depot
}
foreach ($native in $contract.private) {
    $depot=$prefix+$native
    CookJson (Join-Path $work ('edited_02/'+$depot+'.json')) $depot
}
function Hit($evidence,$name) {
    $hits=@($evidence.hits | Where-Object depot -ceq $name)
    if (!$hits.Count -or @($hits.sha256 | Select-Object -Unique).Count -ne 1) {throw "Missing or conflicting donors $name"}
    if ((Get-FileHash $hits[0].raw).Hash -cne $hits[0].sha256) {throw "Donor changed $name"}
    return $hits[0].raw
}
function MuteWorkspot($part,[ref]$changed) {
    if ($part -is [Collections.IDictionary]) {
        if ($part['$type'] -ceq 'animAnimNode_WorkspotHub') {
            if ($part.eventFilterType -cnotin @('Mute','Default')) {throw 'Unreviewed event filter'}
            $part.eventFilterType='Mute';$changed.Value++
        }
        if ($part['$type'] -ceq 'workWorkspotTree' -and $part.initialActions.Count) {
            foreach ($act in $part.initialActions) {if ($act.Data.'$type' -cne 'workEquipItemToSlotAction') {throw 'Unreviewed workspot action'}}
            $part.initialActions=@();$changed.Value++
        }
        foreach ($child in $part.Values) {MuteWorkspot $child $changed}
    } elseif ($part -is [array]) {foreach ($child in $part) {MuteWorkspot $child $changed}}
}
foreach ($native in $contract.workspots) {
    $dump=Join-Path $out ((Split-Path $native -Leaf)+'.json')
    Export-Cr2wJson (Read-Cr2wFile (Hit $extra $native)) $dump
    $doc=Json $dump;$count=0;MuteWorkspot $doc ([ref]$count)
    if (!$count) {throw "No visual action identified $native"}
    $target=$dump+'.private.json'
    [IO.File]::WriteAllText($target,($doc|ConvertTo-Json -Depth 100 -Compress))
    CookJson $target ($prefix+$native)
}
$lip='towercontinued\sidejob_repair_sr1\en-us.lipmap'
$combined=Read-Cr2wFile (Hit $extra $lip);$official=(Read-Cr2wFile (Hit $extra 'base\localization\en-us.lipmap')).RootChunk
function Key($path) {[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($path)}
$lipBefore=$combined.RootChunk.ScenePaths.Count
foreach ($scene in $contract.presentation.Keys) {
    $key=Key $scene;$dest=Key ($prefix+$scene)
    $index=@(for ($i=0;$i -lt $official.ScenePaths.Count;$i++) {if ($official.ScenePaths[$i].ToString() -ceq $key.ToString()) {$i}})
    if (!$index.Count -and $scene -ceq 'base\quest\minor_quests\mq061\scenes\mq061_12_kabuki_scene_haze_body.scene') {
        # Johnny is the only scene actor here. The native English map has no entry.
        continue
    }
    if ($index.Count -ne 1 -or @($combined.RootChunk.ScenePaths | Where-Object {$_.ToString() -ceq $dest.ToString()}).Count) {throw "Lipmap binding $scene"}
    $combined.RootChunk.ScenePaths.Add([WolvenKit.RED4.Types.CUInt64]::op_Implicit([uint64]$dest))
    $combined.RootChunk.SceneEntries.Add($official.SceneEntries[$index[0]].DeepCopy())
}
if ($combined.RootChunk.ScenePaths.Count -ne ($lipBefore+3)) {throw 'Missing lip sync'}
SaveResource $combined $lip
$parent=(Read-Cr2wFile (Hit $source 'base\quest\bugfixing\quest_bugfixing.questphase')).RootChunk.Graph.Chunk
$nativeGraph=(Get-QuestNode $parent 3).PhaseGraph.Chunk
$g=[WolvenKit.RED4.Types.questGraphDefinition]::new()
foreach ($id in @(126..135)+@(142)) {
    $node=(Get-QuestNode $nativeGraph $id).DeepCopy();ClearB5 $node;AddNodeB5 $g $node
}
$child=Get-QuestNode $g 126
$child.PhaseResource=[WolvenKit.RED4.Types.CResourceAsyncReference`1[WolvenKit.RED4.Types.questQuestPhaseResource]]::new($prefix+'base\quest\minor_quests\mq061\mq061.questphase')
if ('Out1' -cnotin @($child.Sockets | ForEach-Object {$_.Chunk.Name.ToString()})) {[void](New-QuestSocket $child 'Out1' 'Output')}
$tag='PTFRParadise'
$pairs=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;PTFRPA2_Finished=1;PTFRPA2_Fault=0;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;q307_active=0;q307_debug_reset=0;q115_point_of_no_return=0;q305_johnny_scene_active=0;PTFRU9_Support_Issued=1;PTFRU9_Support_Fault=0}
foreach ($name in $contract.facts) {$pairs[$name]=0}
foreach ($suffix in @('Issued','Entered','Finished','Fault')) {$pairs[$tag+'_'+$suffix]=0}
$pairs[$tag+'_Permit']=1
$guard=AllB5 $pairs
$path=[WolvenKit.RED4.Types.gameJournalPath]::new();$path.RealPath='quests/minor_quest/mq061';$path.ClassName='gameJournalQuest';$path.FileEntryIndex=2
$state=[WolvenKit.RED4.Types.questJournalEntryState_ConditionType]::new();Set-RedHandleProperty $state Path $path
$state.State=[WolvenKit.RED4.Types.Enums+gameJournalEntryState]::Inactive
$journal=[WolvenKit.RED4.Types.questJournalCondition]::new();Set-RedHandleProperty $journal Type $state;Add-RedHandle $guard.Conditions $journal
foreach ($node in @((New-InputNode 65000 'In1'),(New-SetFactNode 65001 ($tag+'_Ready') 1),(New-SetFactNode 65002 ($tag+'_Revision') 1),(PauseB5 65003 $guard),(New-SetFactNode 65004 ($tag+'_Ready') 2),(New-SetFactNode 65005 ($tag+'_Permit') 0),(New-SetFactNode 65006 ($tag+'_Ready') 1),(PauseB5 65007 $guard.DeepCopy()),(New-ConditionNode 65008 $guard.DeepCopy()),(New-SetFactNode 65009 ($tag+'_Issued') 1),(New-SetFactNode 65010 ($tag+'_Entered') 1),(New-SetFactNode 65011 ($tag+'_Finished') 1))) {AddNodeB5 $g $node}
$edges=@(Json (Join-Path $PSScriptRoot 'native_edges.json'))
foreach ($edge in $edges) {if ($edge[0] -eq 128 -and $edge[2] -eq 126) {$edge[2]=65006;$edge[3]='In'}}
foreach ($pair in @('65000:65001','65001:65002','65002:65003','65003:65004','65004:65005','65005:129','65006:65007','65007:65008','65009:65010')) {
    $ids=$pair.Split(':');$edges+=,@([int]$ids[0],'Out',[int]$ids[1],'In')
}
$edges+=,@(65008,'False',65007,'In');$edges+=,@(65008,'True',65009,'In');$edges+=,@(65010,'Out',126,'In1');$edges+=,@(126,'Out1',65011,'In')
RebuildB5 $g $edges
$root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();Set-RedHandleProperty $root Graph $g
$file=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$file.RootChunk=$root
SaveResource $file ($prefix+'entry.questphase')
@{resources=$records.ToArray();baseline_sha256=$source.manifest_sha256;status='SERIALIZED'} | ConvertTo-Json -Depth 7 | Set-Content -LiteralPath (Join-Path $out 'manifest.json') -Encoding utf8NoBOM
Write-Output "Serialized and re-opened $($records.Count) resources."
