# Add the omitted vanilla world support without restarting persisted LR1 actors.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$out=Join-Path $PSScriptRoot 'candidate_01'
if(Test-Path -LiteralPath $out){throw 'Fresh candidate required'}
$baseline=Join-Path $ws 'prealpha/lizzies_lr1/candidate_02'
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$relArchive='archive/pc/mod/zzzz_PTFR_Combined.archive';$relXl='archive/pc/mod/zzzz_PTFR_Combined.archive.xl'
foreach($rel in @($relArchive,$relXl)){if((Get-FileHash -LiteralPath (Join-Path $game $rel)).Hash -cne (Get-FileHash -LiteralPath (Join-Path $baseline ('package/'+$rel))).Hash){throw "LR1 baseline drift: $rel"}}
$review=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'native_review_02/providers_01.json') -Raw|ConvertFrom-Json -Depth 90
$nativeRow=@($review.hits|Where-Object {$_.depot -like '*wat_kab_lizzies_bar_phase.questphase'})
if($nativeRow.Count -ne 1 -or (Get-FileHash -LiteralPath $nativeRow[0].source).Hash -cne $nativeRow[0].sha256){throw 'Native reference drift'}
$native=Read-Cr2wFile $nativeRow[0].source
if($native.RootChunk.PhasePrefabs.Count -ne 1 -or $native.RootChunk.PhasePrefabs[0].PrefabNodeRef.ToString() -cne '#loc_q004_lizzys_nightclub_openworld'){throw 'Native prefab mismatch'}
$full='$/03_night_city/c_watson/kabuki/loc_q004_lizzys_nightclub_prefabMARLNHA/#loc_q004_lizzys_nightclub_openworld'
if($review.descriptors.Count -ne 2 -or @($review.descriptors|Where-Object {$_.prefab -cne $full -or $_.category -cne 'Quest' -or $_.variants -ne 0}).Count){throw 'Native descriptor mismatch'}
$template=Read-Cr2wFile (Join-Path $ws 'research/q307_extracted/raw/base/quest/cyberpunk2077.questphase')
function Put($g,$n){Add-RedHandle $g.Nodes $n}
function Link($g,$a,$b,$inputName='In'){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $a) 'Out') (Get-QuestSocket (Get-QuestNode $g $b) $inputName))}
function Pause($id,$condition){$n=(Get-QuestNode $template.RootChunk.Graph.Chunk 106).DeepCopy();$n.Id=[uint16]$id;foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()};Set-RedHandleProperty $n Condition $condition;return $n}
$facts=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;q307_active=0;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q305_johnny_scene_active=0;q115_point_of_no_return=0;q004_done=1;q105_01_done=1;PTFRBASE_Suspended=0;PTFRLR1_Claimed=1;PTFRLR2_Claimed=0;PTFRLR2_Entered=0;PTFRLR2_Hold=0}
$guard=[WolvenKit.RED4.Types.questLogicalCondition]::new();$guard.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
foreach($k in $facts.Keys){Add-RedHandle $guard.Conditions (New-FactCondition $k $facts[$k] ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))}
$inner=[WolvenKit.RED4.Types.questGraphDefinition]::new()
Put $inner (New-InputNode 0 'In1');Put $inner (New-SetFactNode 1 'PTFRLR2_Entered' 1)
Put $inner (Pause 2 (New-FactCondition 'PTFRLR2_Hold' 1 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal)))
Link $inner 0 1;Link $inner 1 2
$owner=[WolvenKit.RED4.Types.questPhaseNodeDefinition]::new();$owner.Id=[uint16]3
$prefab=$native.RootChunk.PhasePrefabs[0].DeepCopy();$prefab.PrefabNodeRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($full);$owner.PhaseInstancePrefabs.Add($prefab)
Set-RedHandleProperty $owner PhaseGraph $inner
[void](New-QuestSocket $owner 'CutDestination' ([WolvenKit.RED4.Types.Enums+questSocketType]::CutDestination))
[void](New-QuestSocket $owner 'In1' ([WolvenKit.RED4.Types.Enums+questSocketType]::Input))
$outer=[WolvenKit.RED4.Types.questGraphDefinition]::new()
Put $outer (New-InputNode 0 'In1');Put $outer (Pause 1 $guard);Put $outer (New-SetFactNode 2 'PTFRLR2_Claimed' 1);Put $outer $owner
Link $outer 0 1;Link $outer 1 2;Link $outer 2 3 'In1'
$root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();$root.CookingPlatform=[WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC
Set-RedHandleProperty $root Graph $outer
$file=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$file.RootChunk=$root
$source=Join-Path $out 'archive_source';$package=Join-Path $out 'package'
New-Item -ItemType Directory -Path $out|Out-Null
Copy-Item -LiteralPath (Join-Path $baseline 'archive_source') -Destination $source -Recurse
Copy-Item -LiteralPath (Join-Path $baseline 'package') -Destination $package -Recurse
$depot='towercontinued\lizzies_lr2\club_support.questphase'
Write-Cr2wFile $file (Join-Path $source $depot)
$read=Read-Cr2wFile (Join-Path $source $depot);Export-Cr2wJson $read (Join-Path $out 'owner_readback_01.json')
$xl=Join-Path $package $relXl;$x=[IO.File]::ReadAllText($xl)
if($x.Contains($depot) -or [regex]::Matches($x,'(?m)^streaming:').Count -ne 1){throw 'XL anchor drift'}
$nl=if($x.Contains("`r`n")){"`r`n"}else{"`n"}
$entry=@("    - path: $depot",'      parent: ep1\quest\ep1.quest','      input:','        node: [1]','        socket: Out') -join $nl
[IO.File]::WriteAllText($xl,$x.Replace('streaming:',($entry+$nl+'streaming:')),[Text.UTF8Encoding]::new($false))
$archive=Join-Path $package $relArchive;$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
@{status='BUILT_NOT_INSTALLED';new_depot=$depot;guard=$facts;native_prefab=$full;archive_sha256=(Get-FileHash -LiteralPath $archive).Hash;xl_sha256=(Get-FileHash -LiteralPath $xl).Hash;outer_edges=@(Get-GraphEdges $read.RootChunk.Graph.Chunk);inner_edges=@(Get-GraphEdges (Get-QuestNode $read.RootChunk.Graph.Chunk 3).PhaseGraph.Chunk)}|ConvertTo-Json -Depth 10|Set-Content -LiteralPath (Join-Path $out 'build_01.json') -Encoding utf8NoBOM
Get-Content -LiteralPath (Join-Path $out 'build_01.json')
