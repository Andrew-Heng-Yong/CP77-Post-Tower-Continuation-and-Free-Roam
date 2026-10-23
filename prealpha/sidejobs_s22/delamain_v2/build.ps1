param([string]$Revision='delamain_01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$WorkspaceRoot=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $WorkspaceRoot 'tools/build_phase2a.ps1') -HelpersOnly
. (Join-Path $WorkspaceRoot 'tools/shark_b7_2_helpers.ps1')
$helper=Get-Content (Join-Path $WorkspaceRoot 'tools/build_fresh_gigs_b5.ps1') -Raw
$begin=$helper.IndexOf('function ClearB5(');$end=$helper.IndexOf('$allRoots=@{};')
if($begin -lt 0 -or $end -le $begin){throw 'Helper boundary changed'}
. ([scriptblock]::Create($helper.Substring($begin,$end-$begin)))
if($Revision -cnotmatch '^delamain_\d{2}$'){throw 'Bad revision'}
$out=Join-Path $PSScriptRoot ('build/'+$Revision)
if(Test-Path $out){throw 'Immutable build exists'}
New-Item -ItemType Directory $out,(Join-Path $out 'source'),(Join-Path $out 'readback')|Out-Null
$pins=[ordered]@{};$resources=[ordered]@{};$boots=@();$transforms=@()
function Pin($p){$pins[$p]=(Get-FileHash -LiteralPath (Join-Path $WorkspaceRoot $p)).Hash}
function Native($p){Pin $p;Pin ($p.Replace('/raw/','/json/')+'.json');return Read-Cr2wFile (Join-Path $WorkspaceRoot $p)}
foreach($p in @('prealpha/sidejobs_s22/delamain_v2/build.ps1','prealpha/sidejobs_s22/delamain_v2/admission.json','tools/build_phase2a.ps1','tools/build_fresh_gigs_b5.ps1','tools/shark_b7_2_helpers.ps1','research/q307_extracted/raw/base/quest/cyberpunk2077.questphase')){Pin $p}
function CopyGraph($g,$ids){
 $new=[WolvenKit.RED4.Types.questGraphDefinition]::new()
 foreach($id in $ids){$o=Get-QuestNode $g $id;$n=$o.DeepCopy();ClearB5 $n
  if($n -is [WolvenKit.RED4.Types.questPhaseNodeDefinition] -and $null -ne $n.PhaseGraph -and $null -ne $n.PhaseGraph.Chunk){RewireB5 $n.PhaseGraph.Chunk $o.PhaseGraph.Chunk};AddNodeB5 $new $n
 };return $new
}
function JournalPath($path,$class){$p=[WolvenKit.RED4.Types.gameJournalPath]::new();$p.RealPath=$path;$p.ClassName=$class;$p.FileEntryIndex=2;return $p}
function JournalState($path,$class,$state){
 $t=[WolvenKit.RED4.Types.questJournalEntryState_ConditionType]::new();Set-RedHandleProperty $t Path (JournalPath $path $class);$t.State=[Enum]::Parse([WolvenKit.RED4.Types.Enums+gameJournalEntryState],$state)
 $c=[WolvenKit.RED4.Types.questJournalCondition]::new();Set-RedHandleProperty $c Type $t;return $c
}
function JournalNode($id,$path,$class){
 $n=[WolvenKit.RED4.Types.questJournalNodeDefinition]::new();$n.Id=[uint16]$id
 $t=[WolvenKit.RED4.Types.questJournalQuestEntry_NodeType]::new();Set-RedHandleProperty $t Path (JournalPath $path $class);$t.SendNotification=$false;$t.TrackQuest=$false;Set-RedHandleProperty $n Type $t
 foreach($port in @('Active','Inactive','Succeeded','Failed')){[void](New-QuestSocket $n $port ([WolvenKit.RED4.Types.Enums+questSocketType]::Input))}
 [void](New-QuestSocket $n 'Out' ([WolvenKit.RED4.Types.Enums+questSocketType]::Output));return $n
}
function SaveRoot($r,$label,$inject=$false,$depot=''){
 if(!$depot){$depot='towercontinued\sidejobs_s22\delamain\'+$label+'.questphase'}
 $f=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$f.RootChunk=$r
 $raw=Join-Path (Join-Path $out 'source') $depot;Write-Cr2wFile $f $raw
 Export-Cr2wJson (Read-Cr2wFile $raw) (Join-Path $out ('readback/'+$label+'.json'))
 $resources[$depot]=(Get-FileHash $raw).Hash;if($inject){$script:boots+=,$depot}
}
function SaveGraph($g,$label,$inject=$false,$depot=''){$r=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();Set-RedHandleProperty $r Graph $g;SaveRoot $r $label $inject $depot}
$common=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;PTFRPA2_Finished=1;PTFRPA2_Fault=0;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;q307_active=0;q307_debug_reset=0;q115_point_of_no_return=0;q305_johnny_scene_active=0;PTFRU9_Support_Issued=1;PTFRU9_Support_Fault=0}
$a=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'admission.json') -Raw|ConvertFrom-Json
$pairs=[ordered]@{};foreach($k in $common.Keys){$pairs[$k]=$common[$k]};foreach($p in $a.facts_equal.PSObject.Properties){$pairs[$p.Name]=[int]$p.Value}
$pairs['PTFRS22_SQ025_Permit']=1;$pairs['PTFRS22_SQ025_Issued']=0;$pairs['PTFRS22_SQ025_Fault']=0
function Admission {
 $c=AllB5 $pairs
 foreach($j in $a.journals){$o=[WolvenKit.RED4.Types.questLogicalCondition]::new();$o.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::OR
  foreach($s in $j.states){$sn=@{1='Inactive';2='Active';3='Succeeded';4='Failed'}[[int]$s];Add-RedHandle $o.Conditions (JournalState $j.path $j.class $sn)};Add-RedHandle $c.Conditions $o
 };return $c
}
# One stock controller already contains the main contact and all seven personalities.
$initSource='research/gig_restoration/gig_phone_u9/sources/raw/base/quest/holocalls/holocall_initializers.questphase'
$init=(Native $initSource).RootChunk.Graph.Chunk
$idle=[ordered]@{};foreach($k in @('holo_setup_active','holo_setup_started','holo_interrupt_call','holo_active_call_interrupted','holo_reset','holo_force_reset','holo_reset_soft','holo_interrupt_call_manual','holo_interrupt_braindance')){$idle[$k]=0}
$contacts=@('delamain','delamain_angry','delamain_sad','delamain_mean','delamain_manic','delamain_scared','delamain_deep','delamain_suicidal');$balances=@()
foreach($contact in $contacts){foreach($dir in @(($contact+'_calls_v'),('v_calls_'+$contact))){
 foreach($kind in @('start_activate','end_activate','active')){$idle['holo_'+$dir+'_'+$kind]=0};$balances+=,@(('holo_'+$dir+'_start_count'),('holo_'+$dir+'_end_count'))
}}
function Idle {$c=AllB5 $idle;foreach($b in $balances){Add-RedHandle $c.Conditions (EqB5 $b[0] $b[1])};return $c}
function SupportAdmission {$c=Admission;Add-RedHandle $c.Conditions (Idle);Add-RedHandle $c.Conditions (New-FactCondition 'PTFRS22_SQ025_SupportIssued' 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal));return $c}
$sg=CopyGraph $init @(51)
foreach($n in @((New-InputNode 1000 'In1'),(New-SetFactNode 1001 'PTFRS22_SQ025_SupportReady' 1),(PauseB5 1002 (SupportAdmission)),(New-ConditionNode 1003 (SupportAdmission)),(New-SetFactNode 1004 'PTFRS22_SQ025_SupportIssued' 1))){AddNodeB5 $sg $n}
RebuildB5 $sg @(@(1000,'Out',1001,'In'),@(1001,'Out',1002,'In'),@(1002,'Out',1003,'In'),@(1003,'False',1002,'In'),@(1003,'True',1004,'In'),@(1004,'Out',51,'In1'))
SaveGraph $sg 'support' $true
# Extend only the currently winning C1 cleanup, after BOTH Daniels branch exits.
$oldCleanup='prealpha/courier_c1/build/c1_02/source/towercontinued/gig_phone_u9/fixer_cleanup.questphase';Pin $oldCleanup
$old=(Read-Cr2wFile (Join-Path $WorkspaceRoot $oldCleanup)).RootChunk.Graph.Chunk
$cs='research/gig_restoration/gig_phone_u9/sources/raw/base/quest/holocalls/holocall_cleanup.questphase';$nc=(Native $cs).RootChunk.Graph.Chunk
$cg=CopyGraph $old @($old.Nodes|ForEach-Object {[int]$_.Chunk.Id.ToString()})
foreach($x in @(@(438,700),@(302,701))){$n=(Get-QuestNode $nc $x[0]).DeepCopy();ClearB5 $n;$n.Id=[uint16]$x[1];AddNodeB5 $cg $n}
$ce=@(EdgesB5 $old|ForEach-Object {$_});$redirects=0
foreach($e in $ce){if($e[0] -in @(600,601) -and $e[2] -eq 6){$e[2]=700;$e[3]='In';$redirects++}}
if($redirects -ne 2){throw 'C1 cleanup boundaries changed'}
$ce+=,@(700,'True',701,'In12');$ce+=,@(700,'False',6,'In2');$ce+=,@(701,'Out12',6,'In2');RebuildB5 $cg $ce
SaveGraph $cg 'fixer_cleanup' $false 'towercontinued\gig_phone_u9\fixer_cleanup.questphase'
# Preserve every stock scan payload; change only completed-leg admission and
# cleanup's attempts to hide already-succeeded sibling roots.
$scanSource='research/activity_state_r3/native_sources/raw/base/quest/side_quests/sq025/phases/sq025_04_scan.questphase'
$scan=Native $scanSource;$sr=$scan.RootChunk.DeepCopy();RewireB5 $sr.Graph.Chunk $scan.RootChunk.Graph.Chunk;$g=$sr.Graph.Chunk
$legs=@(
 @{name='angry';root='sq025c01_angry';slot=1;delay=259},@{name='sad';root='sq025c02_sad';slot=2;delay=260},
 @{name='mean';root='sq025c03_mean';slot=3;delay=261},@{name='manic';root='sq025c04_manic';slot=4;delay=263},
 @{name='scared';root='sq025c05_scared';slot=5;delay=264},@{name='deep';root='sq025c06_mean';slot=6;delay=265},
 @{name='suicidal';root='sq025c07_suicidal';slot=7;delay=266})
