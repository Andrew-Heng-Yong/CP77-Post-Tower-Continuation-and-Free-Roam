Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$audit=Join-Path $ws 'diagnostics/lizzies_restoration_audit_20261029_01'
$out=Join-Path $PSScriptRoot 'candidate_02'
if(Test-Path -LiteralPath $out){throw 'Fresh candidate required'}
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$baseline=Join-Path $ws 'prealpha/viktor_door_vd1/candidate_02'
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$relArchive='archive/pc/mod/zzzz_PTFR_Combined.archive';$relXl='archive/pc/mod/zzzz_PTFR_Combined.archive.xl'
foreach($rel in @($relArchive,$relXl)){
 $current=(Get-FileHash -LiteralPath (Join-Path $game $rel)).Hash
 if($current -cne (Get-FileHash -LiteralPath (Join-Path $baseline ('package/'+$rel))).Hash){throw ('Baseline drift '+$rel)}
}
$nativeDefault=Read-Cr2wFile (Join-Path $audit 'native/raw/base/quest/main_quests/prologue/q004/lizzies_club/phases/lizzies_default.questphase')
$nativeScenes=Read-Cr2wFile (Join-Path $audit 'native/raw/base/quest/main_quests/prologue/q004/lizzies_club/phases/lizzies_scenes.questphase')
$common=Read-Cr2wFile (Join-Path $ws 'research/q307_extracted/raw/base/quest/cyberpunk2077.questphase')
function ClearConnections($n){foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()}}
function Link($g,$a,$s,$b,$d){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $a) $s) (Get-QuestSocket (Get-QuestNode $g $b) $d))}
function RepairNested($original,$copy){
 foreach($h in $copy.Nodes){ClearConnections $h.Chunk}
 foreach($edge in @(Get-GraphEdges $original)){
  if($edge -notmatch '^(\d+)\.(.+) -> (\d+)\.(.+)$'){throw "Bad original edge $edge"}
  Link $copy ([int]$Matches[1]) $Matches[2] ([int]$Matches[3]) $Matches[4]
 }
 foreach($h in $original.Nodes){
  $n=$h.Chunk
  if($n -is [WolvenKit.RED4.Types.questPhaseNodeDefinition] -and $null -ne $n.PhaseGraph.Chunk){
   RepairNested $n.PhaseGraph.Chunk (Get-QuestNode $copy ([int]$n.Id)).PhaseGraph.Chunk
  }
 }
 if(@(Get-GraphEdges $copy).Count -ne @(Get-GraphEdges $original).Count){throw 'Nested edge count changed'}
}
function Subgraph($source,$ids){
 $g=[WolvenKit.RED4.Types.questGraphDefinition]::new()
 foreach($id in $ids){$original=Get-QuestNode $source $id;$n=$original.DeepCopy();ClearConnections $n;Add-RedHandle $g.Nodes $n
  if($original -is [WolvenKit.RED4.Types.questPhaseNodeDefinition] -and $null -ne $original.PhaseGraph.Chunk){RepairNested $original.PhaseGraph.Chunk $n.PhaseGraph.Chunk}
 }
 return $g
}
$nd=$nativeDefault.RootChunk.Graph.Chunk
$d=Subgraph $nd @(0,2,14,18,19,24,25,26,27,28,29,30,31,32,33,34,35,36,37)
foreach($edge in @(
 @(0,'Out',18,'In1'),@(0,'Out',19,'In1'),@(18,'Out1',28,'In1'),@(28,'Out1',18,'Loop'),
 @(2,'Out',29,'In'),@(29,'Out',14,'In'),@(14,'Out',24,'In'),@(24,'Out',25,'In'),@(25,'Out',26,'In'),@(26,'Out',27,'In'),@(27,'Out',30,'In'),
 @(30,'Out',31,'In'),@(31,'Out',32,'In'),@(32,'Out',33,'In'),@(33,'Out',34,'In'),@(34,'Out',35,'In'),@(35,'Out',36,'In1'),@(36,'Out1',37,'In1'),@(37,'Out1',29,'In')
)) {Link $d $edge[0] $edge[1] $edge[2] $edge[3]}
$ns=$nativeScenes.RootChunk.Graph.Chunk
$s=[WolvenKit.RED4.Types.questGraphDefinition]::new()
$input=New-InputNode 0 'In1';Add-RedHandle $s.Nodes $input
foreach($id in @(19,26,27)){$n=(Get-QuestNode (Get-QuestNode $ns 17).PhaseGraph.Chunk $id).DeepCopy();ClearConnections $n;Add-RedHandle $s.Nodes $n}
foreach($id in @(29,31,57,56,59,60)){$n=(Get-QuestNode $ns $id).DeepCopy();ClearConnections $n;Add-RedHandle $s.Nodes $n}
foreach($edge in @(
 @(0,'Out',29,'In'),@(0,'Out',57,'In'),@(29,'Out',31,'In'),@(31,'Out',27,'In'),
 @(27,'Out',19,'in_club_opened'),@(19,'out_club_opened',26,'In'),@(26,'Out',27,'In'),
 @(57,'Out',56,'In'),@(56,'Out',59,'In'),@(59,'Out',60,'In'),@(60,'Out',56,'In')
)) {Link $s $edge[0] $edge[1] $edge[2] $edge[3]}
$guard=[WolvenKit.RED4.Types.questLogicalCondition]::new();$guard.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
$facts=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;q307_active=0;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q305_johnny_scene_active=0;q115_point_of_no_return=0;q004_done=1;q105_01_done=1;PTFRBASE_Suspended=0;PTFRLR1_Claimed=0}
foreach($k in $facts.Keys){Add-RedHandle $guard.Conditions (New-FactCondition $k $facts[$k] ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))}
$pause=(Get-QuestNode $common.RootChunk.Graph.Chunk 106).DeepCopy();$pause.Id=[uint16]1;ClearConnections $pause;Set-RedHandleProperty $pause Condition $guard
$outer=[WolvenKit.RED4.Types.questGraphDefinition]::new()
Add-RedHandle $outer.Nodes (New-InputNode 0 'In1');Add-RedHandle $outer.Nodes $pause
Add-RedHandle $outer.Nodes (New-SetFactNode 2 'PTFRLR1_Claimed' 1)
$dp=[WolvenKit.RED4.Types.questPhaseNodeDefinition]::new();$dp.Id=[uint16]3;Set-RedHandleProperty $dp PhaseGraph $d
foreach($name in @('base','after_q105')){[void](New-QuestSocket $dp $name ([WolvenKit.RED4.Types.Enums+questSocketType]::Input))}
Add-RedHandle $outer.Nodes $dp
$sp=[WolvenKit.RED4.Types.questPhaseNodeDefinition]::new();$sp.Id=[uint16]4;Set-RedHandleProperty $sp PhaseGraph $s
[void](New-QuestSocket $sp 'In1' ([WolvenKit.RED4.Types.Enums+questSocketType]::Input));Add-RedHandle $outer.Nodes $sp
foreach($edge in @(@(0,'Out',1,'In'),@(1,'Out',2,'In'),@(2,'Out',3,'base'),@(2,'Out',3,'after_q105'),@(2,'Out',4,'In1'))){Link $outer $edge[0] $edge[1] $edge[2] $edge[3]}
$root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();$root.CookingPlatform=[WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC;Set-RedHandleProperty $root Graph $outer
$file=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$file.RootChunk=$root
$source=Join-Path $out 'archive_source';$package=Join-Path $out 'package';New-Item -ItemType Directory -Force -Path $out|Out-Null
Copy-Item -LiteralPath (Join-Path $baseline 'archive_source') -Destination $source -Recurse
Copy-Item -LiteralPath (Join-Path $baseline 'package') -Destination $package -Recurse
$depot='towercontinued\lizzies_lr1\club_owner.questphase'
Write-Cr2wFile $file (Join-Path $source $depot)
$readback=Read-Cr2wFile (Join-Path $source $depot);Export-Cr2wJson $readback (Join-Path $out 'owner_readback_01.json')
$xl=Join-Path $package $relXl;$x=[IO.File]::ReadAllText($xl)
if($x.Contains($depot) -or [regex]::Matches($x,'(?m)^streaming:').Count -ne 1){throw 'XL anchor drift'}
$nl=if($x.Contains("`r`n")){"`r`n"}else{"`n"}
$entry=@("    - path: $depot",'      parent: ep1\quest\ep1.quest','      input:','        node: [1]','        socket: Out') -join $nl
[IO.File]::WriteAllText($xl,$x.Replace('streaming:',($entry+$nl+'streaming:')),[Text.UTF8Encoding]::new($false))
$archive=Join-Path $package $relArchive;$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$a=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$a).ToString() -ne 'NoError'){throw 'Readback failed'}
if($a.Files.Count -ne 1565){throw "Member count $($a.Files.Count)"}
@{status='BUILT_NOT_INSTALLED';archive_members=$a.Files.Count;new_depot=$depot;guard=$facts;archive_sha256=(Get-FileHash -LiteralPath $archive).Hash;xl_sha256=(Get-FileHash -LiteralPath $xl).Hash}|ConvertTo-Json -Depth 6|Set-Content -LiteralPath (Join-Path $out 'build_01.json') -Encoding utf8NoBOM
Get-Content -LiteralPath (Join-Path $out 'build_01.json')
