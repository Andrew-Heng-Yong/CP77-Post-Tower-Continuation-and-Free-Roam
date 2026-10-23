param([string]$Revision='families_03',[string]$Contract='prealpha/sidejobs_s25/families/contract03.json')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly
$helper=Get-Content (Join-Path $ws 'tools/build_fresh_gigs_b5.ps1') -Raw
$begin=$helper.IndexOf('function ClearB5(');$end=$helper.IndexOf('$allRoots=@{};')
if($begin -lt 0 -or $end -le $begin){throw 'Definition helper boundary changed'}
. ([scriptblock]::Create($helper.Substring($begin,$end-$begin)))
if($Revision -cnotmatch '^families_\d{2}$'){throw 'Invalid immutable revision'}
$out=Join-Path $PSScriptRoot ('build/'+$Revision)
if(Test-Path -LiteralPath $out){throw 'Component already exists'}
New-Item -ItemType Directory $out,(Join-Path $out 'source'),(Join-Path $out 'readback')|Out-Null
$spec=Get-Content (Join-Path $ws $Contract) -Raw|ConvertFrom-Json
$pins=[ordered]@{};$copies=[Collections.Generic.List[object]]::new();$resources=[Collections.Generic.List[object]]::new()
function Pin($rel){$pins[$rel]=(Get-FileHash -LiteralPath (Join-Path $ws $rel)).Hash}
function ReadGraph($rel){Pin $rel;Pin ($rel.Replace('/raw/','/json/')+'.json');return (Read-Cr2wFile (Join-Path $ws $rel)).RootChunk.Graph.Chunk}
function NewGraph{return [WolvenKit.RED4.Types.questGraphDefinition]::new()}
function CopyNode($dest,$src,$id,$rel,$gp,$target,$newid=$id){
 $old=Get-QuestNode $src $id;$n=$old.DeepCopy();ClearB5 $n;$n.Id=[uint16]$newid
 if($n -is [WolvenKit.RED4.Types.questPhaseNodeDefinition] -and $null -ne $n.PhaseGraph -and $null -ne $n.PhaseGraph.Chunk){RewireB5 $n.PhaseGraph.Chunk $old.PhaseGraph.Chunk}
 AddNodeB5 $dest $n;$copies.Add([ordered]@{source=$rel;source_graph=$gp;source_id=$id;target_graph=$target;target_id=$newid})
}
function Slice($src,$ids,$rel,$gp,$target){$g=NewGraph;foreach($id in $ids){CopyNode $g $src $id $rel $gp $target};RebuildB5 $g @(EdgesB5 $src|ForEach-Object {$_}|Where-Object {$_[0] -in $ids -and $_[2] -in $ids});return $g}
function SaveGraph($g,$depot,$key){
 $root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();Set-RedHandleProperty $root Graph $g
 $f=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$f.RootChunk=$root
 $raw=Join-Path (Join-Path $out 'source') $depot;Write-Cr2wFile $f $raw
 $json=Join-Path $out ('readback/'+$key+'.json');Export-Cr2wJson (Read-Cr2wFile $raw) $json
 $resources.Add([ordered]@{depot=$depot;relative=('source/'+$depot.Replace('\','/'));sha256=(Get-FileHash $raw).Hash;readback=('readback/'+$key+'.json');readback_sha256=(Get-FileHash $json).Hash})
}
function JournalCondition($path,$class,$state){
 $p=[WolvenKit.RED4.Types.gameJournalPath]::new();$p.RealPath=$path;$p.ClassName=$class;$p.FileEntryIndex=if($path -match '(^|/)contacts/'){1}else{2}
 $t=[WolvenKit.RED4.Types.questJournalEntryState_ConditionType]::new();Set-RedHandleProperty $t Path $p;$t.State=[Enum]::Parse([WolvenKit.RED4.Types.Enums+gameJournalEntryState],$state);$t.Inverted=$false
 $c=[WolvenKit.RED4.Types.questJournalCondition]::new();Set-RedHandleProperty $c Type $t;return $c
}
function Guard($owner,[bool]$post){
 $pairs=[ordered]@{};foreach($o in @($spec.common_equal,$owner.facts_equal)){foreach($p in $o.PSObject.Properties){$pairs[$p.Name]=[int]$p.Value}}
 $pairs[$owner.tag+'_Issued']=[int]$post;$pairs[$owner.tag+'_Fault']=0;$pairs[$owner.tag+'_Finished']=0
 if(!$post){$pairs[$owner.tag+'_Permit']=1}
 $c=AllB5 $pairs
 foreach($p in $owner.fact_ranges.PSObject.Properties){Add-RedHandle $c.Conditions (New-FactCondition $p.Name ([int]$p.Value.min) 'GreaterOrEqual');Add-RedHandle $c.Conditions (New-FactCondition $p.Name ([int]$p.Value.max) 'LessOrEqual')}
 foreach($j in $owner.journals){if(@($j.states).Count -ne 1 -or $j.states[0] -ne 1){throw 'Only Inactive fresh entry'};Add-RedHandle $c.Conditions (JournalCondition $j.path $j.class 'Inactive')}
 return $c
}
$templateRel='research/sidejobs_s24/ep1/native_01/raw/ep1/quest/minor_quests/mq305/phases/mq305_01_hook_setup.questphase';$template=ReadGraph $templateRel
$phaseRel='research/sidejobs_s24/ep1/native_01/raw/ep1/quest/minor_quests/mq306/mq306.questphase';$phase=ReadGraph $phaseRel
$tickRel='research/ncpd_scanner_n1/parents_02/raw/base/open_world/minor_activities/badlands/inland_avenue_se1/ma_bls_ina_se1_minor_activities.questphase';$tick=ReadGraph $tickRel
$initRel='research/sidejobs_s25/families/native_01/raw/base/quest/holocalls/holocall_initializers.questphase';$init=ReadGraph $initRel
$persistRel='research/sidejobs_s25/families/native_03/raw/base/quest/persistent_content.questphase';$persistent=ReadGraph $persistRel
foreach($o in $spec.owners){
 $key=$o.key.ToLower();$rel=$o.native_source.Substring(0,$o.native_source.Length-5).Replace('/json/','/raw/');$old=ReadGraph $rel
 $native=Slice $old @($o.selected_nodes) $rel 'root' ($key+'/root/100')
 if($o.key -eq 'SQ025_FRESH'){
  # Terminate only at the original scanner return, before excluded sequel134.
  AddNodeB5 $native (New-SetFactNode 1000 ($o.tag+'_Finished') 1)
  $cut=[WolvenKit.RED4.Types.questCutControlNodeDefinition]::new();$cut.Id=[uint16]1001
  foreach($port in @(@('In','Input'),@('Out','Output'),@('CutSource','CutSource'))){[void](New-QuestSocket $cut $port[0] ([Enum]::Parse([WolvenKit.RED4.Types.Enums+questSocketType],$port[1])))}
  AddNodeB5 $native $cut;$traffic=NestedB5 $old @(147)
  CopyNode $native $traffic 18 $rel 'root/147' ($key+'/root/100') 1002
  CopyNode $native $traffic 14 $rel 'root/147' ($key+'/root/100') 1003
  $e=@(EdgesB5 $native|ForEach-Object {$_});$e+=,@(124,'Out1',1000,'In');$e+=,@(1000,'Out',1001,'In')
  foreach($id in @(147,142,114)){$e+=,@(1001,'CutSource',$id,'CutDestination')}
  $e+=,@(1001,'Out',1002,'In');$e+=,@(1002,'Out',1003,'In');RebuildB5 $native $e
 }
 $wrapper=(Get-QuestNode $phase 7).DeepCopy();ClearB5 $wrapper;$wrapper.Id=[uint16]100;$wrapper.PhaseResource=[WolvenKit.RED4.Types.CResourceAsyncReference[WolvenKit.RED4.Types.questQuestPhaseResource]]::new('');Set-RedHandleProperty $wrapper PhaseGraph $native
 $boot=NewGraph
 foreach($n in @((New-InputNode 0 'In1'),(New-SetFactNode 1 ($o.tag+'_Ready') 1),(PauseB5 2 (Guard $o $false)),(New-ConditionNode 3 (Guard $o $false)),(New-SetFactNode 4 ($o.tag+'_Issued') 1),(New-ConditionNode 90 (Guard $o $true)),(New-SetFactNode 91 ($o.tag+'_Fault') 1),(New-SetFactNode 92 ($o.tag+'_Entered') 1),$wrapper)){AddNodeB5 $boot $n}
 $delay=(Get-QuestNode $tick 173).DeepCopy();ClearB5 $delay;$delay.Id=[uint16]89;$delay.Condition.Chunk.Type.Chunk.TickCount=[uint32]2;AddNodeB5 $boot $delay
 $e=@(@(0,'Out',1,'In'),@(1,'Out',2,'In'),@(2,'Out',3,'In'),@(3,'False',2,'In'),@(3,'True',4,'In'),@(4,'Out',89,'In'),@(89,'Out',90,'In'),@(90,'False',91,'In'),@(90,'True',92,'In'))
 if($o.key -eq 'MQ025_FRESH'){
  $contact=(Get-QuestNode $template 9).DeepCopy();ClearB5 $contact;$contact.Id=[uint16]93;$contact.Type.Chunk.Params[0].Contact.Chunk.RealPath=$o.contact;$contact.Type.Chunk.Params[0].SendNotification=$false;AddNodeB5 $boot $contact
  AddNodeB5 $boot (New-SetFactNode 101 ($o.tag+'_Finished') 1)
  $j=@($o.journals|Where-Object {$_.class -eq 'gameJournalQuest' -and $_.path.EndsWith('/'+$o.id)})[0]
  AddNodeB5 $boot (PauseB5 102 (JournalCondition $j.path $j.class 'Succeeded'))
  $e+=,@(92,'Out',93,'In');$e+=,@(93,'Out',100,$o.entry);$e+=,@(92,'Out',102,'In');$e+=,@(102,'Out',101,'In')
 }else{
  CopyNode $boot $init 51 $initRel 'root' ($key+'/root') 94
  CopyNode $boot (NestedB5 $persistent @(151,6)) 35 $persistRel 'root/151/6' ($key+'/root') 95
  $e+=,@(92,'Out',94,'In1');$e+=,@(92,'Out',95,'In1');$e+=,@(92,'Out',100,$o.entry)
 }
 RebuildB5 $boot $e;SaveGraph $boot $o.depot $key
}
# Keep exactly ONE existing Fred owner; only select the original dialogue when
# this fresh boxing owner has issued. Legacy/nonfresh service keeps hidden B0.
$fredRel='archive/b0_story_services/source/towercontinued/b0_story_services/fred.questphase';Pin $fredRel
$fredOriginal=(Read-Cr2wFile (Join-Path $ws $fredRel)).RootChunk.Graph.Chunk;$fred=$fredOriginal.DeepCopy();RewireB5 $fred $fredOriginal
$g=NestedB5 $fred @(5,14);$scene=(Get-QuestNode $g 3).DeepCopy();ClearB5 $scene;$scene.Id=[uint16]300
$scene.SceneFile=[WolvenKit.RED4.Types.CResourceAsyncReference[WolvenKit.RED4.Types.scnSceneResource]]::new('base\open_world\vendors\watson\little_china\wat_lch_melee_01\wat_lch_melee_01.scene')
AddNodeB5 $g $scene;AddNodeB5 $g (New-ConditionNode 301 (AllB5 ([ordered]@{PTFRS25_MQ025_FRESH_Issued=1;PTFRS25_MQ025_FRESH_Fault=0})))
$e=@(EdgesB5 $g|ForEach-Object {$_});$redirect=0
foreach($x in $e){if($x[0] -eq 202 -and $x[2] -eq 3){$x[2]=301;$x[3]='In';$redirect++}}
if($redirect -ne 1){throw 'Fred single native entry changed'}
$e+=,@(301,'True',300,'wat_lch_melee_01_default_start');$e+=,@(301,'False',3,'wat_lch_melee_01_default_start');RebuildB5 $g $e
SaveGraph $fred 'towercontinued\b0_story_services\fred.questphase' 'fred'
foreach($p in $spec.source_pins.PSObject.Properties){Pin $p.Name;if($pins[$p.Name] -cne $p.Value){throw 'Changed contract source'}}
foreach($p in @($Contract,'prealpha/sidejobs_s25/families/build.ps1','prealpha/sidejobs_s25/families/test.py','prealpha/sidejobs_s25/families/prepare.py','prealpha/sidejobs_s25/families/inspect.py','prealpha/sidejobs_s25/families/extract.ps1','research/b0_story_services/validation/fred.questphase.json','tools/build_phase2a.ps1','tools/build_fresh_gigs_b5.ps1','research/q307_extracted/raw/base/quest/cyberpunk2077.questphase')){Pin $p}
$map=[ordered]@{};foreach($r in $resources){$map[$r.depot]=$r.sha256}
$donors=[ordered]@{'towercontinued\b0_story_services\fred.questphase'=[ordered]@{source=$fredRel;sha256=$pins[$fredRel];archive='TowerContinued_PreAlpha.archive'}}
$m=[ordered]@{status='COMPONENT_BUILT_FRESH_FAMILIES_LIVE_PENDING';revision=$Revision;resources=$map;resource_details=@($resources.ToArray());boots=@($spec.owners|ForEach-Object {$_.depot});contract=$Contract;contract_sha256=$pins[$Contract];source_pins=$pins;native_copies=@($copies.ToArray());native_resources=$spec.native_resources;override_donors=$donors;native_changes=@('Original selected parent payloads/internal nested edges retained; Delamain excluded sequel134 disconnected at parent boundary','Original scanner-return success gets ownedFinished then cuts147/142/114 local watchers and copies stock local traffic release18/14','Single existing Fred owner selects original scene only for freshIssued1; nonfresh B0 behavior retained','Original AddContact template targets verified Fred contact silently after fresh admission');limitations=@('All family descendants must be Inactive and native progress zero except audited passive sq025_active0..1','Claire story family deferred due connected official dependency absent; existing R1 races unchanged','Live fresh family gameplay/rewards/reload/Johnny voice-body behavior pending');native_progress_resets=$false;game_writes=$false}
[IO.File]::WriteAllText((Join-Path $out 'component.json'),($m|ConvertTo-Json -Depth 50),[Text.UTF8Encoding]::new($false))
[pscustomobject]$m|Select-Object status,revision,contract_sha256|ConvertTo-Json
