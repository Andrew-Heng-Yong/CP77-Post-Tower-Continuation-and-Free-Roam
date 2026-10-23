param([string]$Revision='fo1_01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$WorkspaceRoot=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $WorkspaceRoot 'tools/build_phase2a.ps1') -HelpersOnly
. (Join-Path $WorkspaceRoot 'tools/shark_b7_2_helpers.ps1')
$helper=Get-Content (Join-Path $WorkspaceRoot 'tools/build_fresh_gigs_b5.ps1') -Raw
$begin=$helper.IndexOf('function ClearB5(');$end=$helper.IndexOf('$allRoots=@{};')
if($begin -lt 0 -or $end -le $begin){throw 'Helper boundary changed'}
. ([scriptblock]::Create($helper.Substring($begin,$end-$begin)))
if($Revision -cnotmatch '^fo1_\d{2}$'){throw 'Invalid revision'}
$out=Join-Path $PSScriptRoot ('build/'+$Revision)
if(Test-Path $out){throw 'Build evidence is immutable; use a new revision'}
New-Item -ItemType Directory $out,(Join-Path $out 'source'),(Join-Path $out 'readback') | Out-Null
$pins=[ordered]@{}
function Pin([string]$rel){$pins[$rel]=(Get-FileHash -LiteralPath (Join-Path $WorkspaceRoot $rel)).Hash}
foreach($p in @('prealpha/fixer_offices_fo1/build.ps1','tools/build_phase2a.ps1','tools/build_fresh_gigs_b5.ps1','tools/shark_b7_2_helpers.ps1','tools/gig_family_b7_1_xl.ps1','tools/afterlife_faces_r5_deployment.ps1','research/q307_extracted/raw/base/quest/cyberpunk2077.questphase','research/q307_extracted/json/ep1/quest/ep1.quest.json')){Pin $p}
$specs=@(
 @{key='wakako';ids=@(0,17,19,20,52,53,54,55,59);entry=52;fact='wakako_default_on';prefabs=@('#wakako_okada_default')},
 @{key='dakota';ids=@(53,64);entry=53;fact='dakota_default_on';prefabs=@()},
 @{key='dyno';ids=@(40,50,48);entry=40;fact='dyno_default_on';prefabs=@()},
 @{key='el_capitan';ids=@(52,59);entry=52;fact='el_capitan_default_on';prefabs=@('#muamar_reyes_default')},
 @{key='padre';ids=@(55,56);entry=55;fact='padre_default_on';prefabs=@('#padre_default_prefab')},
 @{key='reggie';ids=@(88,128,98);entry=88;fact='reggie_default_on';prefabs=@('#pr_reggie_default')},
 @{key='mr_hands';ids=@();entry=0;fact='mr_hands_default_on';prefabs=@()}
)
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
B71Parser | Out-Null
$inventory=@(B72Inventory $game)
$stock=Get-Content (Join-Path $WorkspaceRoot 'research/q307_extracted/json/ep1/quest/ep1.quest.json') -Raw|ConvertFrom-Json
$used=@($stock.Data.RootChunk.graph.Data.nodes.Data.id)+@($inventory.id)
$resources=[ordered]@{};$boots=@();$rows=@()
foreach($s in $specs){
 $key=$s.key;$tag='PTFRFO1_'+$key
 $rel=if($key -eq 'mr_hands'){'research/fixer_offices_fo1/scenes/raw/ep1/openworld/fixers/mr_hands/phases/mr_hands_combat_zone_default.questphase'}else{"research/fixer_offices_fo1/parents/raw/base/open_world/fixers/$key/phases/$key.questphase"}
 Pin $rel;Pin ($rel.Replace('/raw/','/json/')+'.json')
 $native=Read-Cr2wFile (Join-Path $WorkspaceRoot $rel);$ng=$native.RootChunk.Graph.Chunk
 $child=[WolvenKit.RED4.Types.questPhaseNodeDefinition]::new();$child.Id=[uint16]100
 [void](New-QuestSocket $child 'In1' ([WolvenKit.RED4.Types.Enums+questSocketType]::Input))
 if($key -eq 'mr_hands'){
  # This native resource is already the isolated, repeatable default owner.
  $child.PhaseResource=[WolvenKit.RED4.Types.CResourceAsyncReference`1[WolvenKit.RED4.Types.questQuestPhaseResource]]::new('ep1\openworld\fixers\mr_hands\phases\mr_hands_combat_zone_default.questphase')
 }else{
  $slice=[WolvenKit.RED4.Types.questGraphDefinition]::new()
  foreach($id in $s.ids){
   $original=Get-QuestNode $ng $id;$n=$original.DeepCopy();ClearB5 $n
   if($n -is [WolvenKit.RED4.Types.questPhaseNodeDefinition] -and $null -ne $n.PhaseGraph -and $null -ne $n.PhaseGraph.Chunk){RewireB5 $n.PhaseGraph.Chunk $original.PhaseGraph.Chunk}
   AddNodeB5 $slice $n
  }
  $edges=@(EdgesB5 $ng|ForEach-Object {$_}|Where-Object {$_[0] -in $s.ids -and $_[2] -in $s.ids})
  if($key -eq 'wakako'){
   # Do not replay stock startup's default_on=1 write. Existing permission is
   # required by admission; retain actor spawn confirmation before its wait.
   $edges+=,@(19,'Out',20,'In')
  }else{AddNodeB5 $slice (New-InputNode 0 'In1');$edges+=,@(0,'Out',$s.entry,'In1')}
  RebuildB5 $slice $edges;Set-RedHandleProperty $child PhaseGraph $slice
  foreach($ref in $s.prefabs){
   $p=@($native.RootChunk.PhasePrefabs|Where-Object {$_.PrefabNodeRef.ToString() -ceq $ref})
   if($p.Count -ne 1){throw "Missing native prefab $ref"}
   $child.PhaseInstancePrefabs.Add($p[0].DeepCopy())
  }
 }
 $pairs=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;PTFRPA2_Finished=1;PTFRPA2_Fault=0;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;q307_active=0;q307_debug_reset=0;q115_point_of_no_return=0;q305_johnny_scene_active=0;PTFRU9_Support_Issued=1;PTFRU9_Support_Fault=0;($tag+'_Issued')=0}
 function GuardFO1 {
  $c=AllB5 $pairs
  Add-RedHandle $c.Conditions (New-FactCondition $s.fact 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Greater))
  if($key -eq 'mr_hands'){Add-RedHandle $c.Conditions (New-FactCondition 'mr_hands_default_ep1' 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Greater))}
  return $c
 }
 $g=[WolvenKit.RED4.Types.questGraphDefinition]::new()
 foreach($n in @((New-InputNode 0 'In1'),(New-SetFactNode 1 ($tag+'_Ready') 1),(PauseB5 2 (GuardFO1)),(New-ConditionNode 3 (GuardFO1)),(New-SetFactNode 4 ($tag+'_Issued') 1),$child)){AddNodeB5 $g $n}
 RebuildB5 $g @(@(0,'Out',1,'In'),@(1,'Out',2,'In'),@(2,'Out',3,'In'),@(3,'False',2,'In'),@(3,'True',4,'In'),@(4,'Out',100,'In1'))
 $root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();Set-RedHandleProperty $root Graph $g
 $depot='towercontinued\fixer_offices_fo1\'+$key+'.questphase';$id=B72Id ($depot+':1')
 if($id -in $used -or $id -ne (B72IdIndependent ($depot+':1'))){throw "Injection ID collision $key"};$used+=,$id
 $f=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$f.RootChunk=$root
 $raw=Join-Path (Join-Path $out 'source') $depot;Write-Cr2wFile $f $raw
 Export-Cr2wJson (Read-Cr2wFile $raw) (Join-Path $out ('readback/'+$key+'.json'))
 $resources[$depot]=(Get-FileHash $raw).Hash;$boots+=,$depot
 $rows+=,@{key=$key;depot=$depot;injection_id=$id;source=$rel;selected_nodes=$s.ids;entry=$s.entry;prefabs=$s.prefabs;guard_equal=$pairs;guard_positive=@($s.fact)+$(if($key -eq 'mr_hands'){@('mr_hands_default_ep1')}else{@()})}
}
# All dialogue scenes stay direct native references: pin for audit, never pack.
foreach($p in Get-ChildItem (Join-Path $WorkspaceRoot 'research/fixer_offices_fo1/scenes/raw') -Recurse -File -Filter '*.scene'){Pin ([IO.Path]::GetRelativePath($WorkspaceRoot,$p.FullName).Replace('\','/'))}
$name='TowerContinued_FixerOffices_FO1.archive';$archive=Join-Path $out $name
$xl=B71Render $boots;B71Parse $xl|Out-Null
[IO.File]::WriteAllText(($archive+'.xl'),$xl,[Text.UTF8Encoding]::new($false))
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new((Join-Path $out 'source')),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -ne 'NoError' -or $packed.Files.Count -ne 7){throw 'Archive scope mismatch'}
foreach($entry in $packed.Files.Values){
 if(!$resources.Contains($entry.Name)){throw 'Unexpected packed resource'}
 $mem=[IO.MemoryStream]::new()
 try{$entry.Extract($mem);if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($mem.ToArray())) -cne $resources[$entry.Name]){throw 'Packed readback mismatch'}}finally{$mem.Dispose()}
}
$files=@();foreach($file in @($archive,($archive+'.xl'))){$files+=,@{relative='archive/pc/mod/'+[IO.Path]::GetFileName($file);sha256=(Get-FileHash $file).Hash}}
$result=[ordered]@{status='BUILT_FO1_LIVE_PENDING';files=$files;resources=$resources;offices=$rows;source_pins=$pins;installed_injections=$inventory;packed_readback=$true;native_scenes_unchanged=$true;runtime_scripts_added=0;official_overrides=@();game_writes=0;save_writes=0}
[IO.File]::WriteAllText((Join-Path $out 'build.json'),($result|ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false))
@{status=$result.status;build=$out;sha256=(Get-FileHash (Join-Path $out 'build.json')).Hash}|ConvertTo-Json
