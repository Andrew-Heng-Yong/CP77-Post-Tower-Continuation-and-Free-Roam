param([string]$Revision='p1_01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$WorkspaceRoot=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $WorkspaceRoot 'tools/build_phase2a.ps1') -HelpersOnly
. (Join-Path $WorkspaceRoot 'tools/shark_b7_2_helpers.ps1')
$helper=Get-Content (Join-Path $WorkspaceRoot 'tools/build_fresh_gigs_b5.ps1') -Raw
$begin=$helper.IndexOf('function ClearB5(');$end=$helper.IndexOf('$allRoots=@{};')
if($begin -lt 0 -or $end -le $begin){throw 'Helper boundary changed'}
. ([scriptblock]::Create($helper.Substring($begin,$end-$begin)))
if($Revision -cnotmatch '^p1_\d{2}$'){throw 'Invalid revision'}
$out=Join-Path $PSScriptRoot ('build/'+$Revision)
if(Test-Path $out){throw 'Immutable build exists'}
New-Item -ItemType Directory $out,(Join-Path $out 'source'),(Join-Path $out 'readback')|Out-Null
$pins=[ordered]@{};$resources=[ordered]@{};$boots=@();$rows=@()
function Pin($p){$pins[$p]=(Get-FileHash -LiteralPath (Join-Path $WorkspaceRoot $p)).Hash}
function Native($p){Pin $p;Pin ($p.Replace('/raw/','/json/')+'.json');return Read-Cr2wFile (Join-Path $WorkspaceRoot $p)}
foreach($p in @('prealpha/cyberpsycho_p1/build.ps1','prealpha/cyberpsycho_p1/init.lua','prealpha/cyberpsycho_p1/prepare.py','prealpha/cyberpsycho_p1/catalog.py','research/cyberpsycho_p1/catalog_v1.json','research/cyberpsycho_p1/test_data_v1.json','tools/build_phase2a.ps1','tools/build_fresh_gigs_b5.ps1','tools/shark_b7_2_helpers.ps1','tools/gig_family_b7_1_xl.ps1','tools/afterlife_faces_r5_deployment.ps1','research/q307_extracted/raw/base/quest/cyberpunk2077.questphase','research/q307_extracted/json/ep1/quest/ep1.quest.json')){Pin $p}
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
B71Parser|Out-Null;$inventory=@(B72Inventory $game)
$stock=Get-Content (Join-Path $WorkspaceRoot 'research/q307_extracted/json/ep1/quest/ep1.quest.json') -Raw|ConvertFrom-Json
$used=@($stock.Data.RootChunk.graph.Data.nodes.Data.id)+@($inventory.id)
function CopyGraph($g,$ids){
 $new=[WolvenKit.RED4.Types.questGraphDefinition]::new()
 foreach($id in $ids){$o=Get-QuestNode $g $id;$n=$o.DeepCopy();ClearB5 $n
  if($n -is [WolvenKit.RED4.Types.questPhaseNodeDefinition] -and $null -ne $n.PhaseGraph -and $null -ne $n.PhaseGraph.Chunk){RewireB5 $n.PhaseGraph.Chunk $o.PhaseGraph.Chunk};AddNodeB5 $new $n
 };return $new
}
function JournalPath($path,$class){$p=[WolvenKit.RED4.Types.gameJournalPath]::new();$p.RealPath=$path;$p.ClassName=$class;$p.FileEntryIndex=if($path.StartsWith('quests/')){2}else{1};return $p}
function JournalState($path,$class,$state){
 $t=[WolvenKit.RED4.Types.questJournalEntryState_ConditionType]::new();Set-RedHandleProperty $t Path (JournalPath $path $class);$t.State=[Enum]::Parse([WolvenKit.RED4.Types.Enums+gameJournalEntryState],$state)
 $c=[WolvenKit.RED4.Types.questJournalCondition]::new();Set-RedHandleProperty $c Type $t;return $c
}
function JournalNode($id,$path,$class){
 $n=[WolvenKit.RED4.Types.questJournalNodeDefinition]::new();$n.Id=[uint16]$id
 $t=if($path.StartsWith('quests/')){[WolvenKit.RED4.Types.questJournalQuestEntry_NodeType]::new()}else{[WolvenKit.RED4.Types.questJournalEntry_NodeType]::new()};Set-RedHandleProperty $t Path (JournalPath $path $class);$t.SendNotification=$false;Set-RedHandleProperty $n Type $t
 foreach($port in @('Active','Inactive','Succeeded','Failed')){[void](New-QuestSocket $n $port ([WolvenKit.RED4.Types.Enums+questSocketType]::Input))}
 [void](New-QuestSocket $n 'Out' ([WolvenKit.RED4.Types.Enums+questSocketType]::Output));return $n
}
function SaveGraph($g,$label){
 $depot='towercontinued\cyberpsycho_p1\'+$label+'.questphase'
 $r=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();Set-RedHandleProperty $r Graph $g
 $f=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$f.RootChunk=$r;$raw=Join-Path (Join-Path $out 'source') $depot
 Write-Cr2wFile $f $raw;Export-Cr2wJson (Read-Cr2wFile $raw) (Join-Path $out ('readback/'+$label+'.json'));$resources[$depot]=(Get-FileHash $raw).Hash
 $id=B72Id ($depot+':1');if($id -in $script:used -or $id -ne (B72IdIndependent ($depot+':1'))){throw "Injection collision $depot"};$script:used+=,$id;$script:boots+=,$depot
}
$common=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;PTFRPA2_Finished=1;PTFRPA2_Fault=0;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;q307_active=0;q307_debug_reset=0;q115_point_of_no_return=0;q305_johnny_scene_active=0;PTFRU9_Support_Issued=1;PTFRU9_Support_Fault=0;PTFRN1_Support_Issued=1;PTFRP1_TestPreparing=0}
function Pairs($tag){$p=[ordered]@{};foreach($k in $common.Keys){$p[$k]=$common[$k]};$p[$tag+'_Issued']=0;return $p}
function Wrap($g,$pairs,$condition,$tag,$port='In1'){
 $outer=[WolvenKit.RED4.Types.questGraphDefinition]::new()
 $c=AllB5 $pairs;if($null -ne $condition){Add-RedHandle $c.Conditions $condition}
 $phase=[WolvenKit.RED4.Types.questPhaseNodeDefinition]::new();$phase.Id=[uint16]5;Set-RedHandleProperty $phase PhaseGraph $g
 [void](New-QuestSocket $phase $port ([WolvenKit.RED4.Types.Enums+questSocketType]::Input));[void](New-QuestSocket $phase 'CutDestination' ([WolvenKit.RED4.Types.Enums+questSocketType]::CutDestination))
 foreach($n in @((New-InputNode 0 'In1'),(New-SetFactNode 1 ($tag+'_Ready') 1),(PauseB5 2 $c),(New-ConditionNode 3 ($c.DeepCopy())),(New-SetFactNode 4 ($tag+'_Issued') 1),$phase)){AddNodeB5 $outer $n}
 RebuildB5 $outer @(@(0,'Out',1,'In'),@(1,'Out',2,'In'),@(2,'Out',3,'In'),@(3,'False',2,'In'),@(3,'True',4,'In'),@(4,'Out',5,$port));return $outer
}
$catalog=Get-Content (Join-Path $WorkspaceRoot 'research/cyberpsycho_p1/catalog_v1.json') -Raw|ConvertFrom-Json
if($catalog.rows.Count -ne 17 -or $catalog.issues.Count){throw 'Catalog changed'}
$badlands=(Native 'research/ncpd_scanner_n1/parents_02/raw/base/open_world/minor_activities/badlands/badlands_minor_activities.questphase').RootChunk.Graph.Chunk
foreach($s in $catalog.rows){
 $parent=($s.parent -replace '\.json$','').Replace('/json/','/raw/');$nr=Native $parent;$ng=$nr.RootChunk.Graph.Chunk
 if($nr.RootChunk.PhasePrefabs.Count){throw 'Unexpected parent prefabs'}
 $tag='PTFRP1_'+$s.key;$pairs=Pairs $tag
 foreach($f in @($s.start_facts)+@($s.finish_facts)){if($f -ne 'ow_psychos_done'){$pairs[$f]=0}}
 if(!$s.start_facts.Count){throw 'Missing native start witness'}
 $fresh=[WolvenKit.RED4.Types.questLogicalCondition]::new();$fresh.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
 Add-RedHandle $fresh.Conditions (JournalState $s.pois[0].quest.realPath 'gameJournalQuest' 'Inactive')
 Add-RedHandle $fresh.Conditions (New-FactCondition 'ow_psychos_done' 17 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Less))
 Add-RedHandle $fresh.Conditions (New-FactCondition 'ow_psychos_done' 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::GreaterOrEqual))
 $guard=AllB5 $pairs;Add-RedHandle $guard.Conditions $fresh
 $g=CopyGraph $ng $s.selected_nodes;$ad=$s.admission_edges[0]
 if($s.admission_edges.Count -ne 1){throw 'Ambiguous admission'}
 $ee=@(EdgesB5 $ng|ForEach-Object {$_}|Where-Object {$_[0] -in $s.selected_nodes -and $_[2] -in $s.selected_nodes}|Where-Object {-not($_[0] -eq $ad[0] -and $_[1] -ceq $ad[1] -and $_[2] -eq $ad[2] -and $_[3] -ceq $ad[3])})
 # The outer wrapper claims its owner before the native tier waits. Recheck
 # progress with Issued=1 at the actual native admission edge.
 $recheckPairs=[ordered]@{};foreach($k in $pairs.Keys){$recheckPairs[$k]=$pairs[$k]};$recheckPairs[$tag+'_Issued']=1
 $rc=AllB5 $recheckPairs;Add-RedHandle $rc.Conditions ($fresh.DeepCopy())
 foreach($n in @((New-ConditionNode 1000 $rc),(JournalNode 1001 $s.pois[0].path 'gameJournalPointOfInterestMappin'),(New-SetFactNode 1002 ($tag+'_Refused') 1),(New-SetFactNode 1003 ($tag+'_Entered') 1))){AddNodeB5 $g $n}
 $ee+=,@($ad[0],$ad[1],1000,'In');$ee+=,@(1000,'False',1002,'In');$ee+=,@(1000,'True',1001,'Active');$ee+=,@(1001,'Out',1003,'In');$ee+=,@(1003,'Out',$ad[2],$ad[3])
 if($s.extra_parent_gate){
  $b=(Get-QuestNode $badlands 9).DeepCopy();ClearB5 $b;$b.Id=[uint16]1010;AddNodeB5 $g $b
  $inputEdges=@($ee|Where-Object {$_[0] -eq $s.input});$ee=@($ee|Where-Object {$_[0] -ne $s.input});$ee+=,@($s.input,'Out',1010,'In');foreach($e in $inputEdges){$ee+=,@(1010,'Out',$e[2],$e[3])}
 }
 RebuildB5 $g $ee;$entryPort=(Get-QuestNode $ng $s.input).SocketName.ToString()
 SaveGraph (Wrap $g $pairs $fresh $tag $entryPort) $s.key
 Native (($s.source -replace '\.json$','').Replace('/json/','/raw/'))|Out-Null
 $rows+=,@{key=$s.key;parent=$parent;source=$s.source;selected_nodes=$s.selected_nodes;admission_edge=$ad;guard_equal=$pairs;quest=$s.pois[0].quest.realPath;poi=$s.pois[0].path;extra_parent_gate=$s.extra_parent_gate}
}
$reportSource='research/cyberpsycho_p1/support_01/raw/base/open_world/phases/cyberpsychos/open_world_cyberpsychos.questphase'
$ng=(Native $reportSource).RootChunk.Graph.Chunk
$g=CopyGraph $ng @($ng.Nodes|ForEach-Object {[int]$_.Chunk.Id.ToString()});$ee=@(EdgesB5 $ng|ForEach-Object {$_}|Where-Object {$_[0] -ne 0 -and -not($_[0] -eq 112 -and $_[2] -ge 27 -and $_[2] -le 59) -and $_[0] -ne 113})
AddNodeB5 $g (New-ConditionNode 1000 (New-FactCondition 'ow_psychos_intro_done' 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal)))
$ee+=,@(0,'Out',1000,'In');$ee+=,@(1000,'True',63,'In');$ee+=,@(0,'Out',111,'In')
# Arm only FUTURE milestones. Re-entering a killed controller must not increment
# the journal counter again for the saved, already-completed milestone.
for($i=1;$i -le 17;$i++){$id=1010+$i;AddNodeB5 $g (New-ConditionNode $id (New-FactCondition 'ow_psychos_done' $i ([WolvenKit.RED4.Types.Enums+EComparisonType]::Less)));$ee+=,@(112,'Out1',$id,'In');$ee+=,@($id,'True',(25+2*$i),'In')}
$mq='quests/minor_quest/mq043_cyberpsychos';$mqphase=$mq+'/mq043_cyberpsychos/'
AddNodeB5 $g (New-ConditionNode 1040 (JournalState ($mqphase+'02_talk_regina') 'gameJournalQuestObjective' 'Active'))
$ee+=,@(113,'Out',1040,'In');$ee+=,@(1040,'True',84,'In1');$ee+=,@(1040,'False',9,'In')
RebuildB5 $g $ee
$pairs=Pairs 'PTFRP1_Report';$pairs['mq043_done']=0;$pairs['ow_psychos_reward_collected']=0
$alive=[WolvenKit.RED4.Types.questLogicalCondition]::new();$alive.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::OR
foreach($state in @('Inactive','Active')){Add-RedHandle $alive.Conditions (JournalState $mq 'gameJournalQuest' $state)}
SaveGraph (Wrap $g $pairs $alive 'PTFRP1_Report') 'report'
$bugSource='research/cyberpsycho_p1/support_02/raw/base/open_world/bugfixing/fixers/regina_bugfixing.questphase'
$bug=(Native $bugSource).RootChunk.Graph.Chunk
$g=CopyGraph $bug @(7,8);AddNodeB5 $g (New-InputNode 0 'In1');RebuildB5 $g @(@(0,'Out',7,'In1'),@(0,'Out',8,'In1'))
SaveGraph (Wrap $g (Pairs 'PTFRP1_Reward') ($alive.DeepCopy()) 'PTFRP1_Reward') 'reward'
# Explicit development fixture. Nothing below is reachable without the user's
# tokened CET request. It is NOT used for normal unfinished-content restoration.
$s=$catalog.rows|Where-Object key -eq 'ma_wat_kab_08';$mower=(Native (($s.source -replace '\.json$','').Replace('/json/','/raw/'))).RootChunk.Graph.Chunk
$fixture=Get-Content (Join-Path $WorkspaceRoot 'research/cyberpsycho_p1/test_data_v1.json') -Raw|ConvertFrom-Json
$g=[WolvenKit.RED4.Types.questGraphDefinition]::new();$ee=@();$last=0;AddNodeB5 $g (New-InputNode 0 'In1')
function Step($node,$port='In'){AddNodeB5 $g $node;$id=[int]$node.Id.ToString();$script:ee+=,@($script:last,'Out',$id,$port);$script:last=$id}
$id=10
foreach($oldId in @(3,8)){
 $base=Get-QuestNode (Get-QuestNode $mower 98).PhaseGraph.Chunk $oldId
 foreach($action in @('ResetKillCount','Respawn')){
  $n=$base.DeepCopy();ClearB5 $n;$n.Id=[uint16]$id;$id++
  foreach($a in $n.Actions){$a.Type.Chunk.Action=[Enum]::Parse([WolvenKit.RED4.Types.Enums+populationSpawnerObjectCtrlAction],$action)};Step $n
 }
}
foreach($p in $fixture.paths|Sort-Object {$_.path.Length} -Descending){if($p.class -eq 'gameJournalOnscreen'){continue};Step (JournalNode $id $p.path $p.class) 'Inactive';$id++}
Step (JournalNode $id 'quests/minor_quest/ma_wat_kab_08/ma_wat_kab_08' 'gameJournalQuestPhase') 'Inactive';$id++
foreach($p in @(@($mq,'gameJournalQuest'),@(($mq+'/mq043_cyberpsychos'),'gameJournalQuestPhase'),@(($mqphase+'01_help_regina'),'gameJournalQuestObjective'),@(($mqphase+'02_a_wait_regina'),'gameJournalQuestObjective'),@(($mqphase+'02_talk_regina'),'gameJournalQuestObjective'),@(($mqphase+'03_take_reward'),'gameJournalQuestObjective'))){Step (JournalNode $id $p[0] $p[1]) 'Inactive';$id++}
$counter=(Get-QuestNode $ng 58).DeepCopy();ClearB5 $counter;$counter.Id=[uint16]$id;Step $counter 'Decrement';$id++
foreach($f in @($fixture.facts)+@('mq043_done','ow_psychos_reward_collected','ow_psychos_killed')){Step (New-SetFactNode $id $f 0);$id++}
Step (New-SetFactNode $id 'ow_psychos_done' 16);$id++
Step (JournalNode $id ($mqphase+'01_help_regina') 'gameJournalQuestObjective') 'Active';$id++
Step (New-SetFactNode $id 'PTFRP1_TestResetDone' 1);$id++
Step (New-SetFactNode $id 'PTFRP1_TestPreparing' 0);$id++
# Refill only the named reward container, once, via the stock retrofix's
# ReInitContainers payload. Never touch player inventory or CP77 retrofix flags.
$retro=(Get-QuestNode $bug 13).PhaseGraph.Chunk
foreach($oldId in @(10,8,12,6)){$n=(Get-QuestNode $retro $oldId).DeepCopy();ClearB5 $n;$n.Id=[uint16]$id;Step $n;$id++}
Step (New-SetFactNode $id 'PTFRP1_TestCrateReady' 1)
RebuildB5 $g $ee
$pairs=Pairs 'PTFRP1_Test';$pairs['PTFRP1_TestPreparing']=1;$pairs['PTFRP1_TestRequest']=1;$pairs['ow_psychos_done']=17;$pairs['mq043_done']=1;$pairs['ow_psychos_reward_collected']=1;$pairs['PTFRP1_Report_Issued']=0;$pairs['PTFRP1_Reward_Issued']=0;$pairs['PTFRP1_ma_wat_kab_08_Issued']=0
$testCond=[WolvenKit.RED4.Types.questLogicalCondition]::new();$testCond.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
Add-RedHandle $testCond.Conditions (JournalState $mq 'gameJournalQuest' 'Succeeded');Add-RedHandle $testCond.Conditions (JournalState 'quests/minor_quest/ma_wat_kab_08' 'gameJournalQuest' 'Succeeded')
SaveGraph (Wrap $g $pairs $testCond 'PTFRP1_Test') 'test_only'
foreach($p in Get-ChildItem (Join-Path $WorkspaceRoot 'research/cyberpsycho_p1/scenes_01/raw') -Recurse -File){Native ([IO.Path]::GetRelativePath($WorkspaceRoot,$p.FullName).Replace('\','/'))|Out-Null}
Native 'research/fixer_offices_fo1/scenes/raw/base/open_world/fixers/reggie/scenes/reggie_default.scene'|Out-Null
$archive=Join-Path $out 'TowerContinued_Cyberpsycho_P1.archive';$xl=B71Render $boots;B71Parse $xl|Out-Null
[IO.File]::WriteAllText(($archive+'.xl'),$xl,[Text.UTF8Encoding]::new($false))
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new((Join-Path $out 'source')),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -ne 'NoError' -or $packed.Files.Count -ne 20){throw 'Archive scope mismatch'}
foreach($entry in $packed.Files.Values){if(!$resources.Contains($entry.Name)){throw 'Unexpected resource'};$mem=[IO.MemoryStream]::new();try{$entry.Extract($mem);if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($mem.ToArray())) -cne $resources[$entry.Name]){throw 'Packed readback mismatch'}}finally{$mem.Dispose()}}
Copy-Item (Join-Path $PSScriptRoot 'init.lua') (Join-Path $out 'init.lua');Copy-Item (Join-Path $WorkspaceRoot 'research/cyberpsycho_p1/test_data_v1.json') (Join-Path $out 'data.json')
$files=@();foreach($name in @('TowerContinued_Cyberpsycho_P1.archive','TowerContinued_Cyberpsycho_P1.archive.xl','init.lua','data.json')){$rel=if($name -like '*.archive*'){'archive/pc/mod/'+$name}else{'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_CyberpsychoP1/'+$name};$files+=,@{relative=$rel;sha256=(Get-FileHash (Join-Path $out $name)).Hash}}
$result=[ordered]@{status='BUILT_P1_LIVE_PENDING';files=$files;resources=$resources;activities=$rows;source_pins=$pins;installed_injections=$inventory;boots=$boots;packed_readback=$true;native_scenes_unchanged=$true;runtime_scripts_added=0;official_overrides=@();game_writes=0;save_writes=0;report_source=$reportSource;reward_source=$bugSource;common=$common;test_guard=$pairs;scope='17 native fresh-only psycho encounter slices, resumed stock reporting and reward handlers; explicit one-use completed-save test fixture, not a normal replay feature.'}
[IO.File]::WriteAllText((Join-Path $out 'build.json'),($result|ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false))
@{status=$result.status;build=$out;sha256=(Get-FileHash (Join-Path $out 'build.json')).Hash}|ConvertTo-Json
