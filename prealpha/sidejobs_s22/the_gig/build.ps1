# Definitions only. Caller supplies native graph helpers and journal builders.
function New-S22TheGigGraph {
 param([string]$WorkspaceRoot,[System.Collections.IDictionary]$Common)
 $spec=Get-Content -LiteralPath (Join-Path $WorkspaceRoot 'prealpha/sidejobs_s22/the_gig/contract.json') -Raw|ConvertFrom-Json
 $source=(Read-Cr2wFile (Join-Path $WorkspaceRoot $spec.native_source)).RootChunk.Graph.Chunk
 $g=[WolvenKit.RED4.Types.questGraphDefinition]::new()
 foreach($id in $spec.selected_nodes){$n=(Get-QuestNode $source $id).DeepCopy();ClearB5 $n;AddNodeB5 $g $n}
 function Guard([bool]$ack){
  $pairs=[ordered]@{};foreach($k in $Common.Keys){$pairs[$k]=$Common[$k]}
  foreach($p in $spec.facts_equal.PSObject.Properties){$pairs[$p.Name]=$p.Value}
  $pairs[$spec.tag+'_Issued']=[int]$ack;$pairs[$spec.tag+'_Finished']=0;$pairs[$spec.tag+'_Fault']=0
  if(!$ack){$pairs[$spec.tag+'_Permit']=1}
  $c=AllB5 $pairs
  foreach($j in $spec.journals){
   $states=if($ack -and $j.path -in $spec.reactivate_paths){@(2)}else{@($j.states)}
   $or=[WolvenKit.RED4.Types.questLogicalCondition]::new();$or.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::OR
   foreach($v in $states){$s=@('','Inactive','Active','Succeeded','Failed')[[int]$v];Add-RedHandle $or.Conditions (S22BoxingJournalState $j.path $j.class $s)}
   Add-RedHandle $c.Conditions $or
  };return $c
 }
 foreach($n in @((New-SetFactNode 1000 ($spec.tag+'_Ready') 1),(PauseB5 1001 (Guard $false)),(New-ConditionNode 1002 (Guard $false)),(New-SetFactNode 1003 ($spec.tag+'_Issued') 1),(New-SetFactNode 1004 ($spec.tag+'_Finished') 1),(New-SetFactNode 1005 ($spec.tag+'_Refused') 1),(S22BoxingJournalNode 1006 'quests/side_quest/sq_q001_wakako/wakako' 'gameJournalQuestPhase'),(PauseB5 1007 (Guard $true)),(New-ConditionNode 1008 (Guard $true)))){AddNodeB5 $g $n}
 $edges=@(EdgesB5 $source|ForEach-Object {$_}|Where-Object {$_[0] -in $spec.selected_nodes -and $_[2] -in $spec.selected_nodes -and $_[0] -ne 0 -and $_[0] -ne 15 -and -not($_[0] -eq 27 -and $_[2] -eq 1)})
 $edges+=,@(0,'Out',1000,'In');$edges+=,@(1000,'Out',1001,'In');$edges+=,@(1001,'Out',1002,'In')
 $edges+=,@(1002,'True',1003,'In');$edges+=,@(1002,'False',1005,'In');$edges+=,@(1003,'Out',25,'In')
 $edges+=,@(2,'Out',1006,'Active');$edges+=,@(1006,'Out',15,'Active');$edges+=,@(15,'Out',1007,'In')
 $edges+=,@(1007,'Out',1008,'In');$edges+=,@(1008,'True',30,'In');$edges+=,@(1008,'False',1005,'In')
 $edges+=,@(27,'Out',1004,'In');$edges+=,@(1004,'Out',1,'In')
 RebuildB5 $g $edges
 return @{graph=$g;spec=$spec;depot=$spec.depot}
}
