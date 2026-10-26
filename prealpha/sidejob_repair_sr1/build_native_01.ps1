Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$helper=Get-Content -LiteralPath (Join-Path $ws 'tools/build_fresh_gigs_b5.ps1') -Raw
$begin=$helper.IndexOf('function ClearB5(');$end=$helper.IndexOf('$allRoots=@{};')
if($begin -lt 0 -or $end -le $begin){throw 'Quest helper boundary changed'}
. ([scriptblock]::Create($helper.Substring($begin,$end-$begin)))
$plan=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'plan_01.json') -Raw|ConvertFrom-Json
$out=Join-Path $PSScriptRoot 'candidate_01'
if(Test-Path -LiteralPath $out){throw 'Immutable candidate exists; use a successor'}
New-Item -ItemType Directory -Path (Join-Path $out 'source'),(Join-Path $out 'readback') -Force|Out-Null
$sources=@{};foreach($r in $plan.installed){$p=Join-Path $ws $r.raw;if((Get-FileHash -LiteralPath $p).Hash -cne $r.sha256){throw ('Installed source drift: '+$r.depot)};$sources[$r.depot]=$p}
$nb=Join-Path $ws $plan.native_bullets.path;if((Get-FileHash -LiteralPath $nb).Hash -cne $plan.native_bullets.sha256){throw 'Native default-dialogue donor drift'}
$ny='diagnostics/restored_audit_20261025_03/dialogue/native_01/15651456292936307253.scene';$ny=Join-Path $ws $ny
if((Get-FileHash -LiteralPath $ny).Hash -cne '3618C469468E73C67F6D1F9D8A4A85BABDA949FA1692A204DDE7C732EE253104'){throw 'Native Yoko donor drift'}
$resources=[ordered]@{};$edits=[Collections.Generic.List[object]]::new()
function SceneNode($file,[int]$id){$found=@($file.RootChunk.SceneGraph.Chunk.Graph|Where-Object {$_.Chunk.NodeId.Id.ToString() -ceq "$id"});if($found.Count -ne 1){throw "Scene node $id ambiguous"};return $found[0].Chunk}
function SaveFile($file,[string]$depot,[string]$label){$p=Join-Path (Join-Path $out 'source') $depot;Write-Cr2wFile $file $p;$rb=Join-Path $out ('readback/'+$label+'.json');Export-Cr2wJson (Read-Cr2wFile $p) $rb;$resources[$depot]=(Get-FileHash -LiteralPath $p).Hash}
function JournalActive(){
 $p=[WolvenKit.RED4.Types.gameJournalPath]::new();$p.RealPath='ep1/quests/main_quest/q305_postcontent';$p.ClassName='gameJournalQuest';$p.FileEntryIndex=2
 $t=[WolvenKit.RED4.Types.questJournalEntryState_ConditionType]::new();Set-RedHandleProperty $t Path $p;$t.State=[Enum]::Parse([WolvenKit.RED4.Types.Enums+gameJournalEntryState],'Active');$t.Inverted=$false
 $c=[WolvenKit.RED4.Types.questJournalCondition]::new();Set-RedHandleProperty $c Type $t;return $c
}

# Restore only This Corrosion's four native Yoko choices and their original
# destinations. Add an owner/journal gate; leave other disabled story choices.
$yokoDep='towercontinued\b0_story_eight\yoko.scene'
$private=Read-Cr2wFile $sources[$yokoDep];$native=Read-Cr2wFile $ny
$target=SceneNode $private 779;$donor=SceneNode $native 779
foreach($i in 4..7){
 if($target.OutputSockets[$i].Destinations.Count -ne 0 -or $donor.OutputSockets[$i].Destinations.Count -eq 0){throw "Yoko choice $i changed"}
 $target.Options[$i]=$donor.Options[$i].DeepCopy();$target.OutputSockets[$i]=$donor.OutputSockets[$i].DeepCopy()
 $gate=AllB5 ([ordered]@{PTFRS29_q305_postcontent_Issued=1;PTFRS29_q305_postcontent_Entered=1;PTFRS29_q305_postcontent_Fault=0})
 Add-RedHandle $gate.Conditions $target.Options[$i].QuestCondition.Chunk.DeepCopy()
 Add-RedHandle $gate.Conditions (JournalActive)
 Set-RedHandleProperty $target.Options[$i] QuestCondition $gate
}
if($target.OutputSockets[2].Destinations.Count -ne 0){throw 'Unrelated Yoko choice reopened'}
SaveFile $private $yokoDep 'yoko_scene';$edits.Add(@{kind='restore_haunted_weapon_choices';depot=$yokoDep;node=779;options=@(4,5,6,7);additional_gate='issued+entered+fault0+active_root';unrelated_option2_retained_disabled=$true})

