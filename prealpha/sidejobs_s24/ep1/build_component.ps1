param([string]$Revision='ep1_02',[string]$Contract='prealpha/sidejobs_s24/ep1/contract02.json')
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
$spec=Get-Content (Join-Path $ws $Contract) -Raw|ConvertFrom-Json
$pins=[ordered]@{};$copies=[Collections.Generic.List[object]]::new();$resources=[Collections.Generic.List[object]]::new();$dependencies=[ordered]@{}
function Pin($rel){$pins[$rel]=(Get-FileHash -LiteralPath (Join-Path $ws $rel)).Hash}
function ReadGraph($rel){Pin $rel;Pin ($rel.Replace('/raw/','/json/')+'.json');return (Read-Cr2wFile (Join-Path $ws $rel)).RootChunk.Graph.Chunk}
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
 foreach($j in $owner.journals){if(@($j.states).Count -ne 1 -or $j.states[0] -ne 1){throw 'Fresh owner admits only Inactive'};Add-RedHandle $c.Conditions (JournalCondition $j.path $j.class 'Inactive')}
 if('vehicle_not_available' -in $owner.PSObject.Properties.Name){
  $t=[WolvenKit.RED4.Types.questVehicleAvailable_ConditionType]::new();$t.VehicleType=[WolvenKit.RED4.Types.Enums+questAvailableVehicleType]::SpecificVehicle;$t.VehicleName=$owner.vehicle_not_available
  $v=[WolvenKit.RED4.Types.questVehicleCondition]::new();Set-RedHandleProperty $v Type $t
  $not=[WolvenKit.RED4.Types.questLogicalCondition]::new();$not.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::NOR;Add-RedHandle $not.Conditions $v;Add-RedHandle $c.Conditions $not
 }
 return $c
}
$nativeRel='research/sidejobs_s24/ep1/native_01/raw/'
$minorRel=$nativeRel+'ep1/quest/minor_quests/ep1_minor_quests.questphase';$minor=ReadGraph $minorRel
$persistentRel=$nativeRel+'ep1/quest/ep1_persistent_content.questphase';$persistent=ReadGraph $persistentRel
$templateRel=$nativeRel+'ep1/quest/minor_quests/mq305/phases/mq305_01_hook_setup.questphase';$template=ReadGraph $templateRel
$mqRel=$nativeRel+'ep1/quest/minor_quests/mq306/mq306.questphase';$mq=ReadGraph $mqRel
$tickRel='research/ncpd_scanner_n1/parents_02/raw/base/open_world/minor_activities/badlands/inland_avenue_se1/ma_bls_ina_se1_minor_activities.questphase';$tick=ReadGraph $tickRel
foreach($o in $spec.owners){
 $key=$o.key.ToLower()+'_boot';$parent=$o.parent_slice
 if($parent.source -eq 'ep1\quest\minor_quests\ep1_minor_quests.questphase'){$source=$minor;$rel=$minorRel}else{$source=NestedB5 $persistent @(30);$rel=$persistentRel}
 $native=Slice $source @($parent.ids) $rel $parent.graph ($key+'/root/100')
 AddNodeB5 $native (New-InputNode 0 'In1')
 $edges=@(EdgesB5 $native|ForEach-Object {$_});$edges+=,@(0,'Out',[int]$parent.entry,$parent.socket);RebuildB5 $native $edges
 $wrapper=(Get-QuestNode $mq 7).DeepCopy();ClearB5 $wrapper;$wrapper.Id=[uint16]100;$wrapper.PhaseResource=[WolvenKit.RED4.Types.CResourceAsyncReference[WolvenKit.RED4.Types.questQuestPhaseResource]]::new('');Set-RedHandleProperty $wrapper PhaseGraph $native
 $boot=NewGraph
 foreach($n in @((New-InputNode 0 'In1'),(New-SetFactNode 1 ($o.tag+'_Ready') 1),(PauseB5 2 (Guard $o $false)),(New-ConditionNode 3 (Guard $o $false)),(New-SetFactNode 4 ($o.tag+'_Issued') 1),(New-ConditionNode 90 (Guard $o $true)),(New-SetFactNode 91 ($o.tag+'_Fault') 1),(New-SetFactNode 92 ($o.tag+'_Entered') 1),(New-SetFactNode 101 ($o.tag+'_Finished') 1),$wrapper)){AddNodeB5 $boot $n}
 $delay=(Get-QuestNode $tick 173).DeepCopy();ClearB5 $delay;$delay.Id=[uint16]89;$delay.Condition.Chunk.Type.Chunk.TickCount=[uint32]2;AddNodeB5 $boot $delay
 $rootJournal=@($o.journals|Where-Object class -eq 'gameJournalQuest')[0]
 AddNodeB5 $boot (PauseB5 102 (JournalCondition $rootJournal.path $rootJournal.class 'Succeeded'))
 $edges=@(@(0,'Out',1,'In'),@(1,'Out',2,'In'),@(2,'Out',3,'In'),@(3,'False',2,'In'),@(3,'True',4,'In'),@(4,'Out',89,'In'),@(89,'Out',90,'In'),@(90,'False',91,'In'),@(90,'True',92,'In'),@(92,'Out',102,'In'),@(102,'Out',101,'In'))
 if($null -ne $o.contact){
  # Stock AddContact operation, only the approved target and notification change.
  # Contact metadata comes from the extracted original journal, never a guess.
  # This is before only a FRESH owner; existing S23 Aaron reply stays untouched.
  $contact=(Get-QuestNode $template 9).DeepCopy();ClearB5 $contact;$contact.Id=[uint16]93
  $contact.Type.Chunk.Params[0].Contact.Chunk.RealPath=$o.contact
  $contact.Type.Chunk.Params[0].SendNotification=$false
  AddNodeB5 $boot $contact;$edges+=,@(92,'Out',93,'In');$edges+=,@(93,'Out',100,'In1')
 }else{$edges+=,@(92,'Out',100,'In1')}
 RebuildB5 $boot $edges;SaveGraph $boot $o.depot $key
 foreach($depot in $o.native_dependencies){
  $rel=$null
  foreach($dir in @(Get-ChildItem -LiteralPath (Join-Path $ws 'research/sidejobs_s24/ep1') -Directory -Filter 'native_*')){
   $candidate='research/sidejobs_s24/ep1/'+$dir.Name+'/raw/'+$depot.Replace('\','/')
   if(Test-Path -LiteralPath (Join-Path $ws $candidate)){$rel=$candidate;break}
  }
  if($null -eq $rel){throw ('Missing native resource '+$depot)}
  Pin $rel;Pin ($rel.Replace('/raw/','/json/')+'.json');$dependencies[$depot]=[ordered]@{raw=$rel;raw_sha256=$pins[$rel];json=($rel.Replace('/raw/','/json/')+'.json');json_sha256=$pins[($rel.Replace('/raw/','/json/')+'.json')]}
 }
}
foreach($p in $spec.source_pins.PSObject.Properties){Pin $p.Name;if($pins[$p.Name] -cne $p.Value){throw 'Changed contract source'}}
$journalProof='research/sidejobs_s24/ep1/journal_variants_01/metadata_03.json'
foreach($p in @($Contract,'prealpha/sidejobs_s24/ep1/prepare_contract.py','prealpha/sidejobs_s24/ep1/inspect.py','prealpha/sidejobs_s24/ep1/build_component.ps1','prealpha/sidejobs_s24/ep1/test_component.py','prealpha/sidejobs_s24/ep1/extract.ps1','prealpha/sidejobs_s24/ep1/extract_journals.ps1','prealpha/sidejobs_s24/ep1/audit_transitions.py','prealpha/sidejobs_s24/ep1/verify_journal_variants.ps1','prealpha/sidejobs_s24/ep1/verify_journal_metadata.py',$journalProof,'research/sidejobs_s24/ep1/transition_01.json','tools/build_phase2a.ps1','tools/build_fresh_gigs_b5.ps1','research/q307_extracted/raw/base/quest/cyberpunk2077.questphase')){Pin $p}
$resourceMap=[ordered]@{};foreach($r in $resources){$resourceMap[$r.depot]=$r.sha256}
$m=[ordered]@{status='COMPONENT_BUILT_FRESH_ONLY_LIVE_PENDING';revision=$Revision;resources=$resourceMap;resource_details=@($resources.ToArray());boots=@($spec.owners|ForEach-Object {$_.depot});contract=$Contract;contract_sha256=$pins[$Contract];source_pins=$pins;native_copies=@($copies.ToArray());native_resources=$dependencies;journal_metadata=$journalProof;transition_proof='research/sidejobs_s24/ep1/transition_01.json';native_changes=@('Only mod boot edges; original parent payloads and internal nested edges exact','Original AddContact template copied for Fred/Ashley: target path adapted from native journal contact and sendNotification=false; only after fresh issued guard','No original quest resources overridden or gameplay/scenes/rewards changed');limitations=@('MQ306 original invitation delay and Moving Heat original delay restart; no old remaining-timer reconstruction','All three currently progressed/completed captured branches protected; future fresh-save live playtests required','Existing Aaron missing-contact partial repair parked; this fresh component does not repair it');native_progress_resets=$false;game_writes=$false}
[IO.File]::WriteAllText((Join-Path $out 'component.json'),($m|ConvertTo-Json -Depth 50),[Text.UTF8Encoding]::new($false))
[pscustomobject]$m|Select-Object status,revision,contract_sha256|ConvertTo-Json