$se=@(EdgesB5 $g|ForEach-Object {$_})
foreach($leg in $legs){
 $id=1000+$leg.slot;$c=AllB5 ([ordered]@{('sq025_'+$leg.name+'_done')=1});Add-RedHandle $c.Conditions (JournalState ('quests/side_quest/'+$leg.root) 'gameJournalQuest' 'Succeeded')
 AddNodeB5 $g (New-ConditionNode $id $c)
 foreach($e in $se){if($e[0] -eq 195 -and $e[2] -eq $leg.delay){$e[2]=$id;$e[3]='In'}}
 $se+=,@($id,'True',198,('In'+$leg.slot));$se+=,@($id,'False',$leg.delay,'In')
}
RebuildB5 $g $se
$hide=(Get-QuestNode $g 267).PhaseGraph.Chunk;$he=@(EdgesB5 $hide|ForEach-Object {$_})
foreach($jid in @(2,3,4,5,6,7,8)){
 $jn=Get-QuestNode $hide $jid;$path=$jn.Type.Chunk.Path.Chunk.RealPath.ToString();$next=@($he|Where-Object {$_[0] -eq $jid})
 if($next.Count -ne 1){throw 'Native cleanup successor changed'}
 $id=100+$jid;AddNodeB5 $hide (New-ConditionNode $id (JournalState $path 'gameJournalQuest' 'Succeeded'))
 foreach($e in $he){if($e[2] -eq $jid){$e[2]=$id;$e[3]='In'}}
 $he+=,@($id,'False',$jid,'Inactive');$he+=,@($id,'True',$next[0][2],$next[0][3])
}
RebuildB5 $hide $he;SaveRoot $sr 'scan'
# Retain the original scan, reward, damage/failure owner, and traffic lease.
# Deliberately no reception/briefing, post-Epistrophy messages or sequel phases.
$parentSource='research/activity_state_r3/native_sources/raw/base/quest/side_quests/sq025/sq025.questphase'
$pn=Native $parentSource;$ng=$pn.RootChunk.Graph.Chunk
$ids=@(79,114,124,142,143,145,147,160,170,126)
$pg=CopyGraph $ng $ids
(Get-QuestNode $pg 79).PhaseResource=[WolvenKit.RED4.Types.CResourceAsyncReference`1[WolvenKit.RED4.Types.questQuestPhaseResource]]::new('towercontinued\sidejobs_s22\delamain\scan.questphase')
# Traffic lease is the exact stock local loop, not its unrelated briefing retry
# or compensation/regular-crowd failure subtree.
$traffic=(Get-QuestNode $ng 147).PhaseGraph.Chunk;$tids=@(0,1,3,4,10,11,12,14,15,16,17,18,19,65)
$tg=CopyGraph $traffic $tids;$te=@(EdgesB5 $traffic|ForEach-Object {$_}|Where-Object {$_[0] -in $tids -and $_[2] -in $tids});$te+=,@(0,'Out',65,'In');RebuildB5 $tg $te;Set-RedHandleProperty (Get-QuestNode $pg 147) PhaseGraph $tg
function EntryAdmission {$c=Admission;Add-RedHandle $c.Conditions (Idle);Add-RedHandle $c.Conditions (New-FactCondition 'PTFRS22_SQ025_SupportIssued' 1 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal));return $c}
$rootpath='quests/side_quest/sq025_delamain'
$scanpath=$rootpath+'/03_scan';$scanobjective=$scanpath+'/03_02_scan_delamains'
$post=AllB5 ([ordered]@{PTFRS22_SQ025_Issued=1})
Add-RedHandle $post.Conditions (JournalState $rootpath 'gameJournalQuest' 'Active')
Add-RedHandle $post.Conditions (JournalState $scanpath 'gameJournalQuestPhase' 'Active')
Add-RedHandle $post.Conditions (JournalState $scanobjective 'gameJournalQuestObjective' 'Active')
foreach($j in @($a.journals|Where-Object {$_.states.Count -eq 1 -and $_.states[0] -eq 3})){Add-RedHandle $post.Conditions (JournalState $j.path $j.class 'Succeeded')}
foreach($n in @((New-InputNode 1000 'In1'),(New-SetFactNode 1001 'PTFRS22_SQ025_Ready' 1),(PauseB5 1002 (EntryAdmission)),(New-ConditionNode 1003 (EntryAdmission)),(New-SetFactNode 1004 'PTFRS22_SQ025_Issued' 1),(JournalNode 1005 $rootpath 'gameJournalQuest'),(PauseB5 1006 $post),(New-SetFactNode 1007 'PTFRS22_SQ025_Entered' 1),(New-SetFactNode 1008 'PTFRS22_SQ025_Finished' 1),(New-SetFactNode 1009 'PTFRS22_SQ025_Fault' 1))){AddNodeB5 $pg $n}
# Explicitly prepare the failed scan parent and objective. The original entry
# activates the objective only; do not assume implicit parent-state recovery.
AddNodeB5 $pg (JournalNode 1013 $scanpath 'gameJournalQuestPhase')
AddNodeB5 $pg (JournalNode 1014 $scanobjective 'gameJournalQuestObjective')
$pe=@(EdgesB5 $ng|ForEach-Object {$_}|Where-Object {$_[0] -in $ids -and $_[2] -in $ids})
$pe+=,@(1000,'Out',1001,'In');$pe+=,@(1001,'Out',1002,'In');$pe+=,@(1002,'Out',1003,'In');$pe+=,@(1003,'False',1002,'In');$pe+=,@(1003,'True',1004,'In');$pe+=,@(1004,'Out',1005,'Active');$pe+=,@(1005,'Out',1013,'Active');$pe+=,@(1013,'Out',1014,'Active');$pe+=,@(1014,'Out',1006,'In');$pe+=,@(1006,'Out',1007,'In')
$pe+=,@(1007,'Out',79,'main_in');$pe+=,@(1007,'Out',114,'In1');$pe+=,@(1007,'Out',142,'In1');$pe+=,@(1007,'Out',147,'In1');$pe+=,@(124,'Out1',1008,'In');$pe+=,@(126,'Out',1009,'In')
# Stock final scanner-return cleanup completed; release only the local traffic
# lease. Do not start SQ025's excluded resurgence chain or end its global history.
$cut=[WolvenKit.RED4.Types.questCutControlNodeDefinition]::new();$cut.Id=[uint16]1010
foreach($port in @(@('In','Input'),@('Out','Output'),@('CutSource','CutSource'))){[void](New-QuestSocket $cut $port[0] ([Enum]::Parse([WolvenKit.RED4.Types.Enums+questSocketType],$port[1])))}
AddNodeB5 $pg $cut
foreach($x in @(@(18,1011),@(14,1012))){$n=(Get-QuestNode $traffic $x[0]).DeepCopy();ClearB5 $n;$n.Id=[uint16]$x[1];AddNodeB5 $pg $n}
$pe+=,@(1008,'Out',1010,'In');$pe+=,@(1010,'CutSource',147,'CutDestination');$pe+=,@(1010,'CutSource',142,'CutDestination');$pe+=,@(1010,'CutSource',114,'CutDestination');$pe+=,@(1010,'Out',1011,'In');$pe+=,@(1011,'Out',1012,'In')
RebuildB5 $pg $pe;SaveGraph $pg 'owner' $true
foreach($dep in @('dependencies_01','dependencies_02')){foreach($p in Get-ChildItem (Join-Path $WorkspaceRoot ('research/sidejobs_s22/delamain/'+$dep+'/raw')) -Recurse -File){$rel=[IO.Path]::GetRelativePath($WorkspaceRoot,$p.FullName).Replace('\','/');Pin $rel;Pin ($rel.Replace('/raw/','/json/')+'.json')}}
Pin 'research/cyberpsycho_p1/scenes_01/raw/base/quest/side_quests/sq025/scenes/sq025_05_scan.scene'
Pin 'research/cyberpsycho_p1/scenes_01/json/base/quest/side_quests/sq025/scenes/sq025_05_scan.scene.json'
$result=[ordered]@{status='EXPORTED_S22_DELAMAIN_NOT_PACKAGED_OR_INSTALLED';resources=$resources;boots=$boots;source_pins=$pins;admission=$a;common_equal=$common;phone_idle_equal=$idle;phone_balances=$balances;parent_source=$parentSource;parent_selected=$ids;scan_source=$scanSource;legs=$legs;cleanup_source=$cs;cleanup_previous=$oldCleanup;cleanup_override='towercontinued\gig_phone_u9\fixer_cleanup.questphase';phone_init_source=$initSource;native_scenes_unchanged=$true;excluded_sequel_connected=$false;runtime_scripts_added=0;game_writes=0;save_writes=0;scope='Bounded 3-of-7 Epistrophy resume, completed-leg preservation, original remaining4scenes/rewards/finalscanner-return; native Delamain8identitycontact and cleanup. Other progress shapes are not admitted.'}
[IO.File]::WriteAllText((Join-Path $out 'build.json'),($result|ConvertTo-Json -Depth 35),[Text.UTF8Encoding]::new($false))
@{status=$result.status;build=$out;sha256=(Get-FileHash (Join-Path $out 'build.json')).Hash}|ConvertTo-Json

