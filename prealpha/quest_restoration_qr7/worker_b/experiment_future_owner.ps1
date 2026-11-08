param([string]$OutputName='experiments/future_owner_01')
# PRIVATE SOURCE-BASED PROPOSAL. No registration, package or production write.
$ErrorActionPreference='Stop'
$ws=(Get-Location).Path;$homeDir=Join-Path $ws 'prealpha/quest_restoration_qr7/worker_b';$out=Join-Path $homeDir $OutputName
if(Test-Path -LiteralPath $out){throw 'Fresh output required'}
New-Item -ItemType Directory -Path $out -Force|Out-Null
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$spec=Get-Content -Raw -LiteralPath (Join-Path $homeDir 'future_protocol_spec_01.json')|ConvertFrom-Json
$pins=Get-Content -Raw -LiteralPath (Join-Path $homeDir 'raw_inputs_01.json')|ConvertFrom-Json
$nativePin=@($pins|Where-Object {$_.depot -ceq 'ep1\quest\main_quests\q302\phases\q302_ronald_tree.questphase'})[0]
$b0Pin=@($pins|Where-Object {$_.depot -ceq 'towercontinued\b0_story_eight\ronald.questphase'})[0]
$smsPin=@($pins|Where-Object {$_.depot -ceq 'ep1\quest\main_quests\q302\phases\q302_msg_ronald_sts_ep1_12.questphase'})[0]
foreach($p in @($nativePin,$b0Pin,$smsPin)){if((Get-FileHash -LiteralPath $p.raw).Hash -cne $p.raw_sha256){throw 'Pinned native/current input changed'}}
$native=Read-Cr2wFile $nativePin.raw;$b0=Read-Cr2wFile $b0Pin.raw;$sms=Read-Cr2wFile $smsPin.raw
$donor=(Get-QuestNode $native.RootChunk.Graph.Chunk 11).PhaseGraph.Chunk
function Put($g,$n){Add-RedHandle $g.Nodes $n}
function Link($g,$a,$s,$b,$d){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $a) $s) (Get-QuestSocket (Get-QuestNode $g $b) $d))}
function AndCondition($parts){$c=[WolvenKit.RED4.Types.questLogicalCondition]::new();$c.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND;foreach($p in $parts){Add-RedHandle $c.Conditions $p};return $c}
function PauseNode($id,$condition){$n=(Get-QuestNode $native.RootChunk.Graph.Chunk 12).DeepCopy();$n.Id=[uint16]$id;foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()};Set-RedHandleProperty $n Condition $condition;return $n}
$g=[WolvenKit.RED4.Types.questGraphDefinition]::new()
foreach($id in $spec.kept_native_ids){$n=(Get-QuestNode $donor $id).DeepCopy();foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()};Put $g $n}
# Selected native terminal fan-in is four, while original fifth input belongs only to removed fluff.
$terminal=Get-QuestNode $g 67;$terminal.InputSocketCount=[uint32]4
$socket5=@($terminal.Sockets|Where-Object {$_.Chunk.Name.ToString() -eq 'In5'})[0];[void]$terminal.Sockets.Remove($socket5)
foreach($e in $spec.kept_edges){Link $g $e[0] $e[1] $e[2] $e[3]}
Put $g (New-InputNode 0 'In1')
# Phase entry acquires a private lease; explicit loaded checks prevent an unavailable trigger from masquerading as IsOutside.
$markers=Get-Content -Raw -LiteralPath (Join-Path $homeDir 'experiments/markers_04/NOT_FOR_INTEGRATION.json')|ConvertFrom-Json
$loaded=@()
foreach($ref in $markers.private_refs){$p=[WolvenKit.RED4.Types.questNodeLoadingCondition]::new();$p.ObjectRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($ref);$p.Inverted=$false;$loaded+=,$p}
Put $g (PauseNode 220 (AndCondition $loaded));Link $g 0 Out 220 In
foreach($c in $spec.case_gates){
 $armFact='PTFRQR7_RonaldNews_Armed_'+$c.quest
 $history=[WolvenKit.RED4.Types.questLogicalCondition]::new();$history.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::OR
 Add-RedHandle $history.Conditions (New-FactCondition ('PTFRU9_'+$c.quest+'_ParentEntered') 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
 Add-RedHandle $history.Conditions (New-FactCondition $armFact 1 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
 $condition=AndCondition @((New-FactCondition $c.done_fact 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal)),(New-FactCondition $c.sent_fact 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal)),$history)
 Put $g (New-ConditionNode $c.id $condition)
 $waitId=[int]$c.id+10;Put $g (PauseNode $waitId (New-FactCondition $armFact 1 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal)))
 Link $g 220 Out $c.id In;Link $g $c.id True $waitId In;Link $g $waitId Out $c.hub In1;Link $g $c.id False $c.skip_hub In1
}
# Only spatial condition references change; timers, native facts and child paths retain their authored values.
foreach($n in $g.Nodes){
 if($n.Chunk.GetType().Name -eq 'questPauseConditionNodeDefinition'){
  $condition=$n.Chunk.Condition.Chunk
  if($condition.GetType().Name -eq 'questLogicalCondition'){
   foreach($c in $condition.Conditions){if($c.Chunk.GetType().Name -eq 'questTriggerCondition' -and $c.Chunk.TriggerAreaRef.ToString() -eq '#q302_tr_ronald_area_02'){$c.Chunk.TriggerAreaRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($markers.private_refs[0])}}
  }
 }
}
# Root owns only the admission and one private child; the private trigger lease begins at child entry.
$rootGraph=[WolvenKit.RED4.Types.questGraphDefinition]::new();Put $rootGraph (New-InputNode 0 'In1')
$parts=@();$preservedGuards=@('PostTowerFreeRoamActive','PTFRP0_DR13','q307_active','q307_done','q307_finished','q307_2079','q307_main_game_killed','q305_johnny_scene_active','q115_point_of_no_return','q000_done','q307_ep1_killed','q302_done','q302_ronald_tree')
$originalGuards=(Get-QuestNode $b0.RootChunk.Graph.Chunk 2).Condition.Chunk.Conditions
foreach($name in $preservedGuards){$found=@($originalGuards|Where-Object {$_.Chunk.GetType().Name -eq 'questFactsDBCondition' -and $_.Chunk.Type.Chunk.FactName.ToString() -eq $name});if($found.Count -ne 1){throw ('Exact existing retained-session guard missing '+$name)};$parts+=,$found[0].Chunk.DeepCopy()}
$parts+=,(Get-QuestNode $native.RootChunk.Graph.Chunk 12).Condition.Chunk.DeepCopy()
$parts+=,(New-FactCondition 'q302_ronald_message_pause' 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
$parts+=,(New-FactCondition 'PTFRQR7_RonaldNews_Issued' 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
# Conservative missing-contact deferral: unlike original startup, this future-only adapter never re-adds/notifies a historical contact.
# Generic JournalEntryState predicate serialization is proved; native contact-state semantics still require independent source review.
$journalCondition=(Get-QuestNode $sms.RootChunk.Graph.Chunk 21).Condition.Chunk.DeepCopy()
$journalType=$journalCondition.Type.Chunk
$journalType.Path=(Get-QuestNode $donor 121).Type.Chunk.Path.DeepCopy()
$journalType.State=[Enum]::Parse($journalType.State.GetType().GetGenericArguments()[0],'Active')
$parts+=,$journalCondition
Put $rootGraph (PauseNode 200 (AndCondition $parts))
Put $rootGraph (New-SetFactNode 201 'PTFRQR7_RonaldNews_Issued' 1)
$child=(Get-QuestNode $native.RootChunk.Graph.Chunk 11).DeepCopy();$child.Id=[uint16]202;foreach($s in $child.Sockets){$s.Chunk.Connections.Clear()}
# Native source phase11 has no Out1 socket because original parent keeps it permanently; explicit output is needed for bounded private lifecycle.
if(@($child.Sockets|Where-Object {$_.Chunk.Name.ToString() -eq 'Out1'}).Count -eq 0){[void](New-QuestSocket $child 'Out1' ([WolvenKit.RED4.Types.Enums+questSocketType]::Output))}
Set-RedHandleProperty $child PhaseGraph $g
$prefab=$native.RootChunk.PhasePrefabs[0].DeepCopy();$prefab.PrefabNodeRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($markers.private_parent)
[void]$child.PhaseInstancePrefabs.Add($prefab);Put $rootGraph $child
Put $rootGraph (New-SetFactNode 203 'PTFRQR7_RonaldNews_Retired' 1);Put $rootGraph (New-OutputNode 204 'Out1')
Link $rootGraph 0 Out 200 In;Link $rootGraph 200 Out 201 In;Link $rootGraph 201 Out 202 In1;Link $rootGraph 202 Out1 203 In;Link $rootGraph 203 Out 204 In
$native.RootChunk.PhasePrefabs.Clear();Set-RedHandleProperty $native.RootChunk Graph $rootGraph
$raw=Join-Path $out 'future_owner.NONPRODUCTION.questphase';$json=$raw+'.json'
Write-Cr2wFile $native $raw;Export-Cr2wJson (Read-Cr2wFile $raw) $json
$arming=@()
foreach($case in $spec.case_gates){
 $depot='towercontinued\native_gigs_u9\'+$case.quest+'_entry.questphase';$p=@($pins|Where-Object {$_.depot -ceq $depot})[0]
 if((Get-FileHash -LiteralPath $p.raw).Hash -cne $p.raw_sha256){throw 'Pinned U9 entry changed'}
 $file=Read-Cr2wFile $p.raw;$entry=(Get-QuestNode $file.RootChunk.Graph.Chunk 50).PhaseGraph.Chunk
 if(@($entry.Nodes|Where-Object {$_.Chunk.Id.ToString() -eq '65007'}).Count){throw 'New local arming ID collides'}
 $from=Get-QuestSocket (Get-QuestNode $entry 65002) Out;$to=Get-QuestSocket (Get-QuestNode $entry 65003) In
 $links=@($from.Connections|Where-Object {[object]::ReferenceEquals($_.Chunk.Destination.Chunk,$to)})
 if($links.Count -ne 1){throw 'Exact fresh admission to ParentEntered route changed'}
 $connection=$links[0].Chunk
 foreach($socket in @($from,$to)){
  for($j=$socket.Connections.Count-1;$j -ge 0;$j--){if([object]::ReferenceEquals($socket.Connections[$j].Chunk,$connection)){$socket.Connections.RemoveAt($j)}}
 }
 $armFact='PTFRQR7_RonaldNews_Armed_'+$case.quest;Put $entry (New-SetFactNode 65007 $armFact 1)
 Link $entry 65002 Out 65007 In;Link $entry 65007 Out 65003 In
 $entryRaw=Join-Path $out ($case.quest+'_entry.NONPRODUCTION.questphase');$entryJson=$entryRaw+'.json'
 Write-Cr2wFile $file $entryRaw;Export-Cr2wJson (Read-Cr2wFile $entryRaw) $entryJson
 $arming+=@{quest_id=$case.quest;intended_depot=$depot;source=$p;graph='root/50';added_id=65007;private_fact=$armFact;raw=$entryRaw;raw_sha256=(Get-FileHash -LiteralPath $entryRaw).Hash;json=$entryJson;json_sha256=(Get-FileHash -LiteralPath $entryJson).Hash}
}
@{status='PRIVATE_FUTURE_ONLY_PROPOSAL_REQUIRES_INDEPENDENT_SOURCE_APPROVAL';native=$nativePin;b0=$b0Pin;sms=$smsPin;markers=(Join-Path $homeDir 'experiments/markers_04/NOT_FOR_INTEGRATION.json');spec=(Join-Path $homeDir 'future_protocol_spec_01.json');raw=$raw;raw_sha256=(Get-FileHash -LiteralPath $raw).Hash;json=$json;json_sha256=(Get-FileHash -LiteralPath $json).Hash;intended_depot='towercontinued\quest_restoration_qr7\ronald_news_future.questphase';arming_producers=$arming;private_receipts=@('PTFRQR7_RonaldNews_Issued','PTFRQR7_RonaldNews_Retired');not_proven=@('native contact-state predicate applicability','full native/external global-ID and phase-registration collision inventory','engine save-transition fixtures','new private trigger streaming runtime');production_changes=0;registered=$false}|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $out 'NOT_FOR_INTEGRATION.json') -Encoding utf8
Write-Output 'Private future-only4-branch owner serialized/read back; unregistered'
