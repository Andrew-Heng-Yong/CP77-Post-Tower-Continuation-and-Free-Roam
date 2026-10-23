param([string]$Revision='s2_01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$WorkspaceRoot=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $WorkspaceRoot 'tools/build_phase2a.ps1') -HelpersOnly
. (Join-Path $WorkspaceRoot 'tools/shark_b7_2_helpers.ps1')
$helper=Get-Content (Join-Path $WorkspaceRoot 'tools/build_fresh_gigs_b5.ps1') -Raw
$begin=$helper.IndexOf('function ClearB5(');$end=$helper.IndexOf('$allRoots=@{};')
if($begin -lt 0 -or $end -le $begin){throw 'Helper boundary changed'}
. ([scriptblock]::Create($helper.Substring($begin,$end-$begin)))
if($Revision -cnotmatch '^s2_\d{2}$'){throw 'Invalid revision'}
$out=Join-Path $PSScriptRoot ('build/'+$Revision)
if(Test-Path $out){throw 'Immutable build exists; use new revision'}
New-Item -ItemType Directory $out,(Join-Path $out 'source'),(Join-Path $out 'readback')|Out-Null
$pins=[ordered]@{};$resources=[ordered]@{};$boots=@();$rows=@()
function Pin($p){$pins[$p]=(Get-FileHash -LiteralPath (Join-Path $WorkspaceRoot $p)).Hash}
foreach($p in @('prealpha/sidejobs_s2/build.ps1','prealpha/sidejobs_s2/SideJobsS2.reds','prealpha/sidejobs_s2/admission.json','tools/build_phase2a.ps1','tools/build_fresh_gigs_b5.ps1','tools/shark_b7_2_helpers.ps1','tools/gig_family_b7_1_xl.ps1','tools/afterlife_faces_r5_deployment.ps1','research/q307_extracted/raw/base/quest/cyberpunk2077.questphase','research/q307_extracted/json/ep1/quest/ep1.quest.json')){Pin $p}
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
B71Parser|Out-Null;$inventory=@(B72Inventory $game)
$stock=Get-Content (Join-Path $WorkspaceRoot 'research/q307_extracted/json/ep1/quest/ep1.quest.json') -Raw|ConvertFrom-Json
$used=@($stock.Data.RootChunk.graph.Data.nodes.Data.id)+@($inventory.id)
$data=Get-Content (Join-Path $PSScriptRoot 'admission.json') -Raw|ConvertFrom-Json
$common=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;PTFRPA2_Finished=1;PTFRPA2_Fault=0;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;q307_active=0;q307_debug_reset=0;q115_point_of_no_return=0;q305_johnny_scene_active=0;PTFRU9_Support_Issued=1;PTFRU9_Support_Fault=0}
function JournalInactive($path,$class){
 $p=[WolvenKit.RED4.Types.gameJournalPath]::new();$p.RealPath=$path;$p.ClassName=$class;$p.FileEntryIndex=2
 $t=[WolvenKit.RED4.Types.questJournalEntryState_ConditionType]::new();Set-RedHandleProperty $t Path $p;$t.State=[WolvenKit.RED4.Types.Enums+gameJournalEntryState]::Inactive;$t.Inverted=$false
 $c=[WolvenKit.RED4.Types.questJournalCondition]::new();Set-RedHandleProperty $c Type $t;return $c
}
function FreshGuard($pairs,$journals,$passive,$tag){
 $c=AllB5 $pairs
 foreach($j in $journals){Add-RedHandle $c.Conditions (JournalInactive $j.path $j.class)}
 foreach($f in $passive){
  Add-RedHandle $c.Conditions (New-FactCondition $f.name $f.min ([WolvenKit.RED4.Types.Enums+EComparisonType]::GreaterOrEqual))
  Add-RedHandle $c.Conditions (New-FactCondition $f.name $f.max ([WolvenKit.RED4.Types.Enums+EComparisonType]::LessOrEqual))
 }
 $route=[WolvenKit.RED4.Types.questLogicalCondition]::new();$route.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::OR
 foreach($v in @(1,2)){Add-RedHandle $route.Conditions (New-FactCondition ($tag+'_AuthorizedRoute') $v ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))}
 Add-RedHandle $c.Conditions $route
 return $c
}
function CopyNodes($source,$ids){
 $g=[WolvenKit.RED4.Types.questGraphDefinition]::new()
 foreach($id in $ids){
  $original=Get-QuestNode $source $id;$n=$original.DeepCopy();ClearB5 $n
  if($n -is [WolvenKit.RED4.Types.questPhaseNodeDefinition] -and $null -ne $n.PhaseGraph -and $null -ne $n.PhaseGraph.Chunk){RewireB5 $n.PhaseGraph.Chunk $original.PhaseGraph.Chunk}
  AddNodeB5 $g $n
 };return $g
}
$parentSource='research/sidejobs_s2/sacrum_audit/native_01/raw/base/quest/minor_quests/minorquests.questphase'
$native=(Read-Cr2wFile (Join-Path $WorkspaceRoot $parentSource)).RootChunk.Graph.Chunk
$specs=@(
 @{key='mq032_sacrum';tag='MQ032';ids=@(0,81,83,84,4);child=4;last=84;port='Out1'},
 @{key='mq008_party';tag='MQ008';ids=@(0,81,83,84,54,86,80,55,70,73,62,59,47,176,29);child=29;last=176;port='False'}
)
foreach($s in $specs){
 $entry=@($data.jobs|Where-Object {$_.key -ceq $s.key})
 if($entry.Count -ne 1 -or $entry[0].tag -cne $s.tag){throw 'Admission identity mismatch'}
 $entry=$entry[0];$tag='PTFRS2_'+$s.tag
 $pairs=[ordered]@{};foreach($k in $common.Keys){$pairs[$k]=$common[$k]}
 $pairs[$tag+'_Permit']=1;$pairs[$tag+'_Issued']=0;$pairs[$tag+'_Finished']=0;$pairs[$tag+'_Fault']=0
 foreach($f in $entry.zero_facts){$pairs[$f]=0}
 $g=CopyNodes $native $s.ids
 foreach($n in @((New-SetFactNode 1000 ($tag+'_Ready') 1),(PauseB5 1001 (FreshGuard $pairs $entry.journals $entry.allowed_passive_fields $tag)),(New-ConditionNode 1002 (FreshGuard $pairs $entry.journals $entry.allowed_passive_fields $tag)),(New-SetFactNode 1003 ($tag+'_Issued') 1),(New-SetFactNode 1004 ($tag+'_Finished') 1),(New-SetFactNode 1005 ($tag+'_Refused') 1))){AddNodeB5 $g $n}
 $edges=@(EdgesB5 $native|ForEach-Object {$_}|Where-Object {$_[0] -in $s.ids -and $_[2] -in $s.ids})
 $edges=@($edges|Where-Object {$_[0] -ne 0 -and -not($_[0] -eq $s.last -and $_[2] -eq $s.child)})
 $edges+=,@(0,'Out',1000,'In');$edges+=,@(1000,'Out',1001,'In');$edges+=,@(1001,'Out',81,'In1')
 $edges+=,@($s.last,$s.port,1002,'In');$edges+=,@(1002,'True',1003,'In');$edges+=,@(1002,'False',1005,'In')
 $edges+=,@(1003,'Out',$s.child,'In1');$edges+=,@($s.child,'Out1',1004,'In')
 # No output/termination node: the original owner's cleanup is never cancelled
 # merely because it emitted a native completion output.
 RebuildB5 $g $edges
 $root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();Set-RedHandleProperty $root Graph $g
 $f=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$f.RootChunk=$root
 $depot='towercontinued\sidejobs_s2\'+$s.key+'.questphase';$raw=Join-Path (Join-Path $out 'source') $depot
 Write-Cr2wFile $f $raw;Export-Cr2wJson (Read-Cr2wFile $raw) (Join-Path $out ('readback/'+$s.key+'.json'))
 $resources[$depot]=(Get-FileHash $raw).Hash;$id=B72Id ($depot+':1')
 if($id -in $used -or $id -ne (B72IdIndependent ($depot+':1'))){throw 'Injection collision'}
 $used+=,$id;$boots+=,$depot
 $rows+=,@{key=$s.key;tag=$s.tag;depot=$depot;selected_nodes=$s.ids;child=$s.child;last=$s.last;port=$s.port;guard_equal=$pairs;journals=$entry.journals;allowed_passive_fields=$entry.allowed_passive_fields;native_depot=(Get-QuestNode $native $s.child).PhaseResource.DepotPath.ToString();injection_id=$id}
}
foreach($p in Get-ChildItem (Join-Path $WorkspaceRoot 'research/sidejobs_s2') -Recurse -File|Where-Object {$_.FullName -match '[\\/]raw[\\/]'}){
 $rel=[IO.Path]::GetRelativePath($WorkspaceRoot,$p.FullName).Replace('\','/');Pin $rel;Pin ($rel.Replace('/raw/','/json/')+'.json')
}
$name='TowerContinued_SideJobs_S2.archive';$archive=Join-Path $out $name
$xl=B71Render $boots;B71Parse $xl|Out-Null;[IO.File]::WriteAllText(($archive+'.xl'),$xl,[Text.UTF8Encoding]::new($false))
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new((Join-Path $out 'source')),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -ne 'NoError' -or $packed.Files.Count -ne 2){throw 'Archive scope mismatch'}
foreach($entry in $packed.Files.Values){if(!$resources.Contains($entry.Name)){throw 'Unexpected packed resource'};$mem=[IO.MemoryStream]::new();try{$entry.Extract($mem);if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($mem.ToArray())) -cne $resources[$entry.Name]){throw 'Packed readback mismatch'}}finally{$mem.Dispose()}}
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'SideJobsS2.reds') -Destination (Join-Path $out 'SideJobsS2.reds')
$files=@();foreach($file in @($archive,($archive+'.xl'))){$files+=,@{relative='archive/pc/mod/'+[IO.Path]::GetFileName($file);sha256=(Get-FileHash $file).Hash}}
$files+=,@{relative='r6/scripts/TowerContinued_SideJobs_S2/SideJobsS2.reds';sha256=(Get-FileHash (Join-Path $out 'SideJobsS2.reds')).Hash}
$officialCount=@($pins.Keys|Where-Object {$_ -match '^research/sidejobs_s2/.+/raw/'}|ForEach-Object {($_ -split '/raw/',2)[1]}|Sort-Object -Unique).Count
$result=[ordered]@{status='BUILT_S2_LIVE_PENDING';files=$files;resources=$resources;activities=$rows;parent_source=$parentSource;source_pins=$pins;installed_injections=$inventory;boots=$boots;packed_readback=$true;native_scenes_unchanged=$true;runtime_scripts_added=1;official_resource_count=$officialCount;official_overrides=@();scope='Two fresh-only native side-job owners; original phases, scenes, reward and cleanup. Separate genuine pre-Tower history, explicitly uncertified development route, existing Johnny visual policy. No completed/failed/started reset, reward repair, service takeover, whole minor-quest root or Only Pain restart.'}
[IO.File]::WriteAllText((Join-Path $out 'build.json'),($result|ConvertTo-Json -Depth 35),[Text.UTF8Encoding]::new($false))
@{status=$result.status;build=$out;sha256=(Get-FileHash (Join-Path $out 'build.json')).Hash}|ConvertTo-Json
