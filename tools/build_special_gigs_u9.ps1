param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -HelpersOnly
. (Join-Path $PSScriptRoot 'shark_b7_2_helpers.ps1')
$audit=Join-Path $WorkspaceRoot 'research/gig_restoration/special_gigs_u9'
$out=Join-Path $WorkspaceRoot 'build/SpecialGigsU9'
if(Test-Path -LiteralPath (Join-Path $audit 'install_receipt.json')){throw 'Installed special U9 evidence pinned'}
$recipe=Get-Content -LiteralPath (Join-Path $audit 'recipes.json') -Raw|ConvertFrom-Json
foreach($pin in $recipe.pins.PSObject.Properties){R5Match (Join-Path $WorkspaceRoot $pin.Name) $pin.Value}
$helper=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'build_fresh_gigs_b5.ps1') -Raw
$begin=$helper.IndexOf('function ClearB5(');$end=$helper.IndexOf('$allRoots=@{};')
if($begin -lt 0 -or $end -le $begin){throw 'Helper boundary changed'}
. ([scriptblock]::Create($helper.Substring($begin,$end-$begin)))
$raw=Join-Path $WorkspaceRoot $recipe.ep1_parent_raw
$original=(Read-Cr2wFile $raw).RootChunk
$parent=(Get-QuestNode $original.Graph.Chunk 50).PhaseGraph.Chunk
$native=Get-QuestNode $parent 9
$g=[WolvenKit.RED4.Types.questGraphDefinition]::new()
$copy=$native.DeepCopy();ClearB5 $copy;RewireB5 $copy.PhaseGraph.Chunk $native.PhaseGraph.Chunk
AddNodeB5 $g $copy
function AnyS9($conditions){$c=[WolvenKit.RED4.Types.questLogicalCondition]::new();$c.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::OR;foreach($x in $conditions){Add-RedHandle $c.Conditions $x};return $c}
function JournalS9([string]$state){
 $v=(Get-QuestNode $native.PhaseGraph.Chunk 14).Condition.Chunk.Type.Chunk.DeepCopy()
 $v.Path.Chunk.ClassName='gameJournalPhoneMessage';$v.Path.Chunk.RealPath='contacts/mr_hands/mr_hands_global_msg/new_sts_unlocked';$v.Path.Chunk.FileEntryIndex=1
 $v.State=[WolvenKit.RED4.Types.Enums+gameJournalEntryState]::$state
 $c=[WolvenKit.RED4.Types.questJournalCondition]::new();Set-RedHandleProperty $c Type $v;return $c
}
$guard=AllB5 ([ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;q307_active=0;q115_point_of_no_return=0;q305_johnny_scene_active=0;debug_sts_start=0;PTFRU9_Support_Issued=1;PTFRU9_Support_Fault=0;PTFRU9_EP1Tier3_Entered=0})
$requests=AnyS9 @((AllB5 ([ordered]@{PTFRU9_sts_ep1_06_Request=1;PTFRU9_sts_ep1_06_Permit=1})),(AllB5 ([ordered]@{PTFRU9_sts_ep1_07_Request=1;PTFRU9_sts_ep1_07_Permit=1})))
Add-RedHandle $guard.Conditions $requests
$prior=[WolvenKit.RED4.Types.questLogicalCondition]::new();$prior.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
Add-RedHandle $prior.Conditions (AnyS9 @((JournalS9 'Active'),(JournalS9 'Succeeded')))
Add-RedHandle $prior.Conditions (AnyS9 @((New-FactCondition 'sts_ep1_tier_3' 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Greater)),(New-FactCondition 'q304_done' 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Greater))))
foreach($node in @((New-InputNode 0 'In1'),(PauseB5 65000 $guard),(New-SetFactNode 65001 'PTFRU9_EP1Tier3_Entered' 1),
 (New-ConditionNode 65002 (JournalS9 'Inactive')),(PauseB5 65003 $prior),(New-SetFactNode 65004 'PTFRU9_EP1Tier3_Ready' 1))){AddNodeB5 $g $node}
