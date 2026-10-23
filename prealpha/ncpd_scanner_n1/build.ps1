param([string]$Revision='n1_01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$WorkspaceRoot=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $WorkspaceRoot 'tools/build_phase2a.ps1') -HelpersOnly
. (Join-Path $WorkspaceRoot 'tools/shark_b7_2_helpers.ps1')
$helper=Get-Content (Join-Path $WorkspaceRoot 'tools/build_fresh_gigs_b5.ps1') -Raw
$begin=$helper.IndexOf('function ClearB5(');$end=$helper.IndexOf('$allRoots=@{};')
if($begin -lt 0 -or $end -le $begin){throw 'Helper boundary changed'}
. ([scriptblock]::Create($helper.Substring($begin,$end-$begin)))
if($Revision -cnotmatch '^n1_\d{2}$'){throw 'Invalid revision'}
$out=Join-Path $PSScriptRoot ('build/'+$Revision)
if(Test-Path $out){throw 'Immutable build exists; use a new revision'}
New-Item -ItemType Directory $out,(Join-Path $out 'source'),(Join-Path $out 'readback')|Out-Null
$pins=[ordered]@{};$resources=[ordered]@{};$boots=@();$rows=@()
function Pin([string]$rel){$pins[$rel]=(Get-FileHash -LiteralPath (Join-Path $WorkspaceRoot $rel)).Hash}
function Native([string]$rel){Pin $rel;Pin ($rel.Replace('/raw/','/json/')+'.json');return Read-Cr2wFile (Join-Path $WorkspaceRoot $rel)}
foreach($p in @('prealpha/ncpd_scanner_n1/build.ps1','tools/build_phase2a.ps1','tools/build_fresh_gigs_b5.ps1','tools/shark_b7_2_helpers.ps1','tools/gig_family_b7_1_xl.ps1','tools/afterlife_faces_r5_deployment.ps1','research/q307_extracted/raw/base/quest/cyberpunk2077.questphase','research/q307_extracted/json/ep1/quest/ep1.quest.json')){Pin $p}
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
B71Parser|Out-Null;$inventory=@(B72Inventory $game)
$stock=Get-Content (Join-Path $WorkspaceRoot 'research/q307_extracted/json/ep1/quest/ep1.quest.json') -Raw|ConvertFrom-Json
$used=@($stock.Data.RootChunk.graph.Data.nodes.Data.id)+@($inventory.id)
function SaveN1($g,[string]$depot,[string]$label,[bool]$inject){
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
function CopyN1($source,$ids){
 $g=[WolvenKit.RED4.Types.questGraphDefinition]::new()
 foreach($id in $ids){
  $original=Get-QuestNode $source $id;$n=$original.DeepCopy();ClearB5 $n
  if($n -is [WolvenKit.RED4.Types.questPhaseNodeDefinition] -and $null -ne $n.PhaseGraph -and $null -ne $n.PhaseGraph.Chunk){RewireB5 $n.PhaseGraph.Chunk $original.PhaseGraph.Chunk}
  AddNodeB5 $g $n
 };return $g
}
$common=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;PTFRPA2_Finished=1;PTFRPA2_Fault=0;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;q307_active=0;q307_debug_reset=0;q115_point_of_no_return=0;q305_johnny_scene_active=0;PTFRU9_Support_Issued=1;PTFRU9_Support_Fault=0}
$district='research/ncpd_scanner_n1/parents_02/raw/base/open_world/minor_activities/watson/little_china/little_china_minor_activities.questphase'
$ng=(Native $district).RootChunk.Graph.Chunk
$specs=@(
 @{key='ma_wat_lch_01';kind='Suspected Organized Crime';ids=@(0,31,74,34,30,36,73);map=34;child=30;input='In1';last=74;extra='ma_wat_lch_01_av_start_only'},
 @{key='ma_wat_lch_02';kind='Assault in Progress';ids=@(0,31,74,35,16,36,73);map=35;child=16;input='In2';last=74;extra=''},
 @{key='ma_wat_lch_03';kind='Reported Crime';ids=@(0,31,74,55,70,37,28,36,73);map=37;child=28;input='In1';last=70;extra=''}
)
foreach($s in $specs){
 $tag='PTFRN1_'+$s.key;$pairs=[ordered]@{};foreach($k in $common.Keys){$pairs[$k]=$common[$k]}
 $pairs['PTFRN1_Support_Issued']=1;$pairs[$tag+'_Issued']=0
 $pairs[$s.key+'_start']=0;$pairs[$s.key+'_finished']=0
 if($s.extra){$pairs[$s.extra]=0}
 $g=CopyN1 $ng $s.ids
 # The stock tier and side-content waits still control activation. Recheck fresh
 # state AFTER those waits and immediately before POI/owner entry.
 foreach($n in @((New-SetFactNode 1000 ($tag+'_Ready') 1),(PauseB5 1001 (AllB5 $pairs)),(New-ConditionNode 1003 (AllB5 $pairs)),(New-SetFactNode 1004 ($tag+'_Issued') 1),(New-SetFactNode 1005 ($tag+'_NativeOutput') 1),(New-SetFactNode 1006 ($tag+'_Refused') 1))){AddNodeB5 $g $n}
 $edges=@(EdgesB5 $ng|ForEach-Object {$_}|Where-Object {$_[0] -in $s.ids -and $_[2] -in $s.ids})
 $edges=@($edges|Where-Object {$_[0] -ne 0 -and -not ($_[0] -eq $s.last -and $_[2] -eq $s.map)})
 $edges+=,@(0,'Out',1000,'In');$edges+=,@(1000,'Out',1001,'In');$edges+=,@(1001,'Out',31,'In')
 $edges+=,@($s.last,'Out',1003,'In');$edges+=,@(1003,'True',1004,'In');$edges+=,@(1003,'False',1006,'In')
 $edges+=,@(1004,'Out',$s.map,'Active');$edges+=,@($s.child,'Out1',1005,'In')
 RebuildB5 $g $edges
 $nativeDepot=(Get-QuestNode $ng $s.child).PhaseResource.DepotPath.ToString()
 $source='research/ncpd_scanner_n1/encounters_02/raw/'+$nativeDepot.Replace('\','/');Native $source|Out-Null
 $depot='towercontinued\ncpd_scanner_n1\'+$s.key+'.questphase';SaveN1 $g $depot $s.key $true
 $rows+=,@{key=$s.key;kind=$s.kind;depot=$depot;injection_id=(B72Id ($depot+':1'));selected_nodes=$s.ids;map=$s.map;child=$s.child;input=$s.input;last=$s.last;source=$source;native_depot=$nativeDepot;guard_equal=$pairs}
}
# One native dispatcher controller and the original minor-activity token loop.
# The existing U9 global interrupt/reset owner is NOT restarted or duplicated.
$initSource='research/gig_restoration/gig_phone_u9/sources/raw/base/quest/holocalls/holocall_initializers.questphase'
$init=(Native $initSource).RootChunk.Graph.Chunk
$rootSource='research/ncpd_scanner_n1/parents_02/raw/base/open_world/minor_activities/open_world_minor_activities.questphase'
$nativeRoot=(Native $rootSource).RootChunk.Graph.Chunk
$supportPairs=[ordered]@{};foreach($k in $common.Keys){$supportPairs[$k]=$common[$k]}
$supportPairs['PTFRN1_Support_Issued']=0;$supportPairs['ma_token']=0
foreach($k in @('holo_setup_active','holo_setup_started','holo_interrupt_call','holo_active_call_interrupted','holo_reset','holo_force_reset','holo_reset_soft','holo_interrupt_call_manual','holo_interrupt_braindance','holo_ncpd_dispatcher_calls_v_start_activate','holo_ncpd_dispatcher_calls_v_end_activate','holo_v_calls_ncpd_dispatcher_start_activate','holo_v_calls_ncpd_dispatcher_end_activate','audio_ncpd_dispatcher_calls_v_start_activate','audio_ncpd_dispatcher_calls_v_end_activate','audio_v_calls_ncpd_dispatcher_start_activate','audio_v_calls_ncpd_dispatcher_end_activate')){$supportPairs[$k]=0}
$balances=@(@('holo_ncpd_dispatcher_calls_v_start_count','holo_ncpd_dispatcher_calls_v_end_count'),@('holo_v_calls_ncpd_dispatcher_start_count','holo_v_calls_ncpd_dispatcher_end_count'))
function SupportGuard {$c=AllB5 $supportPairs;foreach($p in $balances){Add-RedHandle $c.Conditions (EqB5 $p[0] $p[1])};return $c}
$sg=CopyN1 $init @(77)
$token=(Get-QuestNode $nativeRoot 24).DeepCopy();ClearB5 $token;RewireB5 $token.PhaseGraph.Chunk (Get-QuestNode $nativeRoot 24).PhaseGraph.Chunk;AddNodeB5 $sg $token
foreach($n in @((New-InputNode 0 'In1'),(New-SetFactNode 1 'PTFRN1_Support_Ready' 1),(PauseB5 2 (SupportGuard)),(New-ConditionNode 3 (SupportGuard)),(New-SetFactNode 4 'PTFRN1_Support_Issued' 1))){AddNodeB5 $sg $n}
RebuildB5 $sg @(@(0,'Out',1,'In'),@(1,'Out',2,'In'),@(2,'Out',3,'In'),@(3,'False',2,'In'),@(3,'True',4,'In'),@(4,'Out',77,'In1'),@(4,'Out',24,'In1'))
SaveN1 $sg 'towercontinued\ncpd_scanner_n1\support.questphase' 'support' $true
foreach($p in Get-ChildItem (Join-Path $WorkspaceRoot 'research/ncpd_scanner_n1/support_02/raw') -Recurse -File){Native ([IO.Path]::GetRelativePath($WorkspaceRoot,$p.FullName).Replace('\','/'))|Out-Null}
foreach($p in Get-ChildItem (Join-Path $WorkspaceRoot 'research/ncpd_scanner_n1/pilot_scene/raw') -Recurse -File){Native ([IO.Path]::GetRelativePath($WorkspaceRoot,$p.FullName).Replace('\','/'))|Out-Null}
# Add NCPD at its original position in the scoped U9 cleanup chain. All eight
# existing contact payloads, timeout, terminal and reset handshake are retained.
$oldCleanup='build/GigPhoneU9/source/towercontinued/gig_phone_u9/fixer_cleanup.questphase';Pin $oldCleanup
$old=(Read-Cr2wFile (Join-Path $WorkspaceRoot $oldCleanup)).RootChunk.Graph.Chunk
$cleanupSource='research/gig_restoration/gig_phone_u9/sources/raw/base/quest/holocalls/holocall_cleanup.questphase'
$nativeCleanup=(Native $cleanupSource).RootChunk.Graph.Chunk
$cg=CopyN1 $old @($old.Nodes|ForEach-Object {[int]$_.Chunk.Id.ToString()})
foreach($id in @(466,334)){$n=(Get-QuestNode $nativeCleanup $id).DeepCopy();ClearB5 $n;AddNodeB5 $cg $n}
$ce=@(EdgesB5 $old|ForEach-Object {$_});$redirects=0
foreach($e in $ce){if(($e[0] -eq 332 -or $e[0] -eq 464) -and $e[2] -eq 468){$e[2]=466;$redirects++}}
if($redirects -ne 2){throw 'U9 cleanup boundary changed'}
$ce+=,@(466,'True',334,'In40');$ce+=,@(466,'False',468,'In');$ce+=,@(334,'Out40',468,'In')
RebuildB5 $cg $ce
$cleanupDepot='towercontinued\gig_phone_u9\fixer_cleanup.questphase'
SaveN1 $cg $cleanupDepot 'fixer_cleanup' $false
$name='0_TowerContinued_NCPD_N1.archive';$archive=Join-Path $out $name
$xl=B71Render $boots;B71Parse $xl|Out-Null
[IO.File]::WriteAllText(($archive+'.xl'),$xl,[Text.UTF8Encoding]::new($false))
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new((Join-Path $out 'source')),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -ne 'NoError' -or $packed.Files.Count -ne 5){throw 'Archive scope mismatch'}
foreach($entry in $packed.Files.Values){
 if(!$resources.Contains($entry.Name)){throw 'Unexpected packed resource'}
 $mem=[IO.MemoryStream]::new();try{$entry.Extract($mem);if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($mem.ToArray())) -cne $resources[$entry.Name]){throw 'Packed readback mismatch'}}finally{$mem.Dispose()}
}
$files=@();foreach($file in @($archive,($archive+'.xl'))){$files+=,@{relative='archive/pc/mod/'+[IO.Path]::GetFileName($file);sha256=(Get-FileHash $file).Hash}}
$result=[ordered]@{status='BUILT_N1_LIVE_PENDING';files=$files;resources=$resources;activities=$rows;district_source=$district;support_guard=$supportPairs;support_balances=$balances;support_init=$initSource;token_source=$rootSource;cleanup_source=$cleanupSource;previous_cleanup=$oldCleanup;mod_override=$cleanupDepot;source_pins=$pins;installed_injections=$inventory;boots=$boots;packed_readback=$true;native_scenes_unchanged=$true;runtime_scripts_added=0;official_overrides=@();game_writes=0;save_writes=0;scope='Three fresh-only scanner pilot owners. Original rewards/achievement routing and cleanup. No cyberpsychos, completed/start-state resets, synthetic markers, or story owners.'}
[IO.File]::WriteAllText((Join-Path $out 'build.json'),($result|ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false))
@{status=$result.status;build=$out;sha256=(Get-FileHash (Join-Path $out 'build.json')).Hash}|ConvertTo-Json
