# Dot-source only after build_phase2a.ps1 -HelpersOnly and B5 graph helpers.
# Caller owns packing, injection collision checks, compilation and installation.
function S22BoxingJournalPath($path,$class){
 $p=[WolvenKit.RED4.Types.gameJournalPath]::new();$p.RealPath=$path;$p.ClassName=$class;$p.FileEntryIndex=2;return $p
}
function S22BoxingJournalState($path,$class,$state){
 $t=[WolvenKit.RED4.Types.questJournalEntryState_ConditionType]::new();Set-RedHandleProperty $t Path (S22BoxingJournalPath $path $class);$t.State=[Enum]::Parse([WolvenKit.RED4.Types.Enums+gameJournalEntryState],$state)
 $c=[WolvenKit.RED4.Types.questJournalCondition]::new();Set-RedHandleProperty $c Type $t;return $c
}
function S22BoxingJournalNode($id,$path,$class){
 $n=[WolvenKit.RED4.Types.questJournalNodeDefinition]::new();$n.Id=[uint16]$id
 $t=[WolvenKit.RED4.Types.questJournalQuestEntry_NodeType]::new();Set-RedHandleProperty $t Path (S22BoxingJournalPath $path $class);$t.SendNotification=$false;$t.TrackQuest=$false;Set-RedHandleProperty $n Type $t
 foreach($port in @('Active','Inactive','Succeeded','Failed')){[void](New-QuestSocket $n $port ([WolvenKit.RED4.Types.Enums+questSocketType]::Input))}
 [void](New-QuestSocket $n 'Out' ([WolvenKit.RED4.Types.Enums+questSocketType]::Output));return $n
}
function New-S22BoxingGraph {
 param([string]$WorkspaceRoot,[System.Collections.IDictionary]$Common)
 $spec=Get-Content -LiteralPath (Join-Path $WorkspaceRoot 'prealpha/sidejobs_s22/boxing/contract.json') -Raw|ConvertFrom-Json
 $native=(Read-Cr2wFile (Join-Path $WorkspaceRoot $spec.native_source)).RootChunk.Graph.Chunk
 $g=[WolvenKit.RED4.Types.questGraphDefinition]::new()
 foreach($id in $spec.selected_nodes){
  $old=Get-QuestNode $native $id;$n=$old.DeepCopy();ClearB5 $n
  if($n -is [WolvenKit.RED4.Types.questPhaseNodeDefinition] -and $null -ne $n.PhaseGraph -and $null -ne $n.PhaseGraph.Chunk){RewireB5 $n.PhaseGraph.Chunk $old.PhaseGraph.Chunk};AddNodeB5 $g $n
 }
 $pairs=[ordered]@{};foreach($k in $Common.Keys){$pairs[$k]=$Common[$k]}
 foreach($p in $spec.fact_equal.PSObject.Properties){if($pairs.Contains($p.Name)){throw 'Duplicate common/native guard'};$pairs[$p.Name]=$p.Value}
 $tag=$spec.tag;$pairs[$tag+'_Permit']=1;$pairs[$tag+'_Issued']=0;$pairs[$tag+'_Finished']=0;$pairs[$tag+'_Fault']=0
 function Guard {
  $c=AllB5 $pairs
  foreach($j in $spec.journals){
   $or=[WolvenKit.RED4.Types.questLogicalCondition]::new();$or.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::OR
   foreach($s in $j.states){Add-RedHandle $or.Conditions (S22BoxingJournalState $j.path $j.class $s)}
   Add-RedHandle $c.Conditions $or
  };return $c
 }
 foreach($n in @((New-SetFactNode 1000 ($tag+'_Ready') 1),(PauseB5 1001 (Guard)),(New-ConditionNode 1002 (Guard)),(New-SetFactNode 1003 ($tag+'_Issued') 1),(New-SetFactNode 1004 ($tag+'_Finished') 1),(New-SetFactNode 1005 ($tag+'_Refused') 1))){AddNodeB5 $g $n}
 $j0=$spec.journal_writes[0];$j1=$spec.journal_writes[1]
 AddNodeB5 $g (S22BoxingJournalNode 1006 $j0.path $j0.class)
 AddNodeB5 $g (S22BoxingJournalNode 1007 $j1.path $j1.class)
 function JournalAck {
  $ack=[ordered]@{};foreach($k in $Common.Keys){$ack[$k]=$Common[$k]}
  foreach($p in $spec.fact_equal.PSObject.Properties){$ack[$p.Name]=$p.Value}
  $ack[$tag+'_Issued']=1;$ack[$tag+'_Finished']=0;$ack[$tag+'_Fault']=0
  $c=AllB5 $ack
  foreach($j in $spec.journal_writes){Add-RedHandle $c.Conditions (S22BoxingJournalState $j.path $j.class 'Active')}
  foreach($j in @($spec.journals|Where-Object {$_.path -notin @($j0.path,$j1.path)})){
   $or=[WolvenKit.RED4.Types.questLogicalCondition]::new();$or.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::OR
   foreach($s in $j.states){Add-RedHandle $or.Conditions (S22BoxingJournalState $j.path $j.class $s)}
   Add-RedHandle $c.Conditions $or
  };return $c
 }
 AddNodeB5 $g (PauseB5 1008 (JournalAck));AddNodeB5 $g (New-ConditionNode 1009 (JournalAck))
 $edges=@(EdgesB5 $native|ForEach-Object {$_}|Where-Object {$_[0] -in $spec.selected_nodes -and $_[2] -in $spec.selected_nodes -and $_[0] -ne 0 -and -not($_[0] -eq 25 -and $_[2] -eq 1)})
 $edges+=,@(0,'Out',1000,'In');$edges+=,@(1000,'Out',1001,'In');$edges+=,@(1001,'Out',1002,'In')
 $edges+=,@(1002,'True',1003,'In');$edges+=,@(1002,'False',1005,'In');$edges+=,@(1003,'Out',1006,'Active')
 $edges+=,@(1006,'Out',1007,'Active');$edges+=,@(1007,'Out',1008,'In');$edges+=,@(1008,'Out',1009,'In')
 $edges+=,@(1009,'True',55,'In1');$edges+=,@(1009,'False',1005,'In')
 $edges+=,@(25,'Out1',1004,'In');$edges+=,@(1004,'Out',1,'In')
 RebuildB5 $g $edges
 return @{graph=$g;spec=$spec;guard_equal=$pairs;depot='towercontinued\sidejobs_s22\mq025_progress.questphase'}
}