$edges=@(@(0,'Out',65000,'In'),@(65000,'Out',65001,'In'),@(65001,'Out',65002,'In'),@(65002,'True',9,'In1'),@(65002,'False',65003,'In'),@(65003,'Out',65004,'In'),@(9,'Out1',65004,'In'))
RebuildB5 $g $edges
# Keep nonterminating native gate alive for its original text-response branch.
# No independent reward/side-job/world root is started by this resource.
$container=(Get-QuestNode $original.Graph.Chunk 50).DeepCopy();ClearB5 $container;Set-RedHandleProperty $container PhaseGraph $g
$outer=[WolvenKit.RED4.Types.questGraphDefinition]::new();AddNodeB5 $outer (New-InputNode 0 'In1');AddNodeB5 $outer $container
RebuildB5 $outer (,@(0,'Out',50,'In1'));$g=$outer
$root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();Set-RedHandleProperty $root Graph $g
$f=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$f.RootChunk=$root
$depot='towercontinued\special_gigs_u9\ep1_tier3_gate.questphase'
$target=Join-Path (Join-Path $out 'source') $depot
Write-Cr2wFile $f $target
Export-Cr2wJson (Read-Cr2wFile $target) (Join-Path $audit 'ep1_tier3_gate.json')
. (Join-Path $PSScriptRoot 'build_special_gigs_u9_retaliation.ps1')
$retaliation=Build-RetaliationS9 $WorkspaceRoot $out $audit
$depots=@($depot,$retaliation.depot)
B71Parser|Out-Null
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$inventory=@(B72Inventory $game);$collision=@($depots|ForEach-Object {B72CollisionCheck $inventory $WorkspaceRoot $_})
$xl=B71Render $depots;B71Parse $xl|Out-Null
[IO.File]::WriteAllText((Join-Path $out 'TowerContinued_SpecialGigsU9.archive.xl'),$xl,[Text.UTF8Encoding]::new($false))
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$archive=Join-Path $out 'TowerContinued_SpecialGigsU9.archive';$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new((Join-Path $out 'source')),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -ne 'NoError' -or $packed.Files.Count -ne 2){throw 'Packed scope mismatch'}
if(@(Compare-Object @($depots|Sort-Object) @($packed.Files.Values|ForEach-Object {$_.Name}|Sort-Object)).Count){throw 'Packed names mismatch'}
foreach($entry in $packed.Files.Values){$m=[IO.MemoryStream]::new();try{$entry.Extract($m);if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($m.ToArray())) -ne (R5Hash (Join-Path (Join-Path $out 'source') $entry.Name))){throw 'Packed bytes mismatch'}}finally{$m.Dispose()}}
$files=@(
 @{source='build/SpecialGigsU9/TowerContinued_SpecialGigsU9.archive';relative='archive/pc/mod/TowerContinued_SpecialGigsU9.archive';predecessor=$null},
 @{source='build/SpecialGigsU9/TowerContinued_SpecialGigsU9.archive.xl';relative='archive/pc/mod/TowerContinued_SpecialGigsU9.archive.xl';predecessor=$null})
foreach($file in $files){$file.sha256=R5Hash (Join-Path $WorkspaceRoot $file.source)}
$sourcePins=[ordered]@{}
foreach($pin in $recipe.pins.PSObject.Properties){$sourcePins[$pin.Name]=$pin.Value}
foreach($pin in $retaliation.source_pins.GetEnumerator()){$sourcePins[$pin.Key]=$pin.Value}
foreach($rel in @('research/gig_restoration/special_gigs_u9/recipes.json','tools/build_special_gigs_u9.ps1','tools/build_special_gigs_u9_retaliation.ps1','tools/prepare_special_gigs_u9.py','tools/inspect_special_gigs_u9.py','tools/build_fresh_gigs_b5.ps1','tools/build_phase2a.ps1','tools/shark_b7_2_helpers.ps1')){$sourcePins[$rel]=R5Hash (Join-Path $WorkspaceRoot $rel)}
$manifest=[ordered]@{status='BUILT_SHARED_GATE_AND_NATIVE_RETALIATION_ENGINE_PENDING';files=$files;depot=$depot;boots=$depots;resources=@{($depot)=R5Hash $target;($retaliation.depot)=$retaliation.sha256};source_pins=$sourcePins;collision=$collision;resource_sha256=R5Hash $target;packed_readback=$true;source_raw=$recipe.ep1_parent_raw;source_sha256=R5Hash $raw;builder_sha256=R5Hash $PSCommandPath;ready_fact='PTFRU9_EP1Tier3_Ready';containing_phase_unfreezing_metadata_preserved=$true;independent_sidejob_owners=0;retaliation=$retaliation}
R5Json (Join-Path $audit 'manifest.json') $manifest
R5Json (Join-Path $audit 'manifest_additions.json') $manifest
'BUILT_SPECIAL_U9_SHARED_GATE'
