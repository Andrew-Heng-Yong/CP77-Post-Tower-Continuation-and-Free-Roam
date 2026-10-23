param([string]$Revision='gate_01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$WorkspaceRoot=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $WorkspaceRoot 'tools/build_phase2a.ps1') -HelpersOnly
. (Join-Path $WorkspaceRoot 'tools/shark_b7_2_helpers.ps1')
$helper=Get-Content (Join-Path $WorkspaceRoot 'tools/build_fresh_gigs_b5.ps1') -Raw
$begin=$helper.IndexOf('function ClearB5(');$end=$helper.IndexOf('$allRoots=@{};')
if($begin -lt 0 -or $end -le $begin){throw 'Helper boundary changed'}
. ([scriptblock]::Create($helper.Substring($begin,$end-$begin)))
if($Revision -cnotmatch '^gate_\d{2}$'){throw 'Invalid revision'}
$out=Join-Path $PSScriptRoot ('build/'+$Revision)
if(Test-Path -LiteralPath $out){throw 'Immutable build exists'}
New-Item -ItemType Directory $out,(Join-Path $out 'source'),(Join-Path $out 'readback')|Out-Null
$pins=[ordered]@{};$resources=[ordered]@{}
function Pin($p){$pins[$p]=(Get-FileHash -LiteralPath (Join-Path $WorkspaceRoot $p)).Hash}
$parentSource='research/courier_c1/roots_01/raw/ep1/openworld/ep1_open_world.questphase'
$gateSource='research/dogtown_dt1/gate/native_01/raw/ep1/openworld/combat_zone_gate/combat_zone_gate.questphase'
$ep1Source='research/q307_extracted/raw/ep1/quest/ep1.questphase'
foreach($p in @('prealpha/dogtown_dt1/gate/build.ps1','prealpha/dogtown_dt1/gate/research.py','prealpha/dogtown_dt1/gate/test.py','tools/build_phase2a.ps1','tools/build_fresh_gigs_b5.ps1','tools/shark_b7_2_helpers.ps1','tools/gig_family_b7_1_xl.ps1','tools/afterlife_faces_r5_deployment.ps1',$parentSource,$gateSource,$ep1Source,($parentSource.Replace('/raw/','/json/')+'.json'),($gateSource.Replace('/raw/','/json/')+'.json'),($ep1Source.Replace('/raw/','/json/')+'.json'))){Pin $p}
foreach($p in @('prealpha/ncpd_scanner_n1/native_inspect.py','tools/audit_activity_batches_b1.py','tools/catalog_gig_rollout_r2.py','tools/test_gig_pilot_r1.py')){Pin $p}
$pg=(Read-Cr2wFile (Join-Path $WorkspaceRoot $parentSource)).RootChunk.Graph.Chunk
$gg=(Read-Cr2wFile (Join-Path $WorkspaceRoot $gateSource)).RootChunk.Graph.Chunk
$pairs=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;PTFRPA2_Finished=1;PTFRPA2_Fault=0;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;q307_active=0;q307_debug_reset=0;q115_point_of_no_return=0;q305_johnny_scene_active=0;PTFRDT1_GateIssued=0;q304_block_dogtown_gate=0;wanted_level=0}
function GateGuard {
 $c=AllB5 $pairs
 foreach($f in @('ep1_side_content','q302_started')){Add-RedHandle $c.Conditions (New-FactCondition $f 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Greater))}
 # Both conditions are cloned from the SAME native gate, not fabricated APIs.
 $outside=(Get-QuestNode (Get-QuestNode $gg 7).PhaseGraph.Chunk 6).Condition.Chunk.DeepCopy()
 Add-RedHandle $c.Conditions $outside
 $safe=(Get-QuestNode $gg 177).Condition.Chunk
 foreach($child in $safe.Conditions){if($child.Chunk -is [WolvenKit.RED4.Types.questCharacterCondition]){Add-RedHandle $c.Conditions $child.Chunk.DeepCopy()}}
 return $c
}
$graph=[WolvenKit.RED4.Types.questGraphDefinition]::new()
$native=(Get-QuestNode $pg 13).DeepCopy();ClearB5 $native;$native.Id=[uint16]5
foreach($n in @((New-InputNode 0 'In1'),(New-SetFactNode 1 'PTFRDT1_GateReady' 1),(PauseB5 2 (GateGuard)),(New-ConditionNode 3 (GateGuard)),(New-SetFactNode 4 'PTFRDT1_GateIssued' 1),$native)){AddNodeB5 $graph $n}
RebuildB5 $graph @(@(0,'Out',1,'In'),@(1,'Out',2,'In'),@(2,'Out',3,'In'),@(3,'False',2,'In'),@(3,'True',4,'In'),@(4,'Out',5,'In1'))
$root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();Set-RedHandleProperty $root Graph $graph
$depot='towercontinued\dogtown_dt1\gate_boot.questphase';$file=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$file.RootChunk=$root
$raw=Join-Path (Join-Path $out 'source') $depot
Write-Cr2wFile $file $raw
Export-Cr2wJson (Read-Cr2wFile $raw) (Join-Path $out 'readback/gate_boot.json')
$resources[$depot]=(Get-FileHash -LiteralPath $raw).Hash
$result=[ordered]@{status='BUILT_DT1_GATE_LIVE_PENDING';component='gate';resources=$resources;boots=@($depot);source_pins=$pins;official_sources=@(@{depot='ep1\openworld\ep1_open_world.questphase';raw=$parentSource;json=$parentSource.Replace('/raw/','/json/')+'.json'},@{depot='ep1\openworld\combat_zone_gate\combat_zone_gate.questphase';raw=$gateSource;json=$gateSource.Replace('/raw/','/json/')+'.json'},@{depot='ep1\quest\ep1.questphase';raw=$ep1Source;json=$ep1Source.Replace('/raw/','/json/')+'.json'});guard_equal=$pairs;guard_positive=@('ep1_side_content','q302_started');guard_native=@{outside='root/7 node6 #combat_zone_gate_tr_respawn IsOutside';no_combat='root node177 player combat inverted1'};native_phase_payload='ep1_open_world root13 copied to boot5; id/socket connection changes only';changed_native_edges=@();changed_native_properties=@();official_overrides=@();runtime_scripts_added=0;scope='Restore original persistent checkpoint controller once, outside its native guard-respawn area and combat, after genuine Tower and earned Dogtown access. Original four lanes, scanners, wrong-direction lights, combat lockdown, guard respawn, autosave, native security and all q304 gates remain. No forced gate open, no story replay, no native fact reset, no blanket prevention change. GateIssued is dispatch proof only, not live crossing proof.'}
[IO.File]::WriteAllText((Join-Path $out 'component.json'),($result|ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false))
@{status=$result.status;build=$out;sha256=(Get-FileHash -LiteralPath (Join-Path $out 'component.json')).Hash}|ConvertTo-Json
