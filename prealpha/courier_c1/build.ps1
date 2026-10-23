param([string]$Revision='c1_01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$WorkspaceRoot=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $WorkspaceRoot 'tools/build_phase2a.ps1') -HelpersOnly
. (Join-Path $WorkspaceRoot 'tools/shark_b7_2_helpers.ps1')
$helper=Get-Content (Join-Path $WorkspaceRoot 'tools/build_fresh_gigs_b5.ps1') -Raw
$begin=$helper.IndexOf('function ClearB5(');$end=$helper.IndexOf('$allRoots=@{};')
if($begin -lt 0 -or $end -le $begin){throw 'Helper boundary changed'}
. ([scriptblock]::Create($helper.Substring($begin,$end-$begin)))
if($Revision -cnotmatch '^c1_\d{2}$'){throw 'Invalid revision'}
$out=Join-Path $PSScriptRoot ('build/'+$Revision)
if(Test-Path $out){throw 'Immutable build exists; use a new revision'}
New-Item -ItemType Directory $out,(Join-Path $out 'source'),(Join-Path $out 'readback')|Out-Null
$pins=[ordered]@{};$resources=[ordered]@{};$boots=@()
function Pin([string]$rel){$pins[$rel]=(Get-FileHash -LiteralPath (Join-Path $WorkspaceRoot $rel)).Hash}
function Native([string]$rel){Pin $rel;Pin ($rel.Replace('/raw/','/json/')+'.json');return Read-Cr2wFile (Join-Path $WorkspaceRoot $rel)}
foreach($p in @('prealpha/courier_c1/build.ps1','prealpha/courier_c1/research.py','tools/build_phase2a.ps1','tools/build_fresh_gigs_b5.ps1','tools/shark_b7_2_helpers.ps1','tools/gig_family_b7_1_xl.ps1','tools/afterlife_faces_r5_deployment.ps1','research/q307_extracted/raw/base/quest/cyberpunk2077.questphase','research/q307_extracted/json/ep1/quest/ep1.quest.json')){Pin $p}
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
B71Parser|Out-Null;$inventory=@(B72Inventory $game)
$stock=Get-Content (Join-Path $WorkspaceRoot 'research/q307_extracted/json/ep1/quest/ep1.quest.json') -Raw|ConvertFrom-Json
$used=@($stock.Data.RootChunk.graph.Data.nodes.Data.id)+@($inventory.id)
function SaveC1($g,[string]$depot,[string]$label,[bool]$inject){
 $root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();Set-RedHandleProperty $root Graph $g
 $f=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$f.RootChunk=$root
 $raw=Join-Path (Join-Path $out 'source') $depot;Write-Cr2wFile $f $raw
 Export-Cr2wJson (Read-Cr2wFile $raw) (Join-Path $out ('readback/'+$label+'.json'))
 $resources[$depot]=(Get-FileHash $raw).Hash
 if($inject){
  $id=B72Id ($depot+':1')
  if($id -in $script:used -or $id -ne (B72IdIndependent ($depot+':1'))){throw "Injection collision $depot"}
  $script:used+=,$id;$script:boots+=,$depot
 }
}
function CopyC1($source,$ids){
 $g=[WolvenKit.RED4.Types.questGraphDefinition]::new()
 foreach($id in $ids){
  $original=Get-QuestNode $source $id;$n=$original.DeepCopy();ClearB5 $n
  if($n -is [WolvenKit.RED4.Types.questPhaseNodeDefinition] -and $null -ne $n.PhaseGraph -and $null -ne $n.PhaseGraph.Chunk){RewireB5 $n.PhaseGraph.Chunk $original.PhaseGraph.Chunk}
  AddNodeB5 $g $n
 };return $g
}
$common=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;PTFRPA2_Finished=1;PTFRPA2_Fault=0;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;q307_active=0;q307_debug_reset=0;q115_point_of_no_return=0;q305_johnny_scene_active=0;PTFRU9_Support_Issued=1;PTFRU9_Support_Fault=0}
$positive=@('ep1_installed','ep1_active','ep1_side_content')
function PositiveC1($c){foreach($k in $positive){Add-RedHandle $c.Conditions (New-FactCondition $k 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Greater))}}
# A single additional native contact, sharing the already-running U9 phone and
# interrupt owner. Do not restart the broad EP1 phone initializer.
$phoneSource='research/courier_c1/phone_09/raw/ep1/quest/holocalls/holocall_initializers_ep1.questphase'
$init=(Native $phoneSource).RootChunk.Graph.Chunk
$supportPairs=[ordered]@{};foreach($k in $common.Keys){$supportPairs[$k]=$common[$k]}
$supportPairs['PTFRC1_Support_Issued']=0
foreach($k in @('holo_setup_active','holo_setup_started','holo_interrupt_call','holo_active_call_interrupted','holo_reset','holo_force_reset','holo_reset_soft','holo_interrupt_call_manual','holo_interrupt_braindance','holo_officer_daniels_calls_v_start_activate','holo_officer_daniels_calls_v_end_activate','holo_v_calls_officer_daniels_start_activate','holo_v_calls_officer_daniels_end_activate','audio_officer_daniels_calls_v_start_activate','audio_officer_daniels_calls_v_end_activate','audio_v_calls_officer_daniels_start_activate','audio_v_calls_officer_daniels_end_activate')){$supportPairs[$k]=0}
$balances=@(@('holo_officer_daniels_calls_v_start_count','holo_officer_daniels_calls_v_end_count'),@('holo_v_calls_officer_daniels_start_count','holo_v_calls_officer_daniels_end_count'))
function SupportGuard {$c=AllB5 $supportPairs;PositiveC1 $c;foreach($p in $balances){Add-RedHandle $c.Conditions (EqB5 $p[0] $p[1])};return $c}
$sg=CopyC1 $init @(22)
foreach($n in @((New-InputNode 0 'In1'),(New-SetFactNode 1 'PTFRC1_Support_Ready' 1),(PauseB5 2 (SupportGuard)),(New-ConditionNode 3 (SupportGuard)),(New-SetFactNode 4 'PTFRC1_Support_Issued' 1))){AddNodeB5 $sg $n}
RebuildB5 $sg @(@(0,'Out',1,'In'),@(1,'Out',2,'In'),@(2,'Out',3,'In'),@(3,'False',2,'In'),@(3,'True',4,'In'),@(4,'Out',22,'In1'))
SaveC1 $sg 'towercontinued\courier_c1\support.questphase' 'support' $true
# Exact courier-only slice of the stock sandbox parent. Its normal start and
# retrofix/cleanup/restart branches stay together; no airdrops/cyberjunkies/tests.
$parentSource='research/courier_c1/parents_02/raw/ep1/openworld/sandbox_activities/ep1_sandbox_activities.questphase'
$parent=(Native $parentSource).RootChunk.Graph.Chunk
$ids=@(3,15,21,22,23,25,26,27,28,29,30,33,34,35,36,37,38,41,42,43,44,45,46,47,48)
$g=CopyC1 $parent $ids
$pairs=[ordered]@{};foreach($k in $common.Keys){$pairs[$k]=$common[$k]}
$pairs['PTFRC1_Support_Issued']=1;$pairs['PTFRC1_Issued']=0
foreach($k in @('sa_ep1_couriers_active','sa_ep1_courier_car_mounted_1st_time','sa_ep1_courier_hacking_mounted_1st_time','sa_ep1_courier_hacking_mission_active','sa_ep1_courier_introduction_quest_active','sa_ep1_courier_outro_active','sa_ep1_courier_loop_blocked_by_outro','sa_ep1_courier_force_despawn_and_block','sa_ep1_courier_holocall_status_active','sa_ep1_courier_external_tests','sa_ep1_courier_retrofixing_fullreset','sa_ep1_courier_retrofixing_killallsignals','sa_ep1_courier_retrofixing_killdistrictssignal','sa_ep1_courier_retrofixing_killmainphase','sa_ep1_courier_retrofixing_killloopphase','sa_ep1_courier_retrofixing_signal_inject','sa_ep1_courier_retrofixing_reactivate_signal')){$pairs[$k]=0}
function CourierGuard {
 $c=AllB5 $pairs;PositiveC1 $c
 $intro=[WolvenKit.RED4.Types.questLogicalCondition]::new();$intro.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::OR
 Add-RedHandle $intro.Conditions (New-FactCondition 'sa_ep1_courier_introduction_quest_finished' 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Greater))
 Add-RedHandle $intro.Conditions (New-FactCondition 'sa_ep1_courier_introduction_quest_started' 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
 Add-RedHandle $c.Conditions $intro
 $outro=[WolvenKit.RED4.Types.questLogicalCondition]::new();$outro.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::OR
 foreach($k in @('sa_ep1_courier_outro_finished','sa_ep1_courier_outro_failed')){Add-RedHandle $outro.Conditions (New-FactCondition $k 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Greater))}
 Add-RedHandle $outro.Conditions (New-FactCondition 'sa_ep1_courier_outro_available' 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
 Add-RedHandle $c.Conditions $outro
 return $c
}
foreach($n in @((New-InputNode 1000 'In1'),(New-SetFactNode 1001 'PTFRC1_Ready' 1),(PauseB5 1002 (CourierGuard)),(New-ConditionNode 1003 (CourierGuard)),(New-SetFactNode 1004 'PTFRC1_Issued' 1))){AddNodeB5 $g $n}
$edges=@(EdgesB5 $parent|ForEach-Object {$_}|Where-Object {$_[0] -in $ids -and $_[2] -in $ids})
$edges+=,@(1000,'Out',1001,'In');$edges+=,@(1001,'Out',1002,'In');$edges+=,@(1002,'Out',1003,'In');$edges+=,@(1003,'False',1002,'In');$edges+=,@(1003,'True',1004,'In')
$edges+=,@(1004,'Out',3,'start');$edges+=,@(1004,'Out',15,'In1')
RebuildB5 $g $edges
SaveC1 $g 'towercontinued\courier_c1\courier.questphase' 'courier' $true
# Extend, do not replace/reset, the existing eight-fixer + NCPD cleanup chain.
# The native Daniels balanced-call check/inline cleanup follows those contacts.
$oldCleanup='prealpha/ncpd_scanner_n1/build/n1_01/source/towercontinued/gig_phone_u9/fixer_cleanup.questphase';Pin $oldCleanup
$old=(Read-Cr2wFile (Join-Path $WorkspaceRoot $oldCleanup)).RootChunk.Graph.Chunk
$cleanupSource='research/courier_c1/phone_09/raw/ep1/quest/holocalls/holocall_cleanup_ep1.questphase'
$nativeCleanup=(Native $cleanupSource).RootChunk.Graph.Chunk
$cg=CopyC1 $old @($old.Nodes|ForEach-Object {[int]$_.Chunk.Id.ToString()})
foreach($id in @(84,83)){
 $src=Get-QuestNode $nativeCleanup $id;$n=$src.DeepCopy();ClearB5 $n
 if($id -eq 83){RewireB5 $n.PhaseGraph.Chunk $src.PhaseGraph.Chunk}
 $n.Id=[uint16]$(if($id -eq 84){600}else{601});AddNodeB5 $cg $n
}
$ce=@(EdgesB5 $old|ForEach-Object {$_});$redirects=0
foreach($e in $ce){if($e[0] -eq 424 -and $e[2] -eq 6){$e[2]=600;$e[3]='In';$redirects++}}
if($redirects -ne 1){throw 'N1 cleanup boundary changed'}
$ce+=,@(600,'True',601,'In1');$ce+=,@(600,'False',6,'In2');$ce+=,@(601,'Out1',6,'In2')
RebuildB5 $cg $ce
$cleanupDepot='towercontinued\gig_phone_u9\fixer_cleanup.questphase';SaveC1 $cg $cleanupDepot 'fixer_cleanup' $false
# Pin every audited original dependency, but pack only the three owned graphs.
foreach($p in Get-ChildItem (Join-Path $WorkspaceRoot 'research/courier_c1') -Recurse -File|Where-Object {$_.FullName -match '[\\/]raw[\\/]'} ){
 $rel=[IO.Path]::GetRelativePath($WorkspaceRoot,$p.FullName).Replace('\','/');Pin $rel
 Pin ($rel.Replace('/raw/','/json/')+'.json')
}
$name='00_TowerContinued_Courier_C1.archive';$archive=Join-Path $out $name
$xl=B71Render $boots;B71Parse $xl|Out-Null
[IO.File]::WriteAllText(($archive+'.xl'),$xl,[Text.UTF8Encoding]::new($false))
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new((Join-Path $out 'source')),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -ne 'NoError' -or $packed.Files.Count -ne 3){throw 'Archive scope mismatch'}
foreach($entry in $packed.Files.Values){
 if(!$resources.Contains($entry.Name)){throw 'Unexpected packed resource'}
 $mem=[IO.MemoryStream]::new();try{$entry.Extract($mem);if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($mem.ToArray())) -cne $resources[$entry.Name]){throw 'Packed readback mismatch'}}finally{$mem.Dispose()}
}
$files=@();foreach($file in @($archive,($archive+'.xl'))){$files+=,@{relative='archive/pc/mod/'+[IO.Path]::GetFileName($file);sha256=(Get-FileHash $file).Hash}}
$result=[ordered]@{status='BUILT_C1_LIVE_PENDING';files=$files;resources=$resources;parent_source=$parentSource;selected_nodes=$ids;guard_equal=$pairs;guard_positive=$positive;support_guard=$supportPairs;support_balances=$balances;support_init=$phoneSource;cleanup_source=$cleanupSource;previous_cleanup=$oldCleanup;mod_override=$cleanupDepot;source_pins=$pins;installed_injections=$inventory;boots=$boots;packed_readback=$true;native_scenes_unchanged=$true;runtime_scripts_added=0;official_overrides=@();game_writes=0;save_writes=0;scope='Native courier-only sandbox branch and one native Daniels phone controller. Original introduction, repeatable delivery/rewards/cooldowns, eligible future outro and cleanup. No unfinished delivery/story migration, forced history, or global phone restart.'}
[IO.File]::WriteAllText((Join-Path $out 'build.json'),($result|ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false))
@{status=$result.status;build=$out;sha256=(Get-FileHash (Join-Path $out 'build.json')).Hash}|ConvertTo-Json
