Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$W=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $W 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $W 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$helper=Get-Content -LiteralPath (Join-Path $W 'tools/build_fresh_gigs_b5.ps1') -Raw
$begin=$helper.IndexOf('function ClearB5(');$end=$helper.IndexOf('$allRoots=@{};')
if($begin -lt 0 -or $end -le $begin){throw 'Helper boundaries changed'}
. ([scriptblock]::Create($helper.Substring($begin,$end-$begin)))
$O=Join-Path $PSScriptRoot 'native_02';if(Test-Path $O){throw 'Use successor'}
New-Item -ItemType Directory -Path $O,(Join-Path $O 'source'),(Join-Path $O 'readback')|Out-Null
$inventory=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'research_01/inventory.json') -Raw|ConvertFrom-Json
$pins=[ordered]@{};$resources=[ordered]@{}
function Source([string]$archive,[string]$depot){
 $row=@($inventory|Where-Object {($_.archive -replace '\\','/').EndsWith('/'+$archive) -and $_.depot -ceq $depot})
 if($row.Count -ne 1){throw ('Ambiguous source '+$depot)}
 $p=Join-Path $W $row[0].raw;if((Get-FileHash $p).Hash -cne $row[0].sha256){throw 'Source changed'}
 $pins[$row[0].raw]=$row[0].sha256;return (Read-Cr2wFile $p).RootChunk
}
function CopyNode($g,$s,[int]$id,[int]$newid=-1){
 $original=Get-QuestNode $s $id;$n=$original.DeepCopy();ClearB5 $n
 if($n -is [WolvenKit.RED4.Types.questPhaseNodeDefinition] -and $null -ne $n.PhaseGraph -and $null -ne $n.PhaseGraph.Chunk){RewireB5 $n.PhaseGraph.Chunk $original.PhaseGraph.Chunk}
 if($newid -ge 0){$n.Id=[uint16]$newid};AddNodeB5 $g $n
}
function Save($root,[string]$depot){
 $f=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$f.RootChunk=$root
 $p=Join-Path (Join-Path $O 'source') $depot;Write-Cr2wFile $f $p
 Export-Cr2wJson (Read-Cr2wFile $p) (Join-Path (Join-Path $O 'readback') ($depot.Replace('\','_')+'.json'))
 $resources[$depot]=(Get-FileHash $p).Hash
}
function Any($conditions){$c=[WolvenKit.RED4.Types.questLogicalCondition]::new();$c.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::OR;foreach($v in $conditions){Add-RedHandle $c.Conditions $v};return $c}
function Journal([string]$state){
 $p=[WolvenKit.RED4.Types.gameJournalPath]::new();$p.RealPath='quests/minor_quest/mq038_neweridentity';$p.ClassName='gameJournalQuest';$p.FileEntryIndex=2
 $t=[WolvenKit.RED4.Types.questJournalEntryState_ConditionType]::new();Set-RedHandleProperty $t Path $p;$t.State=[Enum]::Parse([WolvenKit.RED4.Types.Enums+gameJournalEntryState],$state)
 $c=[WolvenKit.RED4.Types.questJournalCondition]::new();Set-RedHandleProperty $c Type $t;return $c
}
$common=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;PTFRPA2_Finished=1;PTFRPA2_Fault=0;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;q307_active=0;q307_debug_reset=0;q115_point_of_no_return=0;q305_johnny_scene_active=0;PTFRU9_Support_Issued=1;PTFRU9_Support_Fault=0;PTFRS23_MQ038_Fault=0;PTFRS23_MQ038_Finished=0;PTFRJD1_Dennis_Issued=0;mq038_done=0;holo_setup_active=0;holo_setup_started=0;holo_reset=0;holo_force_reset=0;holo_reset_soft=0;holo_dennis_calls_v_end_activate=0}
function Admission {
 $c=AllB5 $common
 $fresh=AllB5 ([ordered]@{PTFRS23_MQ038_Permit=1;PTFRS23_MQ038_Issued=0;PTFRS23_MQ038_Entered=0;holo_interrupt_call=0;holo_active_call_interrupted=0;holo_interrupt_call_manual=0;holo_interrupt_braindance=0})
 Add-RedHandle $fresh.Conditions (Journal 'Inactive')
 $existing=AllB5 ([ordered]@{PTFRS23_MQ038_Issued=1;PTFRS23_MQ038_Entered=1})
 Add-RedHandle $existing.Conditions (Any @((Journal 'Inactive'),(Journal 'Active')))
 Add-RedHandle $c.Conditions (Any @($fresh,$existing))
 # Existing MQ038 may itself hold holo_interrupt_call_manual until call_out.
# Listener restoration must not wait on that call-completion side effect.
# A queued incoming start request is deliberately preserved and permitted.
 # The untouched native controller consumes it; no call/quest fact is reset here.
 return $c
}
$init=(Source 'basegame_4_gamedata.archive' 'base\quest\holocalls\holocall_initializers.questphase').Graph.Chunk
$g=[WolvenKit.RED4.Types.questGraphDefinition]::new();CopyNode $g $init 106
foreach($n in @((New-InputNode 1000 'In1'),(New-SetFactNode 1001 'PTFRJD1_Dennis_Ready' 1),(PauseB5 1002 (Admission)),(New-ConditionNode 1003 (Admission)),(New-SetFactNode 1004 'PTFRJD1_Dennis_Issued' 1))){AddNodeB5 $g $n}
RebuildB5 $g @(@(1000,'Out',1001,'In'),@(1001,'Out',1002,'In'),@(1002,'Out',1003,'In'),@(1003,'False',1002,'In'),@(1003,'True',1004,'In'),@(1004,'Out',106,'In1'))
$root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();Set-RedHandleProperty $root Graph $g
$boot='towercontinued\judy_dennis_jd1\dennis_phone.questphase';Save $root $boot

$mq=Source '0000_TowerContinued_SideJobs_S23.archive' 'towercontinued\sidejobs_s23\base_b\mq038.questphase'
$dependency=Get-QuestNode $mq.Graph.Chunk 1003
if($dependency.GetType().Name -cne 'questPauseConditionNodeDefinition'){throw 'Saved dependency node changed'}
$c=$dependency.Condition.Chunk.DeepCopy();if($c.GetType().Name -cne 'questLogicalCondition'){throw 'Unexpected dependency'}
Add-RedHandle $c.Conditions (New-FactCondition 'PTFRJD1_Dennis_Issued' 1 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
Set-RedHandleProperty $dependency Condition $c
Save $mq 'towercontinued\sidejobs_s23\base_b\mq038.questphase'

$old=Source '00000000_TowerContinued_SideJobs_S29.archive' 'towercontinued\gig_phone_u9\fixer_cleanup.questphase'
$native=(Source 'basegame_4_gamedata.archive' 'base\quest\holocalls\holocall_cleanup.questphase').Graph.Chunk
$g=[WolvenKit.RED4.Types.questGraphDefinition]::new()
foreach($n in $old.Graph.Chunk.Nodes){CopyNode $g $old.Graph.Chunk ([int]$n.Chunk.Id.ToString())}
$edges=@(EdgesB5 $old.Graph.Chunk|ForEach-Object {$_});$count=0
foreach($e in $edges){if($e[0] -in @(1255,1210,1211) -and $e[2] -eq 6){$e[2]=1300;$e[3]='In';$count++}}
if($count -ne 3){throw 'Current cleanup boundary changed'}
AddNodeB5 $g (New-ConditionNode 1300 (AllB5 ([ordered]@{PTFRJD1_Dennis_Issued=1})))
CopyNode $g $native 439 1301;CopyNode $g $native 303 1302
$edges+=,@(1300,'False',6,'In2');$edges+=,@(1300,'True',1301,'In');$edges+=,@(1301,'False',6,'In2');$edges+=,@(1301,'True',1302,'In13');$edges+=,@(1302,'Out13',6,'In2')
RebuildB5 $g $edges;Set-RedHandleProperty $old Graph $g;Save $old 'towercontinued\gig_phone_u9\fixer_cleanup.questphase'
@{status='BUILT_NOT_INSTALLED';resources=$resources;boots=@($boot);source_pins=$pins;common=$common;game_writes=0;save_writes=0}|ConvertTo-Json -Depth 15|Set-Content -LiteralPath (Join-Path $O 'component.json') -Encoding utf8
@{resources=$resources.Count;boots=1;status='BUILT_NOT_INSTALLED'}|ConvertTo-Json
