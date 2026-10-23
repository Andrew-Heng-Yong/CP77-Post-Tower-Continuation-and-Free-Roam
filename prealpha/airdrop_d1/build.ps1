param([string]$Revision='d1_01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$WorkspaceRoot=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $WorkspaceRoot 'tools/build_phase2a.ps1') -HelpersOnly
. (Join-Path $WorkspaceRoot 'tools/shark_b7_2_helpers.ps1')
$helper=Get-Content (Join-Path $WorkspaceRoot 'tools/build_fresh_gigs_b5.ps1') -Raw
$begin=$helper.IndexOf('function ClearB5(');$end=$helper.IndexOf('$allRoots=@{};')
if($begin -lt 0 -or $end -le $begin){throw 'Helper boundary changed'}
. ([scriptblock]::Create($helper.Substring($begin,$end-$begin)))
if($Revision -cnotmatch '^d1_\d{2}$'){throw 'Invalid revision'}
$out=Join-Path $PSScriptRoot ('build/'+$Revision)
if(Test-Path $out){throw 'Immutable build exists; use a new revision'}
New-Item -ItemType Directory $out,(Join-Path $out 'source'),(Join-Path $out 'readback')|Out-Null
$pins=[ordered]@{};$resources=[ordered]@{}
function Pin([string]$rel){$pins[$rel]=(Get-FileHash -LiteralPath (Join-Path $WorkspaceRoot $rel)).Hash}
foreach($p in @('prealpha/airdrop_d1/build.ps1','prealpha/airdrop_d1/research.py','tools/build_phase2a.ps1','tools/build_fresh_gigs_b5.ps1','tools/shark_b7_2_helpers.ps1','tools/gig_family_b7_1_xl.ps1','tools/afterlife_faces_r5_deployment.ps1','research/q307_extracted/raw/base/quest/cyberpunk2077.questphase','research/q307_extracted/json/ep1/quest/ep1.quest.json')){Pin $p}
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
B71Parser|Out-Null;$inventory=@(B72Inventory $game)
$stock=Get-Content (Join-Path $WorkspaceRoot 'research/q307_extracted/json/ep1/quest/ep1.quest.json') -Raw|ConvertFrom-Json
$used=@($stock.Data.RootChunk.graph.Data.nodes.Data.id)+@($inventory.id)
$source='research/airdrop_d1/native_01/raw/ep1/openworld/sandbox_activities/ep1_airdrop_activities.questphase'
$original=Read-Cr2wFile (Join-Path $WorkspaceRoot $source)
$root=$original.RootChunk.DeepCopy();$g=$root.Graph.Chunk
RewireB5 $g $original.RootChunk.Graph.Chunk
# Keep every original payload and nested edge. The sole native edge change uses
# the existing post-drop pause/cooldown route, never the one-time Intro entry.
$edges=@(EdgesB5 $g|ForEach-Object {$_});$changed=0
foreach($e in $edges){if($e[0] -eq 23 -and $e[1] -ceq 'False' -and $e[2] -eq 3 -and $e[3] -ceq 'Intro'){$e[2]=17;$e[3]='In';$changed++}}
if($changed -ne 1){throw 'Native intro boundary changed'}
RebuildB5 $g $edges
$loopDepot='towercontinued\airdrop_d1\loop.questphase'
$bootDepot='towercontinued\airdrop_d1\boot.questphase'
function SaveD1($r,[string]$depot,[string]$label){
 $f=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$f.RootChunk=$r
 $raw=Join-Path (Join-Path $out 'source') $depot;Write-Cr2wFile $f $raw
 Export-Cr2wJson (Read-Cr2wFile $raw) (Join-Path $out ('readback/'+$label+'.json'))
 $resources[$depot]=(Get-FileHash $raw).Hash
}
SaveD1 $root $loopDepot 'loop'
$pairs=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;PTFRPA2_Finished=1;PTFRPA2_Fault=0;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;q307_active=0;q307_debug_reset=0;q115_point_of_no_return=0;q305_johnny_scene_active=0;PTFRD1_Issued=0;ep1_sa_test_airdrop_loop=0;mq304_airdrops_active=0}
$positive=@('ep1_installed','ep1_active','ep1_side_content')
function GuardD1 {
 $c=AllB5 $pairs
 foreach($k in $positive){Add-RedHandle $c.Conditions (New-FactCondition $k 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Greater))}
 # Never pay a historical reward backlog merely by installing the owner.
 Add-RedHandle $c.Conditions (EqB5 'sa_ep1_counter' 'sa_ep1_reward_counter')
 return $c
}
$bg=[WolvenKit.RED4.Types.questGraphDefinition]::new()
$parent=(Read-Cr2wFile (Join-Path $WorkspaceRoot 'research/airdrop_d1/native_01/raw/ep1/openworld/sandbox_activities/ep1_sandbox_activities.questphase')).RootChunk.Graph.Chunk
$phase=(Get-QuestNode $parent 2).DeepCopy();ClearB5 $phase
$phase.Id=[uint16]5
$phase.PhaseResource=[WolvenKit.RED4.Types.CResourceAsyncReference[WolvenKit.RED4.Types.questQuestPhaseResource]]::new($loopDepot)
foreach($n in @((New-InputNode 0 'In1'),(New-SetFactNode 1 'PTFRD1_Ready' 1),(PauseB5 2 (GuardD1)),(New-ConditionNode 3 (GuardD1)),(New-SetFactNode 4 'PTFRD1_Issued' 1),$phase)){AddNodeB5 $bg $n}
RebuildB5 $bg @(@(0,'Out',1,'In'),@(1,'Out',2,'In'),@(2,'Out',3,'In'),@(3,'False',2,'In'),@(3,'True',4,'In'),@(4,'Out',5,'In1'))
$br=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();Set-RedHandleProperty $br Graph $bg
SaveD1 $br $bootDepot 'boot'
$id=B72Id ($bootDepot+':1')
if($id -in $used -or $id -ne (B72IdIndependent ($bootDepot+':1'))){throw 'Injection collision'}
foreach($p in Get-ChildItem (Join-Path $WorkspaceRoot 'research/airdrop_d1') -Recurse -File|Where-Object {$_.FullName -match '[\\/]raw[\\/]'}){
 $rel=[IO.Path]::GetRelativePath($WorkspaceRoot,$p.FullName).Replace('\','/');Pin $rel;Pin ($rel.Replace('/raw/','/json/')+'.json')
}
$name='TowerContinued_Airdrops_D1.archive';$archive=Join-Path $out $name
$xl=B71Render @($bootDepot);B71Parse $xl|Out-Null
[IO.File]::WriteAllText(($archive+'.xl'),$xl,[Text.UTF8Encoding]::new($false))
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new((Join-Path $out 'source')),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -ne 'NoError' -or $packed.Files.Count -ne 2){throw 'Archive scope mismatch'}
foreach($entry in $packed.Files.Values){
 if(!$resources.Contains($entry.Name)){throw 'Unexpected packed resource'}
 $mem=[IO.MemoryStream]::new();try{$entry.Extract($mem);if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($mem.ToArray())) -cne $resources[$entry.Name]){throw 'Packed readback mismatch'}}finally{$mem.Dispose()}
}
$files=@();foreach($file in @($archive,($archive+'.xl'))){$files+=,@{relative='archive/pc/mod/'+[IO.Path]::GetFileName($file);sha256=(Get-FileHash $file).Hash}}
$result=[ordered]@{status='BUILT_D1_LIVE_PENDING';files=$files;resources=$resources;native_source=$source;guard_equal=$pairs;guard_positive=$positive;guard_balance=@('sa_ep1_counter','sa_ep1_reward_counter');source_pins=$pins;installed_injections=$inventory;boots=@($bootDepot);packed_readback=$true;native_scenes_unchanged=$true;runtime_scripts_added=0;official_overrides=@();game_writes=0;save_writes=0;scope='Native repeatable airdrop controller. One startup edge resumes normal loop instead of introductory drop. All stock drops/rewards/cooldowns/special-event gates unchanged; no historic counter reset or catch-up payout. Old active facts are not treated as live owners after Tower killed EP1. No migration of an interrupted old drop.'}
[IO.File]::WriteAllText((Join-Path $out 'build.json'),($result|ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false))
@{status=$result.status;build=$out;sha256=(Get-FileHash (Join-Path $out 'build.json')).Hash}|ConvertTo-Json