# Recreate the original Zane default-owner rearm loop inside the private
# Bullets wrapper. Keep the native encounter/cleanup and service lease intact.
$bulletsDep='towercontinued\sidejobs_s23\base_b\mq030.questphase'
$file=Read-Cr2wFile $sources[$bulletsDep];$g=$file.RootChunk.Graph.Chunk;$original=(Get-QuestNode (Read-Cr2wFile $nb).RootChunk.Graph.Chunk 7).PhaseGraph.Chunk
$wait=(Get-QuestNode $original 26).DeepCopy();ClearB5 $wait;$wait.Id=[uint16]1021
if(@($g.Nodes|Where-Object {$_.Chunk.Id -eq 1021}).Count -ne 0){throw 'Bullets node 1021 already used'}
AddNodeB5 $g $wait
$edges=@(EdgesB5 $g|ForEach-Object {,@($_)})
if(@($edges|Where-Object {$_[0] -eq 1020}).Count -ne 0 -or @($edges|Where-Object {$_[0] -eq 1006 -and $_[2] -eq 1020}).Count -ne 1){throw 'Bullets owner boundary changed'}
$edges+=,@(1020,'Out1',1021,'In');$edges+=,@(1021,'Out',1020,'In1')
RebuildB5 $g $edges;SaveFile $file $bulletsDep 'bullets_owner';$edits.Add(@{kind='native_zane_rearm';depot=$bulletsDep;copied_native='base\quest\default_dialogs.questphase|root/7|26';new_node=1021;edges=@(@(1020,'Out1',1021,'In'),@(1021,'Out',1020,'In1'))})

# Declare the child's real End Quest return while retaining the original Out1
# socket for saved-owner compatibility; route only the receipt to End Quest.
$mqDep='towercontinued\sidejobs_s29\entries\mq058_semimaru_crystalcoat.questphase'
$file=Read-Cr2wFile $sources[$mqDep];$g=$file.RootChunk.Graph.Chunk;$child=Get-QuestNode $g 64000
if(@($child.Sockets|Where-Object {$_.Chunk.Name.ToString() -ceq 'Out1'}).Count -ne 1 -or @($child.Sockets|Where-Object {$_.Chunk.Name.ToString() -ceq 'End Quest'}).Count -ne 0){throw 'MQ058 sockets changed'}
[void](New-QuestSocket $child 'End Quest' 'Output')
$edges=@(EdgesB5 $g|ForEach-Object {,@($_)});$rewired=0
foreach($e in $edges){if($e[0] -eq 64000 -and $e[1] -ceq 'Out1' -and $e[2] -eq 65007){$e[1]='End Quest';$rewired++}}
if($rewired -ne 1){throw 'MQ058 receipt edge changed'}
RebuildB5 $g $edges;SaveFile $file $mqDep 'mq058_receipt';$edits.Add(@{kind='native_end_quest_receipt';depot=$mqDep;edge=@(64000,'End Quest',65007,'In');old_socket_retained=$true})

