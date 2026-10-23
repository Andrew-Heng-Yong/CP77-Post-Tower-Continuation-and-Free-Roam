param([string]$Revision='r1_01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$WorkspaceRoot=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $WorkspaceRoot 'tools/build_phase2a.ps1') -HelpersOnly
. (Join-Path $WorkspaceRoot 'tools/shark_b7_2_helpers.ps1')
$helper=Get-Content (Join-Path $WorkspaceRoot 'tools/build_fresh_gigs_b5.ps1') -Raw
$begin=$helper.IndexOf('function ClearB5(');$end=$helper.IndexOf('$allRoots=@{};')
if($begin -lt 0 -or $end -le $begin){throw 'Helper boundary changed'}
. ([scriptblock]::Create($helper.Substring($begin,$end-$begin)))
if($Revision -cnotmatch '^r1_\d{2}$'){throw 'Invalid revision'}
$out=Join-Path $PSScriptRoot ('build/'+$Revision)
if(Test-Path $out){throw 'Immutable build exists'}
New-Item -ItemType Directory $out,(Join-Path $out 'source'),(Join-Path $out 'readback')|Out-Null
$pins=[ordered]@{};$resources=[ordered]@{}
function Pin($p){$pins[$p]=(Get-FileHash -LiteralPath (Join-Path $WorkspaceRoot $p)).Hash}
foreach($p in @('prealpha/races_r1/build.ps1','prealpha/races_r1/research.py','tools/build_phase2a.ps1','tools/build_fresh_gigs_b5.ps1','tools/shark_b7_2_helpers.ps1','tools/gig_family_b7_1_xl.ps1','tools/afterlife_faces_r5_deployment.ps1','research/q307_extracted/raw/base/quest/cyberpunk2077.questphase','research/q307_extracted/json/ep1/quest/ep1.quest.json')){Pin $p}
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
B71Parser|Out-Null;$inventory=@(B72Inventory $game)
$stock=Get-Content (Join-Path $WorkspaceRoot 'research/q307_extracted/json/ep1/quest/ep1.quest.json') -Raw|ConvertFrom-Json
$used=@($stock.Data.RootChunk.graph.Data.nodes.Data.id)+@($inventory.id)
function JournalState($path,$class,$state,[bool]$invert=$false){
 $p=[WolvenKit.RED4.Types.gameJournalPath]::new();$p.RealPath=$path;$p.ClassName=$class;$p.FileEntryIndex=if($path.StartsWith('quests/')){2}else{1}
 $t=[WolvenKit.RED4.Types.questJournalEntryState_ConditionType]::new();Set-RedHandleProperty $t Path $p;$t.State=[Enum]::Parse([WolvenKit.RED4.Types.Enums+gameJournalEntryState],$state);$t.Inverted=$invert
 $c=[WolvenKit.RED4.Types.questJournalCondition]::new();Set-RedHandleProperty $c Type $t;return $c
}
function SaveRace($r,$label){
 $depot='towercontinued\races_r1\'+$label+'.questphase';$f=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$f.RootChunk=$r
 $raw=Join-Path (Join-Path $out 'source') $depot;Write-Cr2wFile $f $raw
 Export-Cr2wJson (Read-Cr2wFile $raw) (Join-Path $out ('readback/'+$label+'.json'));$resources[$depot]=(Get-FileHash $raw).Hash
}
$mainSource='research/races_r1/native_02/raw/base/quest/minor_quests/mq056/phases/mq056_00_main.questphase'
$nativeMain=Read-Cr2wFile (Join-Path $WorkspaceRoot $mainSource);$main=$nativeMain.RootChunk.DeepCopy();$mg=$main.Graph.Chunk
RewireB5 $mg $nativeMain.RootChunk.Graph.Chunk
# Previously delivered native invitation is durable evidence that this owner
# already opened the repeatable races. Do not resend it or restart its delay.
# Without that evidence, retain the stock initial three-day invitation route.
$resume=[WolvenKit.RED4.Types.questLogicalCondition]::new();$resume.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::OR
foreach($s in @('Active','Succeeded')){Add-RedHandle $resume.Conditions (JournalState 'contacts/announcer_mq056/mq056_hook/01_hook2' 'gameJournalPhoneMessage' $s)}
AddNodeB5 $mg (New-ConditionNode 1000 $resume)
AddNodeB5 $mg (New-SetFactNode 1001 'PTFRR1_Resumed' 1)
$ee=@(EdgesB5 $mg|ForEach-Object {$_}|Where-Object {-not($_[0] -eq 0 -and $_[2] -eq 34)})
$ee+=,@(0,'Out',1000,'In');$ee+=,@(1000,'False',34,'In');$ee+=,@(1000,'True',1001,'In');$ee+=,@(1001,'Out',23,'In1')
RebuildB5 $mg $ee;SaveRace $main 'main'
$ownerSource='research/races_r1/native_01/raw/base/quest/minor_quests/mq056/mq056.questphase'
$nativeOwner=Read-Cr2wFile (Join-Path $WorkspaceRoot $ownerSource);$owner=$nativeOwner.RootChunk.DeepCopy();$og=$owner.Graph.Chunk
RewireB5 $og $nativeOwner.RootChunk.Graph.Chunk
(Get-QuestNode $og 9).PhaseResource=[WolvenKit.RED4.Types.CResourceAsyncReference[WolvenKit.RED4.Types.questQuestPhaseResource]]::new('towercontinued\races_r1\main.questphase')
SaveRace $owner 'owner'
$pairs=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;PTFRPA2_Finished=1;PTFRPA2_Fault=0;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;q307_active=0;q307_debug_reset=0;q115_point_of_no_return=0;q305_johnny_scene_active=0;PTFRR1_Issued=0;mq056_test_drive=0;mq056_cour_active=0;mq056_active=0;mq056_prevention_fail=0}
$phasePaths=@('01_city_center','02_badlands','03_santo_domingo','04_big_race')
function RaceGuard {
 $c=AllB5 $pairs
 Add-RedHandle $c.Conditions (New-FactCondition 'sq024_done' 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Greater))
 foreach($p in $phasePaths){Add-RedHandle $c.Conditions (JournalState ('quests/minor_quest/mq056_race_replay/'+$p) 'gameJournalQuestPhase' 'Active' $true)}
 return $c
}
$bg=[WolvenKit.RED4.Types.questGraphDefinition]::new()
$parent=(Read-Cr2wFile (Join-Path $WorkspaceRoot 'research/races_r1/parents_01/raw/base/quest/bugfixing/quest_bugfixing.questphase')).RootChunk.Graph.Chunk
$phase=(Get-QuestNode (Get-QuestNode $parent 3).PhaseGraph.Chunk 74).DeepCopy();ClearB5 $phase;$phase.Id=[uint16]5
$phase.PhaseResource=[WolvenKit.RED4.Types.CResourceAsyncReference[WolvenKit.RED4.Types.questQuestPhaseResource]]::new('towercontinued\races_r1\owner.questphase')
foreach($n in @((New-InputNode 0 'In1'),(New-SetFactNode 1 'PTFRR1_Ready' 1),(PauseB5 2 (RaceGuard)),(New-ConditionNode 3 (RaceGuard)),(New-SetFactNode 4 'PTFRR1_Issued' 1),$phase)){AddNodeB5 $bg $n}
RebuildB5 $bg @(@(0,'Out',1,'In'),@(1,'Out',2,'In'),@(2,'Out',3,'In'),@(3,'False',2,'In'),@(3,'True',4,'In'),@(4,'Out',5,'Intro_in'))
$br=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();Set-RedHandleProperty $br Graph $bg;SaveRace $br 'boot'
$boot='towercontinued\races_r1\boot.questphase';$id=B72Id ($boot+':1')
if($id -in $used -or $id -ne (B72IdIndependent ($boot+':1'))){throw 'Injection collision'}
foreach($p in Get-ChildItem (Join-Path $WorkspaceRoot 'research/races_r1') -Recurse -File|Where-Object {$_.FullName -match '[\\/]raw[\\/]'}){
 $rel=[IO.Path]::GetRelativePath($WorkspaceRoot,$p.FullName).Replace('\','/');Pin $rel;Pin ($rel.Replace('/raw/','/json/')+'.json')
}
$name='TowerContinued_Races_R1.archive';$archive=Join-Path $out $name
$xl=B71Render @($boot);B71Parse $xl|Out-Null;[IO.File]::WriteAllText(($archive+'.xl'),$xl,[Text.UTF8Encoding]::new($false))
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new((Join-Path $out 'source')),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -ne 'NoError' -or $packed.Files.Count -ne 3){throw 'Archive scope mismatch'}
foreach($entry in $packed.Files.Values){if(!$resources.Contains($entry.Name)){throw 'Unexpected packed resource'};$mem=[IO.MemoryStream]::new();try{$entry.Extract($mem);if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($mem.ToArray())) -cne $resources[$entry.Name]){throw 'Packed readback mismatch'}}finally{$mem.Dispose()}}
$files=@();foreach($file in @($archive,($archive+'.xl'))){$files+=,@{relative='archive/pc/mod/'+[IO.Path]::GetFileName($file);sha256=(Get-FileHash $file).Hash}}
$result=[ordered]@{status='BUILT_R1_LIVE_PENDING';files=$files;resources=$resources;main_source=$mainSource;owner_source=$ownerSource;guard_equal=$pairs;guard_positive=@('sq024_done');guard_journal_inactive=$phasePaths;source_pins=$pins;installed_injections=$inventory;boots=@($boot);packed_readback=$true;native_scenes_unchanged=$true;runtime_scripts_added=0;official_overrides=@();scope='Stock repeatable races only. Retain original sq024 completion unlock, native start/finish/reward/abort/repeat and Johnny voice policy. Resume previously delivered invitation without replay; otherwise stock three-day intro. No old interrupted-race migration, historic wins reset, forced unlock or story replay.'}
[IO.File]::WriteAllText((Join-Path $out 'build.json'),($result|ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false))
@{status=$result.status;build=$out;sha256=(Get-FileHash (Join-Path $out 'build.json')).Hash}|ConvertTo-Json
