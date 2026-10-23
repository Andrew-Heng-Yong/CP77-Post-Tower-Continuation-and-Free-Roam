param([string]$Revision='ep1_01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly
$helper=Get-Content (Join-Path $ws 'tools/build_fresh_gigs_b5.ps1') -Raw
$begin=$helper.IndexOf('function ClearB5(');$end=$helper.IndexOf('$allRoots=@{};')
if($begin -lt 0 -or $end -le $begin){throw 'Helper boundary changed'}
. ([scriptblock]::Create($helper.Substring($begin,$end-$begin)))
if($Revision -cnotmatch '^ep1_\d{2}$'){throw 'Invalid revision'}
$out=Join-Path $PSScriptRoot ('build/'+$Revision)
if(Test-Path -LiteralPath $out){throw 'Immutable component exists'}
New-Item -ItemType Directory $out,(Join-Path $out 'source'),(Join-Path $out 'readback')|Out-Null
$rel='research/activity_state_r3/native_sources/raw/ep1/quest/main_quests/q304/phases/q304_car_retrieval.questphase'
$original=(Read-Cr2wFile (Join-Path $ws $rel)).RootChunk.Graph.Chunk
$g=[WolvenKit.RED4.Types.questGraphDefinition]::new()
# Accepted invitation is completed history. Never re-enter its messages, and
# never increment the pre-existing active/started facts a second time.
$excluded=@(2,252,253)
foreach($h in $original.Nodes){
 $old=$h.Chunk;if([int]::Parse($old.Id.ToString()) -in $excluded){continue}
 $n=$old.DeepCopy();ClearB5 $n
 if($n -is [WolvenKit.RED4.Types.questPhaseNodeDefinition] -and $null -ne $n.PhaseGraph -and $null -ne $n.PhaseGraph.Chunk){RewireB5 $n.PhaseGraph.Chunk $old.PhaseGraph.Chunk}
 AddNodeB5 $g $n
}
$edges=@(EdgesB5 $original|ForEach-Object {$_}|Where-Object {$_[0] -notin $excluded -and $_[2] -notin $excluded})
$edges+=,@(0,'Out',115,'In1')
# Exact consumers of the original messages-phase Out1. All later gameplay,
# native SMS, combat, vehicle reward and cleanup payloads remain original.
foreach($e in @(EdgesB5 $original|ForEach-Object {$_}|Where-Object {$_[0] -eq 2 -and $_[1] -eq 'Out1'})){
 $edges+=,@(115,'Out1',$e[2],$e[3])
}
RebuildB5 $g $edges
$root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();Set-RedHandleProperty $root Graph $g
$f=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$f.RootChunk=$root
$depot='towercontinued\sidejobs_s22\moving_heat_resume.questphase'
$raw=Join-Path (Join-Path $out 'source') $depot
Write-Cr2wFile $f $raw
Export-Cr2wJson (Read-Cr2wFile $raw) (Join-Path $out 'readback/moving_heat_resume.json')
$spec=Get-Content (Join-Path $PSScriptRoot 'admission.json') -Raw|ConvertFrom-Json
$states=@{1='Inactive';2='Active';3='Succeeded';4='Failed'}
function JournalStateS22($path,$class,$state){
 $p=[WolvenKit.RED4.Types.gameJournalPath]::new();$p.RealPath=$path;$p.ClassName=$class;$p.FileEntryIndex=2
 $t=[WolvenKit.RED4.Types.questJournalEntryState_ConditionType]::new();Set-RedHandleProperty $t Path $p;$t.State=[Enum]::Parse([WolvenKit.RED4.Types.Enums+gameJournalEntryState],$state);$t.Inverted=$false
 $c=[WolvenKit.RED4.Types.questJournalCondition]::new();Set-RedHandleProperty $c Type $t;return $c
}
$persistent=(Read-Cr2wFile (Join-Path $ws 'research/q307_extracted/raw/ep1/quest/ep1_persistent_content.questphase')).RootChunk.Graph.Chunk
$nativeParent=NestedB5 $persistent @(30,6)
function GuardS22([bool]$post){
 $pairs=[ordered]@{}
 foreach($o in @($spec.common_guard_equal,$spec.guard_equal)){foreach($p in $o.PSObject.Properties){$pairs[$p.Name]=[int]$p.Value}}
 $pairs['PTFRS22_Q304_Issued']=[int]$post;$pairs['PTFRS22_Q304_Finished']=0;$pairs['PTFRS22_Q304_Fault']=0
 if(!$post){$pairs['PTFRS22_Q304_Permit']=1}
 $c=AllB5 $pairs
 foreach($j in $spec.journal_guards){
  $state=[int]$j.state
  if($post -and $state -eq 4){$state=2}
  if(!$post -and 'allowed_states' -in $j.PSObject.Properties.Name){
   $either=[WolvenKit.RED4.Types.questLogicalCondition]::new();$either.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::OR
   foreach($s in $j.allowed_states){Add-RedHandle $either.Conditions (JournalStateS22 $j.path $j.class $states[[int]$s])}
   Add-RedHandle $c.Conditions $either
  }else{Add-RedHandle $c.Conditions (JournalStateS22 $j.path $j.class $states[$state])}
 }
 # Retain the original story availability gate, but not its already-consumed
 # invitation content-token wait.
 Add-RedHandle $c.Conditions ((Get-QuestNode $nativeParent 2).Condition.Chunk.DeepCopy())
 foreach($ref in $spec.outside_triggers){$t=(Get-QuestNode $original 162).Condition.Chunk.DeepCopy();$t.TriggerAreaRef=$ref;Add-RedHandle $c.Conditions $t}
 return $c
}
$messages=(Read-Cr2wFile (Join-Path $ws 'research/activity_state_r3/native_sources/raw/ep1/quest/main_quests/q304/phases/subphases/q304_car_retrieval_messages.questphase')).RootChunk.Graph.Chunk
$bg=[WolvenKit.RED4.Types.questGraphDefinition]::new()
foreach($n in @((New-InputNode 0 'In1'),(New-SetFactNode 1 'PTFRS22_Q304_Ready' 1),(PauseB5 2 (GuardS22 $false)),(New-ConditionNode 3 (GuardS22 $false)),(New-SetFactNode 4 'PTFRS22_Q304_Issued' 1),(New-ConditionNode 9 (GuardS22 $true)),(New-SetFactNode 11 'PTFRS22_Q304_Finished' 1),(New-SetFactNode 12 'PTFRS22_Q304_Fault' 1))){AddNodeB5 $bg $n}
$jid=5
foreach($j in $spec.reactivate){
 $n=(Get-QuestNode $messages 65).DeepCopy();ClearB5 $n;$n.Id=[uint16]$jid
 $n.Type.Chunk.Path.Chunk.RealPath=$j.path;$n.Type.Chunk.Path.Chunk.ClassName=$j.class
 AddNodeB5 $bg $n;$jid++
}
$delay=(Get-QuestNode $original 250).DeepCopy();ClearB5 $delay;$delay.Id=[uint16]8
$delay.Condition.Chunk.Type.Chunk.Seconds=[uint32]0;$delay.Condition.Chunk.Type.Chunk.Miliseconds=[uint32]100
AddNodeB5 $bg $delay
$child=(Get-QuestNode $original 2).DeepCopy();ClearB5 $child;$child.Id=[uint16]10
$child.PhaseResource=[WolvenKit.RED4.Types.CResourceAsyncReference[WolvenKit.RED4.Types.questQuestPhaseResource]]::new($depot)
AddNodeB5 $bg $child
RebuildB5 $bg @(@(0,'Out',1,'In'),@(1,'Out',2,'In'),@(2,'Out',3,'In'),@(3,'False',2,'In'),@(3,'True',4,'In'),@(4,'Out',5,'Active'),@(5,'Out',6,'Active'),@(6,'Out',7,'Active'),@(7,'Out',8,'In'),@(8,'Out',9,'In'),@(9,'False',12,'In'),@(9,'True',10,'In1'),@(10,'Out1',11,'In'))
$br=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();Set-RedHandleProperty $br Graph $bg
$bf=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$bf.RootChunk=$br
$boot='towercontinued\sidejobs_s22\moving_heat_boot.questphase';$bootRaw=Join-Path (Join-Path $out 'source') $boot
Write-Cr2wFile $bf $bootRaw;Export-Cr2wJson (Read-Cr2wFile $bootRaw) (Join-Path $out 'readback/moving_heat_boot.json')
$pins=[ordered]@{}
foreach($p in @('prealpha/sidejobs_s22/ep1_jobs/build_component.ps1','prealpha/sidejobs_s22/ep1_jobs/admission.json','tools/build_phase2a.ps1','tools/build_fresh_gigs_b5.ps1',$rel,($rel.Replace('/raw/','/json/')+'.json'),'research/q307_extracted/raw/ep1/quest/ep1_persistent_content.questphase','research/activity_state_r3/native_sources/raw/ep1/quest/main_quests/q304/phases/subphases/q304_car_retrieval_messages.questphase')){$pins[$p]=(Get-FileHash -LiteralPath (Join-Path $ws $p)).Hash}
$result=[ordered]@{status='COMPONENT_ONLY_NOT_ADMITTED_OR_INSTALLED';depot=$depot;sha256=(Get-FileHash -LiteralPath $raw).Hash;boot=$boot;boot_sha256=(Get-FileHash -LiteralPath $bootRaw).Hash;excluded_native_nodes=$excluded;added_edges=@(@(0,'Out',115,'In1'),@(115,'Out1',164,'In'),@(115,'Out1',65,'In1'),@(115,'Out1',325,'In1'));source_pins=$pins;entry='In1';output='Out1';requires='S22 runtime grants PTFRS22_Q304_Permit only after common safe stable guards. Boot independently rechecks exact state, issues once, activates only Failed root/phase/firstdoor, verifies preserved progress before child. Not safe for any other state.';native_scenes_rewards_cleanup_preserved=$true;native_progress_reset=$false}
[IO.File]::WriteAllText((Join-Path $out 'component.json'),($result|ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false))
$result|ConvertTo-Json -Depth 6
