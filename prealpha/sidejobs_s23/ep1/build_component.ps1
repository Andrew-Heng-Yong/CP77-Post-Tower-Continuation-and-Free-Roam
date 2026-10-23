param([string]$Revision='ep1_01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly
$helper=Get-Content (Join-Path $ws 'tools/build_fresh_gigs_b5.ps1') -Raw
$begin=$helper.IndexOf('function ClearB5(');$end=$helper.IndexOf('$allRoots=@{};')
if($begin -lt 0 -or $end -le $begin){throw 'Definition helper boundary changed'}
. ([scriptblock]::Create($helper.Substring($begin,$end-$begin)))
if($Revision -cnotmatch '^ep1_\d{2}$'){throw 'Invalid immutable revision'}
$out=Join-Path $PSScriptRoot ('build/'+$Revision)
if(Test-Path -LiteralPath $out){throw 'Component already exists'}
New-Item -ItemType Directory $out,(Join-Path $out 'source'),(Join-Path $out 'readback')|Out-Null
$spec=Get-Content (Join-Path $PSScriptRoot 'contract.json') -Raw|ConvertFrom-Json
$pins=[ordered]@{};$copies=[Collections.Generic.List[object]]::new();$resources=[Collections.Generic.List[object]]::new()
function Pin($rel){$pins[$rel]=(Get-FileHash -LiteralPath (Join-Path $ws $rel)).Hash}
function ReadGraph($rel){Pin $rel;return (Read-Cr2wFile (Join-Path $ws $rel)).RootChunk.Graph.Chunk}
function NewGraph{return [WolvenKit.RED4.Types.questGraphDefinition]::new()}
function CopyNodes($dest,$src,$ids,$rel,$graphPath,$destGraphPath){
 foreach($id in $ids){$old=Get-QuestNode $src $id;$n=$old.DeepCopy();ClearB5 $n
  if($n -is [WolvenKit.RED4.Types.questPhaseNodeDefinition] -and $null -ne $n.PhaseGraph -and $null -ne $n.PhaseGraph.Chunk){RewireB5 $n.PhaseGraph.Chunk $old.PhaseGraph.Chunk}
  AddNodeB5 $dest $n
  $copies.Add([ordered]@{source=$rel;source_graph=$graphPath;source_id=$id;target_graph=$destGraphPath;target_id=$id})
 }
}
function Slice($src,$ids,$rel,$gp,$target){
 $g=NewGraph;CopyNodes $g $src $ids $rel $gp $target
 RebuildB5 $g @(EdgesB5 $src|ForEach-Object {$_}|Where-Object {$_[0] -in $ids -and $_[2] -in $ids})
 return $g
}
function Edges($g){return ,@(EdgesB5 $g|ForEach-Object {$_})}
function SaveGraph($g,$depot,$key){
 $root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();Set-RedHandleProperty $root Graph $g
 $f=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$f.RootChunk=$root
 $raw=Join-Path (Join-Path $out 'source') $depot;Write-Cr2wFile $f $raw
 $json=Join-Path $out ('readback/'+$key+'.json');Export-Cr2wJson (Read-Cr2wFile $raw) $json
 $resources.Add([ordered]@{depot=$depot;relative=('source/'+$depot.Replace('\','/'));sha256=(Get-FileHash $raw).Hash;readback=('readback/'+$key+'.json');readback_sha256=(Get-FileHash $json).Hash})
}
function Inline($id,$g,$template){$n=$template.DeepCopy();ClearB5 $n;$n.Id=[uint16]$id;$n.PhaseResource=[WolvenKit.RED4.Types.CResourceAsyncReference[WolvenKit.RED4.Types.questQuestPhaseResource]]::new('');Set-RedHandleProperty $n PhaseGraph $g;return $n}
$n1='research/sidejobs_s23/ep1/native_01/raw/';$n2='research/sidejobs_s23/ep1/native_02/raw/'
$worldRel=$n2+'ep1/openworld/world_stories/ep1_world_stories.questphase';$world=ReadGraph $worldRel
$defaultsRel=$n2+'ep1/quest/ep1_default_dialogs.questphase';$defaults=ReadGraph $defaultsRel
$persistentRel=$n1+'ep1/quest/ep1_persistent_content.questphase';$persistent=ReadGraph $persistentRel
$mqRel=$n1+'ep1/quest/minor_quests/mq306/mq306.questphase';$mq=ReadGraph $mqRel
$aaronRel=$n1+'ep1/quest/minor_quests/mq306/phases/mq306_04a_aaron_meeting.questphase';$aaron=ReadGraph $aaronRel
$vehicleParentRel='research/ncpd_scanner_n1/parents_02/raw/base/open_world/minor_activities/badlands/inland_avenue_se1/ma_bls_ina_se1_minor_activities.questphase';$vehicleParent=ReadGraph $vehicleParentRel
$sliderRel=$n2+'ep1/quest/main_quests/q304/phases/q304_slider_stash.questphase';$slider=ReadGraph $sliderRel
$stevenRel='research/gig_restoration/batch_b4/sources/raw/ep1/openworld/street_stories/sts_ep1_08/phases/sts_ep1_08_cleanup.questphase';$steven=ReadGraph $stevenRel
$base='towercontinued\sidejobs_s23\ep1\'
# MQ306: completed clinic/Angie progress is immutable. Resume the exact original
# SMS choice wait. Initial Aaron message, contact-add, waiting timer and world
# encounter setup are not reissued. Both original reward managers remain later.
$smsIds=@(0,24,26,54,46,28,58,19)
$sms=Slice (NestedB5 $aaron @(25)) $smsIds $aaronRel 'root/25' 'mq306_aaron/root/25'
$se=Edges $sms;$se+=,@(0,'Out',24,'In');RebuildB5 $sms $se
$arIds=@(0,25,37,49,80,42,56,43,45,46,2)
$ar=Slice $aaron $arIds $aaronRel 'root' 'mq306_aaron/root'
Set-RedHandleProperty (Get-QuestNode $ar 25) PhaseGraph $sms
SaveGraph $ar ($base+'mq306_aaron.questphase') 'mq306_aaron'
$resume=Slice $mq @(1,7,9,31,32,33) $mqRel 'root' 'mq306_owner/root'
AddNodeB5 $resume (New-InputNode 0 'In1')
(Get-QuestNode $resume 7).PhaseResource=[WolvenKit.RED4.Types.CResourceAsyncReference[WolvenKit.RED4.Types.questQuestPhaseResource]]::new($base+'mq306_aaron.questphase')
$re=Edges $resume;$re+=,@(0,'Out',7,'In1');$re+=,@(7,'Out1',9,'In1');RebuildB5 $resume $re
SaveGraph $resume ($base+'mq306_owner.questphase') 'mq306_owner'
$states=@{1='Inactive';2='Active';3='Succeeded';4='Failed'}
function JournalCondition($path,$class,$state){
 $p=[WolvenKit.RED4.Types.gameJournalPath]::new();$p.RealPath=$path;$p.ClassName=$class;$p.FileEntryIndex=if($path -match '(^|/)contacts/'){1}else{2}
 $t=[WolvenKit.RED4.Types.questJournalEntryState_ConditionType]::new();Set-RedHandleProperty $t Path $p;$t.State=[Enum]::Parse([WolvenKit.RED4.Types.Enums+gameJournalEntryState],$state);$t.Inverted=$false
 $c=[WolvenKit.RED4.Types.questJournalCondition]::new();Set-RedHandleProperty $c Type $t;return $c
}
function Logical($operation,$conditions){$c=[WolvenKit.RED4.Types.questLogicalCondition]::new();$c.Operation=[Enum]::Parse([WolvenKit.RED4.Types.Enums+questLogicalOperation],$operation);foreach($x in $conditions){Add-RedHandle $c.Conditions $x};return $c}
function Guard($owner,[bool]$post){
 $pairs=[ordered]@{};foreach($o in @($spec.common_equal,$owner.facts_equal)){foreach($p in $o.PSObject.Properties){$pairs[$p.Name]=[int]$p.Value}}
 if($post -and 'lease_facts' -in $owner.PSObject.Properties.Name){foreach($p in $owner.lease_facts.PSObject.Properties){$pairs[$p.Name]=[int]$p.Value}}
 $pairs[$owner.tag+'_Issued']=[int]$post;$pairs[$owner.tag+'_Fault']=0;$pairs[$owner.tag+'_Finished']=0
 if(!$post){$pairs[$owner.tag+'_Permit']=1}
 $c=AllB5 $pairs
 foreach($p in $owner.fact_ranges.PSObject.Properties){Add-RedHandle $c.Conditions (New-FactCondition $p.Name ([int]$p.Value.min) 'GreaterOrEqual');Add-RedHandle $c.Conditions (New-FactCondition $p.Name ([int]$p.Value.max) 'LessOrEqual')}
 foreach($j in $owner.journals){$ss=@($j.states);if($post -and $j.path -in $owner.reactivate_paths){$ss=@(2)};$conds=@();foreach($s in $ss){$conds+=JournalCondition $j.path $j.class $states[[int]$s]};Add-RedHandle $c.Conditions (Logical 'OR' $conds)}
 if($owner.key -eq 'VOODOO'){Add-RedHandle $c.Conditions ((Get-QuestNode $slider 2).Condition.Chunk.DeepCopy());Add-RedHandle $c.Conditions (Logical 'NOR' @((Get-QuestNode $slider 3).Condition.Chunk.DeepCopy()))}
 if('vehicle_not_available' -in $owner.PSObject.Properties.Name){$t=[WolvenKit.RED4.Types.questVehicleAvailable_ConditionType]::new();$t.VehicleType=[WolvenKit.RED4.Types.Enums+questAvailableVehicleType]::SpecificVehicle;$t.VehicleName=$owner.vehicle_not_available;$v=[WolvenKit.RED4.Types.questVehicleCondition]::new();Set-RedHandleProperty $v Type $t;Add-RedHandle $c.Conditions (Logical 'NOR' @($v))}
 return $c
}
foreach($o in $spec.owners){
 $native=NewGraph;$nativeEntry=0;$nativeEntrySocket='In1';$nativeOutput=500
 switch($o.key){
  'MQ306' {$n=(Get-QuestNode $mq 7).DeepCopy();ClearB5 $n;$n.Id=[uint16]0;$n.PhaseResource=[WolvenKit.RED4.Types.CResourceAsyncReference[WolvenKit.RED4.Types.questQuestPhaseResource]]::new($base+'mq306_owner.questphase');AddNodeB5 $native $n;AddNodeB5 $native (New-OutputNode 500 'Out1');RebuildB5 $native (,@(0,'Out1',500,'In'))}
  'VOODOO' {$pg=NestedB5 $persistent @(30);CopyNodes $native $pg @(4) $persistentRel 'root/30' 'voodoo_boot/root/100';$nativeEntry=4;AddNodeB5 $native (New-OutputNode 500 'Out1');RebuildB5 $native (,@(4,'Out1',500,'In'))}
  'BILL' {CopyNodes $native $world @(35,11) $worldRel 'root' 'bill_boot/root/100';CopyNodes $native $defaults @(14,5) $defaultsRel 'root' 'bill_boot/root/100';AddNodeB5 $native (New-InputNode 0 'In1');RebuildB5 $native @(@(0,'Out',35,'In'),@(35,'Out',11,'In1'),@(0,'Out',14,'In'),@(14,'Out',5,'In1'),@(5,'Out1',14,'In'))}
  'HASAN' {CopyNodes $native $world @(29,5) $worldRel 'root' 'hasan_boot/root/100';CopyNodes $native $defaults @(12,9) $defaultsRel 'root' 'hasan_boot/root/100';AddNodeB5 $native (New-InputNode 0 'In1');RebuildB5 $native @(@(0,'Out',29,'In'),@(29,'Out',5,'In1'),@(0,'Out',12,'In'),@(12,'Out',9,'In1'),@(9,'Out1',12,'In'))}
  'RINDER' {CopyNodes $native $world @(47,46,4) $worldRel 'root' 'rinder_boot/root/100';AddNodeB5 $native (New-InputNode 0 'In1');RebuildB5 $native @(@(0,'Out',47,'In'),@(47,'Out',46,'In'),@(46,'Out',4,'In1'))}
  'STEVEN' {
   $sp=NestedB5 $steven @(3);$ids=@(0,2,3,5,8,9,17,37,38,39,56,58,59,64,65,91,92,93,94,95,96)
   $tail=Slice $sp $ids $stevenRel 'root/3' 'steven_boot/root/100/501'
   $phase=Inline 501 $tail (Get-QuestNode $steven 3);AddNodeB5 $native $phase
   CopyNodes $native $defaults @(19,17) $defaultsRel 'root' 'steven_boot/root/100'
   AddNodeB5 $native (New-InputNode 0 'In1')
   RebuildB5 $native @(@(0,'Out',501,'In1'),@(0,'Out',19,'In'),@(19,'Out',17,'In1'),@(17,'Out1',19,'In'))
  }
  {$_ -in @('MQ046','MQ047')} {$id=if($_ -eq 'MQ046'){141}else{145};CopyNodes $native $vehicleParent @(173,$id) $vehicleParentRel 'root' ($o.key.ToLower()+'_boot/root/100');AddNodeB5 $native (New-InputNode 0 'In1');RebuildB5 $native @(@(0,'Out',173,'In'),@(173,'Out',$id,'In1'))}
 }
 # Every embedded graph is entered via a real input node. Direct parent slices
 # receive a new entry only; copied child payload/prefabs stay byte-semantic equal.
 if($nativeEntry -ne 0){AddNodeB5 $native (New-InputNode 0 'In1');$e=Edges $native;$e+=,@(0,'Out',$nativeEntry,$nativeEntrySocket);RebuildB5 $native $e}
 if($o.key -eq 'MQ306'){
  # Node 0 above was a phase, not an input; move it to 501 and give it its own input.
  $child=Get-QuestNode $native 0;$child.Id=[uint16]501;ClearB5 $child;AddNodeB5 $native (New-InputNode 0 'In1');RebuildB5 $native @(@(0,'Out',501,'In1'),@(501,'Out1',500,'In'))
 }
 $boot=NewGraph
 foreach($n in @((New-InputNode 0 'In1'),(New-SetFactNode 1 ($o.tag+'_Ready') 1),(PauseB5 2 (Guard $o $false)),(New-ConditionNode 3 (Guard $o $false)),(New-SetFactNode 4 ($o.tag+'_Issued') 1),(New-ConditionNode 90 (Guard $o $true)),(New-SetFactNode 91 ($o.tag+'_Fault') 1),(New-SetFactNode 92 ($o.tag+'_Entered') 1),(New-SetFactNode 101 ($o.tag+'_Finished') 1))){AddNodeB5 $boot $n}
 $edges=@(@(0,'Out',1,'In'),@(1,'Out',2,'In'),@(2,'Out',3,'In'),@(3,'False',2,'In'),@(3,'True',4,'In'),@(90,'False',91,'In'),@(90,'True',92,'In'),@(92,'Out',100,'In1'))
 if($o.key -in @('MQ306','VOODOO')){$edges+=,@(100,'Out1',101,'In')}else{
  # Observe native journal completion separately. Do not terminate a persistent
  # native default-dialog owner merely because its side job has succeeded.
  $rootJournal=@($o.journals|Where-Object class -eq 'gameJournalQuest')[0]
  AddNodeB5 $boot (PauseB5 102 (JournalCondition $rootJournal.path $rootJournal.class 'Succeeded'))
  $edges+=,@(92,'Out',102,'In');$edges+=,@(102,'Out',101,'In')
 }
 $last=4;$idx=10
 if('lease_facts' -in $o.PSObject.Properties.Name){foreach($p in $o.lease_facts.PSObject.Properties){AddNodeB5 $boot (New-SetFactNode $idx $p.Name ([int]$p.Value));$edges+=,@($last,'Out',$idx,'In');$last=$idx;$idx++}}
 foreach($path in $o.reactivate_paths){$j=@($o.journals|Where-Object path -eq $path)[0];$n=(Get-QuestNode (NestedB5 $aaron @(25)) 34).DeepCopy();ClearB5 $n;$n.Id=[uint16]$idx;$n.Type.Chunk.Path.Chunk.RealPath=$path;$n.Type.Chunk.Path.Chunk.ClassName=$j.class;AddNodeB5 $boot $n;$edges+=,@($last,'Out',$idx,'Active');$last=$idx;$idx++}
 $delay=(Get-QuestNode $vehicleParent 173).DeepCopy();ClearB5 $delay;$delay.Id=[uint16]89;$delay.Condition.Chunk.Type.Chunk.TickCount=[uint32]2;AddNodeB5 $boot $delay
 $edges+=,@($last,'Out',89,'In');$edges+=,@(89,'Out',90,'In')
 $wrapper=Inline 100 $native (Get-QuestNode $mq 7);AddNodeB5 $boot $wrapper;RebuildB5 $boot $edges
 SaveGraph $boot $o.depot ($o.key.ToLower()+'_boot')
}
$proofRel='research/sidejobs_s23/ep1/native_03/official_comparison.json'
$proof=Get-Content (Join-Path $ws $proofRel) -Raw|ConvertFrom-Json
if($proof.status -cne 'PASS_OFFICIAL_BYTES'){throw 'Original bytes not verified'}
foreach($p in $proof.comparisons.PSObject.Properties){
 foreach($rel in @($p.Value.source,$p.Value.official_witness)){if((Get-FileHash (Join-Path $ws $rel)).Hash -cne $p.Value.sha256){throw ('Changed original '+$rel)};Pin $rel;Pin ($rel.Replace('/raw/','/json/')+'.json')}
}
foreach($rel in @('prealpha/sidejobs_s23/ep1/build_component.ps1','prealpha/sidejobs_s23/ep1/prepare_contract.py','prealpha/sidejobs_s23/ep1/contract.json','prealpha/sidejobs_s23/ep1/test_component.py','prealpha/sidejobs_s23/ep1/audit_dependencies.py','prealpha/sidejobs_s23/ep1/verify_official.ps1','tools/build_phase2a.ps1','tools/build_fresh_gigs_b5.ps1','tools/extract_resources.ps1',$spec.capture,$proofRel)){Pin $rel}
$resourceMap=[ordered]@{};foreach($r in $resources){$resourceMap[$r.depot]=$r.sha256}
$manifest=[ordered]@{status='COMPONENT_BUILT_LIVE_PENDING';revision=$Revision;resources=$resourceMap;resource_details=@($resources.ToArray());boots=@($spec.owners|ForEach-Object {$_.depot});contract='prealpha/sidejobs_s23/ep1/contract.json';contract_sha256=$pins['prealpha/sidejobs_s23/ep1/contract.json'];source_pins=$pins;official_comparison=$proofRel;native_copies=@($copies.ToArray());native_changes=@('MQ306 root/25 narrowed to existing dive-reply wait, no replay of delivered message or clinic; original downstream reward/parent cleanup retained','MQ306 Aaron root omits other encounters; only guarded texts route','Steven cleanup narrowed to night-city invitation branch; Janet/Katya/stadium excluded','Original parent slices connect to new one-shot boot; no official-resource override');limitations=@('MQ306 other outcomes require separate audited adapters; phone history absent from capture is checked live','Native availability/contact/door state unknown defers; Issued is not interaction proof','Bill B0 QuestOwns remains1 while original native default owner lives','Current U9 Spy in the Jungle retains its own Steven follow-up; S23 defers that case');native_progress_resets=$false;game_writes=$false}
[IO.File]::WriteAllText((Join-Path $out 'component.json'),($manifest|ConvertTo-Json -Depth 40),[Text.UTF8Encoding]::new($false))
[pscustomobject]$manifest|Select-Object status,revision,contract_sha256|ConvertTo-Json
