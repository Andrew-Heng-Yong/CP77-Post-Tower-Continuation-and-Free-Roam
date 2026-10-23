# Definitions only. Caller loads the ordinary phase2a and B5 graph helpers.
function S23AJournalPath($path,$class){$p=[WolvenKit.RED4.Types.gameJournalPath]::new();$p.RealPath=$path;$p.ClassName=$class;$p.FileEntryIndex=2;return $p}
function S23AJournalState($path,$class,$state){
 $t=[WolvenKit.RED4.Types.questJournalEntryState_ConditionType]::new();Set-RedHandleProperty $t Path (S23AJournalPath $path $class);$t.State=[Enum]::Parse([WolvenKit.RED4.Types.Enums+gameJournalEntryState],$state)
 $c=[WolvenKit.RED4.Types.questJournalCondition]::new();Set-RedHandleProperty $c Type $t;return $c
}
function S23AJournalNode($id,$path,$class){
 $n=[WolvenKit.RED4.Types.questJournalNodeDefinition]::new();$n.Id=[uint16]$id
 $t=[WolvenKit.RED4.Types.questJournalQuestEntry_NodeType]::new();Set-RedHandleProperty $t Path (S23AJournalPath $path $class);$t.SendNotification=$false;$t.TrackQuest=$false;Set-RedHandleProperty $n Type $t
 foreach($p in @('Active','Inactive','Succeeded','Failed')){[void](New-QuestSocket $n $p ([WolvenKit.RED4.Types.Enums+questSocketType]::Input))};[void](New-QuestSocket $n 'Out' ([WolvenKit.RED4.Types.Enums+questSocketType]::Output));return $n
}
function New-S23BaseAResumeGraph {
 param([string]$WorkspaceRoot,[System.Collections.IDictionary]$Common,[string]$Id)
 $spec=@((Get-Content -LiteralPath (Join-Path $PSScriptRoot 'contract.json') -Raw|ConvertFrom-Json).owners|Where-Object tag -EQ $Id)
 if($spec.Count -ne 1){throw 'Unknown or ambiguous S23 base_a job'};$spec=$spec[0]
 $native=(Read-Cr2wFile (Join-Path $WorkspaceRoot $spec.native_source)).RootChunk.Graph.Chunk
 $g=[WolvenKit.RED4.Types.questGraphDefinition]::new()
 foreach($idn in $spec.selected_nodes){$old=Get-QuestNode $native $idn;$n=$old.DeepCopy();ClearB5 $n;if($n -is [WolvenKit.RED4.Types.questPhaseNodeDefinition] -and $null -ne $n.PhaseGraph -and $null -ne $n.PhaseGraph.Chunk){RewireB5 $n.PhaseGraph.Chunk $old.PhaseGraph.Chunk};AddNodeB5 $g $n}

 $target=Get-QuestNode $g 21;$target.PhaseResource=[WolvenKit.RED4.Types.CResourceAsyncReference[WolvenKit.RED4.Types.questQuestPhaseResource]]::new($spec.resume_depot)
 $tag=$spec.tag
 function Guard([bool]$ack){
  $pairs=[ordered]@{};foreach($k in $Common.Keys){$pairs[$k]=$Common[$k]};foreach($p in $spec.facts_equal.PSObject.Properties){$pairs[$p.Name]=$p.Value}
  $pairs[$tag+'_Issued']=[int]$ack;$pairs[$tag+'_Finished']=0;$pairs[$tag+'_Fault']=0
  if(!$ack){$pairs[$tag+'_Permit']=1}
  if($null -ne $spec.phone_dependency){$pairs[$spec.phone_dependency]=1}
  $c=AllB5 $pairs
  foreach($r in $spec.fact_ranges.PSObject.Properties){Add-RedHandle $c.Conditions (New-FactCondition $r.Name $r.Value.min 'GreaterOrEqual');Add-RedHandle $c.Conditions (New-FactCondition $r.Name $r.Value.max 'LessOrEqual')}
  foreach($j in $spec.journals){
   $or=[WolvenKit.RED4.Types.questLogicalCondition]::new();$or.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::OR
   foreach($v in $j.states){
    if($ack -and $j.path -eq $spec.root -and $v -eq 4){continue}
    $stateName=@('','Inactive','Active','Succeeded','Failed')[[int]$v]
    if($ack -and $j.path -eq $spec.root -and $v -eq 1){$and=AllB5 ([ordered]@{($tag+'_RootReactivated')=0});Add-RedHandle $and.Conditions (S23AJournalState $j.path $j.class $stateName);Add-RedHandle $or.Conditions $and}else{Add-RedHandle $or.Conditions (S23AJournalState $j.path $j.class $stateName)}
   }
   if($ack -and $j.path -eq $spec.root){$and=AllB5 ([ordered]@{($tag+'_RootReactivated')=1});Add-RedHandle $and.Conditions (S23AJournalState $j.path $j.class 'Active');Add-RedHandle $or.Conditions $and}
   Add-RedHandle $c.Conditions $or
  }
  if($spec.key -eq 'MQ007_RESUME'){
   $src=(Read-Cr2wFile (Join-Path $WorkspaceRoot 'research/activity_state_r3/native_sources/raw/base/quest/minor_quests/mq007/mq007.questphase')).RootChunk.Graph.Chunk
   $inv=(Get-QuestNode $src 11).Condition.Chunk.DeepCopy();Add-RedHandle $c.Conditions $inv
  };return $c
 }
 foreach($n in @((New-SetFactNode 1000 ($tag+'_Ready') 1),(PauseB5 1001 (Guard $false)),(New-ConditionNode 1002 (Guard $false)),(New-SetFactNode 1003 ($tag+'_Issued') 1),(New-ConditionNode 1004 (S23AJournalState $spec.root 'gameJournalQuest' 'Failed')),(S23AJournalNode 1005 $spec.root 'gameJournalQuest'),(New-SetFactNode 1006 ($tag+'_RootReactivated') 1),(PauseB5 1007 (Guard $true)),(New-ConditionNode 1008 (Guard $true)),(New-SetFactNode 1009 ($tag+'_Refused') 1),(PauseB5 1010 (S23AJournalState $spec.root 'gameJournalQuest' 'Succeeded')),(New-SetFactNode 1011 ($tag+'_Finished') 1))){AddNodeB5 $g $n}
 $edges=@();foreach($e in $spec.native_edges){if($e[0] -ne 0 -and $e[2] -notin $spec.target_nodes){$edges+=,@($e[0],$e[1],$e[2],$e[3])}}
 $edges+=,@(0,'Out',1000,'In');$edges+=,@(1000,'Out',1001,'In');$edges+=,@(1001,'Out',1002,'In');$edges+=,@(1002,'True',1003,'In');$edges+=,@(1002,'False',1009,'In')
 $edges+=,@(1003,'Out',1004,'In');$edges+=,@(1004,'True',1005,'Active');$edges+=,@(1005,'Out',1006,'In');$edges+=,@(1006,'Out',1007,'In');$edges+=,@(1004,'False',1007,'In');$edges+=,@(1007,'Out',1008,'In');$edges+=,@(1008,'False',1009,'In')
 foreach($e in $spec.native_edges){if($e[0] -eq 0){$edges+=,@(1008,'True',$e[2],$e[3])}}
 # Parent native prerequisites may wait. Revalidate after their wait and before
 # any original quest owner starts; no Permit dependency survives Issued.
 $gate=1100
 foreach($target in $spec.target_nodes){
  AddNodeB5 $g (New-ConditionNode $gate (Guard $true));AddNodeB5 $g (New-SetFactNode ($gate+1) ($tag+'_Entered_'+$target) 1)
  foreach($e in $spec.native_edges){if($e[2] -eq $target){$edges+=,@($e[0],$e[1],$gate,'In');$edges+=,@(($gate+1),'Out',$target,$e[3])}}
  $edges+=,@($gate,'True',($gate+1),'In');$edges+=,@($gate,'False',1009,'In');$edges+=,@(($gate+1),'Out',1010,'In');$gate+=2
 }
 $edges+=,@(1010,'Out',1011,'In');RebuildB5 $g $edges
 return @{graph=$g;spec=$spec;depot=$spec.depot}
}
