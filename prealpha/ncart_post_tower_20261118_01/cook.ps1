param([string]$Output='cook_01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$WorkspaceRoot=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $WorkspaceRoot 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $WorkspaceRoot 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$helpers=Get-Content (Join-Path $WorkspaceRoot 'tools/build_fresh_gigs_b5.ps1') -Raw
$start=$helpers.IndexOf('function ClearB5(')
. ([scriptblock]::Create($helpers.Substring($start,$helpers.IndexOf('function RewardB5(')-$start)))
$work=Join-Path $PSScriptRoot 'work'
$out=Join-Path $work $Output
if ($Output -cnotmatch '^cook_\d+$' -or (Test-Path $out)) {throw 'Fresh cook output required'}
$providers=Get-Content (Join-Path $work 'sources_01/providers.json') -Raw | ConvertFrom-Json
$parent=Join-Path $WorkspaceRoot 'prealpha/welcome_to_paradise_cut_20261118_01'
$parentHash='FF043272463E7CEE53E367495DA589F18158F049A3F970455C56BD1FDAB111E0'
if ((Get-FileHash (Join-Path $parent 'candidate_01/core_manifest.json')).Hash -cne $parentHash) {throw 'Staged parent changed'}
$prefix='towercontinued\ncart\'
$native='base\open_world\metro\ue_metro\'
$ride=$native+'scenes\ue_metro_01_train_ride.scene'
function Donor([string]$path) {
    $rows=@($providers.hits | Where-Object depot -CEQ $path)
    if ($rows.Count -ne 1 -or (Get-FileHash $rows[0].raw).Hash -cne $rows[0].sha256) {throw "Ambiguous or changed donor $path"}
    Read-Cr2wFile $rows[0].raw
}
$records=[Collections.Generic.List[object]]::new()
function Save($file,$depot) {
    $raw=Join-Path $out ('source/'+$depot)
    $back=Join-Path $out ('readback/'+$depot+'.json')
    foreach ($path in @($raw,$back)) {[void][IO.Directory]::CreateDirectory((Split-Path $path -Parent))}
    Write-Cr2wFile $file $raw
    Export-Cr2wJson (Read-Cr2wFile $raw) $back
    $records.Add(@{depot=$depot;raw=$raw;sha256=(Get-FileHash $raw).Hash;json=$back;json_sha256=(Get-FileHash $back).Hash})
}
function BindPhase($node,$path) {
    $node.PhaseResource=[WolvenKit.RED4.Types.CResourceAsyncReference`1[WolvenKit.RED4.Types.questQuestPhaseResource]]::new($path)
}
# The wrapper owns no world prefab while it is waiting for the ending.
$entry=[WolvenKit.RED4.Types.questGraphDefinition]::new()
$gate=AllB5 ([ordered]@{PostTowerFreeRoamActive=1;PTFRPA2_Finished=1;PTFRPA2_Fault=0;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;q307_active=0;q307_debug_reset=0;q115_point_of_no_return=0;PTFRNCART_Issued=0})
$idle=AllB5 ([ordered]@{ue_metro_ride_started=0;ue_metro_player_in_train_transition=0;watson_prolog_lock=0;PTFRNCART_Issued=0})
$pass=[WolvenKit.RED4.Types.questInventory_ConditionType]::new()
$pass.ItemID='Items.ue_metro_ncart_city_pass';$pass.IsPlayer=$true;$pass.Quantity=[uint32]1
$pass.ComparisonType=[WolvenKit.RED4.Types.Enums+EComparisonType]::GreaterOrEqual
$object=[WolvenKit.RED4.Types.questObjectCondition]::new()
Set-RedHandleProperty $object Type $pass
Add-RedHandle $idle.Conditions $object
$check=$gate.DeepCopy();Add-RedHandle $check.Conditions $idle.DeepCopy()
$open=(Donor 'base\open_world\phases\open_world_content.questphase').RootChunk.Graph.Chunk
$child=(Get-QuestNode (NestedB5 $open @(156)) 6).DeepCopy()
ClearB5 $child;BindPhase $child ($prefix+'service.questphase')
foreach ($node in @((New-InputNode 0 'In1'),(PauseB5 1 $gate),(PauseB5 2 $idle),(New-ConditionNode 3 $check),(New-SetFactNode 4 'PTFRNCART_Issued' 1),$child)) {AddNodeB5 $entry $node}
$edges=@(@(0,'Out',1,'In'),@(1,'Out',2,'In'),@(2,'Out',3,'In'),@(3,'False',1,'In'),@(3,'True',4,'In'),@(4,'Out',6,'In1'))
RebuildB5 $entry $edges
$root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();Set-RedHandleProperty $root Graph $entry
$file=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$file.RootChunk=$root
Save $file ($prefix+'entry.questphase')

# Keep the original prefab on the service and the nested lease in train prep.
# 102 sends the first NCART message and grants the pass. 7 disables the old
# data terminals and can deregister fast travel during the Watson prologue.
$service=Donor ($native+'ue_metro_main.questphase')
$graph=$service.RootChunk.Graph.Chunk
$edges=@(EdgesB5 $graph | ForEach-Object {$_} | Where-Object {$_[0] -notin @(7,102) -and $_[2] -notin @(7,102)})
foreach ($id in @(7,102)) {
    $handle=@($graph.Nodes | Where-Object {$_.Chunk.Id.ToString() -eq "$id"})
    if ($handle.Count -ne 1) {throw "Missing metro branch $id"}
    [void]$graph.Nodes.Remove($handle[0])
}
RebuildB5 $graph $edges
BindPhase (Get-QuestNode $graph 16) ($prefix+'train_handler.questphase')
Save $service ($prefix+'service.questphase')

$train=Donor ($native+'phases\ue_metro_train_handler.questphase')
foreach ($id in @(4,10)) {
    $node=Get-QuestNode $train.RootChunk.Graph.Chunk $id
    $node.SceneFile=[WolvenKit.RED4.Types.CResourceAsyncReference`1[WolvenKit.RED4.Types.scnSceneResource]]::new($prefix+'train_ride.scene')
}
Save $train ($prefix+'train_handler.questphase')

$scene=Donor $ride
$actors=@($scene.RootChunk.Actors | Where-Object {$_.ActorName.ToString() -ceq 'Johnny'})
if ($actors.Count -ne 1) {throw 'Train actor drift'}
$spawn=$actors[0].SpawnDespawnParams
$spawn.IsEnabled=$false;$spawn.SpawnOnStart=$false;$spawn.AlwaysSpawned=$false
$nodes=@{};foreach ($h in $scene.RootChunk.SceneGraph.Chunk.Graph) {$nodes[[int]$h.Chunk.NodeId.Id.ToString()]=$h.Chunk}
# Redirect both ambient encounters to their own already-played reroll, including
# the authored debug selection. Preserve the competing encounters and their weights.
foreach ($route in @(@(2199,1,2203,860,4),@(2923,0,2203,860,4),@(3368,1,3377,640,7))) {
    $ports=@($nodes[$route[0]].OutputSockets | Where-Object {$_.Stamp.Name.ToString() -eq '0' -and $_.Stamp.Ordinal.ToString() -eq [string]$route[1]})
    if ($ports.Count -ne 1 -or $ports[0].Destinations.Count -ne 1) {throw 'Unexpected train scene socket'}
    $dest=$ports[0].Destinations[0]
    if ($dest.NodeId.Id.ToString() -ne [string]$route[2] -or $dest.IsockStamp.Ordinal.ToString() -ne '0') {throw 'Unexpected train scene target'}
    $dest.NodeId.Id=[uint32]$route[3];$dest.IsockStamp.Ordinal=[uint16]$route[4]
}
Save $scene ($prefix+'train_ride.scene')

$lip='towercontinued\sidejob_repair_sr1\en-us.lipmap'
$source=Join-Path $parent ('work/assets_02/source/'+$lip)
$pin=@((Get-Content (Join-Path $parent 'work/assets_02/readback.json') -Raw | ConvertFrom-Json).resources | Where-Object depot -ceq $lip)
if ($pin.Count -ne 1 -or (Get-FileHash $source).Hash -cne $pin[0].sha256) {throw 'Lipmap parent drift'}
$map=Read-Cr2wFile $source
$stock=(Donor 'base\localization\en-us.lipmap').RootChunk
$key=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($ride)
$destKey=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($prefix+'train_ride.scene')
$indices=@(for ($i=0;$i -lt $stock.ScenePaths.Count;$i++) {if ($stock.ScenePaths[$i].ToString() -ceq $key.ToString()) {$i}})
if ($indices.Count -ne 1 -or @($map.RootChunk.ScenePaths | Where-Object {$_.ToString() -ceq $destKey.ToString()}).Count) {throw 'Train lipmap conflict'}
$map.RootChunk.ScenePaths.Add([WolvenKit.RED4.Types.CUInt64]::op_Implicit([uint64]$destKey))
$map.RootChunk.SceneEntries.Add($stock.SceneEntries[$indices[0]].DeepCopy())
Save $map $lip
@{resources=$records.ToArray();parent_sha256=$parentHash} | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $out 'manifest.json') -Encoding utf8NoBOM