# Publish the shared Delamain phone-owner receipt on the S25 branch that
# actually starts its persistent native controller.
$s25Dep='towercontinued\sidejobs_s25\families\sq025_fresh.questphase'
$file=Read-Cr2wFile $sources[$s25Dep];$g=$file.RootChunk.Graph.Chunk
if(@($g.Nodes|Where-Object {$_.Chunk.Id -eq 65020}).Count -ne 0){throw 'S25 writer node used'}
AddNodeB5 $g (New-SetFactNode 65020 'PTFRS22_SQ025_SupportIssued' 1)
$edges=@(EdgesB5 $g|ForEach-Object {,@($_)});$rewired=0
foreach($e in $edges){if($e[0] -eq 92 -and $e[1] -ceq 'Out' -and $e[2] -eq 94 -and $e[3] -ceq 'In1'){$e[2]=65020;$e[3]='In';$rewired++}}
if($rewired -ne 1){throw 'S25 controller branch changed'}
$edges+=,@(65020,'Out',94,'In1');RebuildB5 $g $edges;SaveFile $file $s25Dep 's25_delamain_phone';$edits.Add(@{kind='shared_phone_owner_receipt';depot=$s25Dep;fact='PTFRS22_SQ025_SupportIssued';writer=65020;controller=94})

# Remove predecessor Epistrophy messages from the sequel's *fresh* guard.
# The sequel's own journal paths/facts and completed predecessor root remain.
$predecessor=@('contacts/delamain/sq025_divergent_found/all_found','contacts/delamain/sq025_divergent_found/all_returned_ch','contacts/delamain/sq025_divergent_found/all_returned_ch/all_returned_ch_01','contacts/delamain/sq025_divergent_found/all_returned_response','contacts/delamain/sq025_scan_damage/sq025_scan_damaged','contacts/delamain/sq025_scan_damage/sq025_scan_destroyed','contacts/delamain/sq025_scan_damage/sq025_scan_left')
$sequelDep='towercontinued\sidejobs_s29\entries\sq025b_delamain_insurgence.questphase'
$file=Read-Cr2wFile $sources[$sequelDep];$g=$file.RootChunk.Graph.Chunk
foreach($id in @(65003,65004)){
 $n=Get-QuestNode $g $id;$condition=$n.Condition.Chunk;$removed=[Collections.Generic.List[string]]::new()
 for($i=$condition.Conditions.Count-1;$i -ge 0;$i--){$c=$condition.Conditions[$i].Chunk;if($c -isnot [WolvenKit.RED4.Types.questJournalCondition]){continue};$p=$c.Type.Chunk.Path.Chunk.RealPath.ToString();if($p -in $predecessor){$condition.Conditions.RemoveAt($i);$removed.Add($p)}}
 if($removed.Count -ne 7 -or @($removed|Sort-Object -Unique).Count -ne 7){throw "Sequel guard $id predecessor mismatch"}
}
SaveFile $file $sequelDep 'delamain_sequel_guard';$edits.Add(@{kind='sequel_not_predecessor_message_freshness';depot=$sequelDep;guard_nodes=@(65003,65004);removed_paths=$predecessor})

# A saved S25 owner can predate the new receipt writer. Stop S29 from creating
# a second controller while that S25 owner exists; runtime adopts its receipt.
$phoneDep='towercontinued\sidejobs_s29\phone\delamain.questphase'
$file=Read-Cr2wFile $sources[$phoneDep];$g=$file.RootChunk.Graph.Chunk
foreach($id in @(1002,1003)){Add-RedHandle (Get-QuestNode $g $id).Condition.Chunk.Conditions (New-FactCondition 'PTFRS25_SQ025_FRESH_Issued' 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))}
SaveFile $file $phoneDep 'delamain_phone_guard';$edits.Add(@{kind='exclude_s25_owned_controller';depot=$phoneDep;guard_nodes=@(1002,1003);fact='PTFRS25_SQ025_FRESH_Issued';value=0})

$proof=[ordered]@{status='STAGED_NATIVE_SIX_RESOURCE_PATCH_NOT_INSTALLED';resources=$resources;edits=$edits.ToArray();plan_sha256=(Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'plan_01.json')).Hash;builder_sha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash;game_writes=0;save_writes=0}
[IO.File]::WriteAllText((Join-Path $out 'build_native_01.json'),($proof|ConvertTo-Json -Depth 60),[Text.UTF8Encoding]::new($false))
$proof|Select-Object status,@{n='resource_count';e={$_.resources.Count}},@{n='edit_count';e={$_.edits.Count}}|ConvertTo-Json
