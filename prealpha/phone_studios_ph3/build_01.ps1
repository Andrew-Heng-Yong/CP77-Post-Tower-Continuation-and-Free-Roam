Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$W=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $W 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $W 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$C=Join-Path $PSScriptRoot 'candidate_01';if(Test-Path $C){throw 'Fresh candidate required'}
$B=Join-Path $W 'prealpha/phone_merge_ph2/candidate_01';$G='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
foreach($f in Get-ChildItem (Join-Path $B 'package') -Recurse -File){$r=[IO.Path]::GetRelativePath((Join-Path $B 'package'),$f.FullName);if((Get-FileHash $f.FullName).Hash -cne (Get-FileHash (Join-Path $G $r)).Hash){throw "Baseline drift $r"}}
$audit=Get-Content (Join-Path $W 'diagnostics/phone_expansion_ph3_20261029_01/native_04/providers_01.json') -Raw|ConvertFrom-Json -Depth 100
$nativeRow=@($audit.hits|Where-Object depot -EQ 'ep1\quest\holocalls\holocall_initializers_ep1.questphase');if($nativeRow.Count -ne 1 -or (Get-FileHash $nativeRow[0].raw).Hash -cne $nativeRow[0].sha256){throw 'Native source drift'}
$native=(Read-Cr2wFile $nativeRow[0].raw).RootChunk
if($native.PhasePrefabs.Count -ne 2 -or $native.PhasePrefabs[0].PrefabNodeRef.ToString() -cne '#holocalls_studio_ep1' -or $native.PhasePrefabs[1].PrefabNodeRef.ToString() -cne '#holocalls_studio'){throw 'Native studio scope drift'}
$full=@('$/03_night_city/c_pacifica/#holocalls_studio_ep1','$/03_night_city/ne2/#holocalls_studio')
foreach($s in $full){if(@($audit.descriptors|Where-Object {$_.prefab -ceq $s -and $_.category -ceq 'Quest'}).Count -ne 2){throw 'Studio descriptor mismatch'}}
$template=(Read-Cr2wFile (Join-Path $W 'research/q307_extracted/raw/base/quest/cyberpunk2077.questphase')).RootChunk
function Put($g,$n){Add-RedHandle $g.Nodes $n}
function Link($g,$a,$b,$inputName='In'){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $a) 'Out') (Get-QuestSocket (Get-QuestNode $g $b) $inputName))}
function Pause($id,$condition){$n=(Get-QuestNode $template.Graph.Chunk 106).DeepCopy();$n.Id=[uint16]$id;foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()};Set-RedHandleProperty $n Condition $condition;return $n}
$facts=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;PTFRPA2_Finished=1;PTFRPA2_Fault=0;q307_active=0;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;q307_debug_reset=0;q115_point_of_no_return=0;q305_johnny_scene_active=0;PTFRU9_Support_Issued=1;PTFRU9_Support_Fault=0;PTFRPH3_Claimed=0;PTFRPH3_Entered=0;PTFRPH3_Ready=0;PTFRPH3_Hold=0}
$guard=[WolvenKit.RED4.Types.questLogicalCondition]::new();$guard.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
foreach($k in $facts.Keys){Add-RedHandle $guard.Conditions (New-FactCondition $k $facts[$k] ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))}
Add-RedHandle $guard.Conditions (Get-QuestNode $template.Graph.Chunk 106).Condition.Chunk.DeepCopy()
# No phone-idle/interruption guard: an already waiting native scene must gain its missing studio.
$inner=[WolvenKit.RED4.Types.questGraphDefinition]::new()
Put $inner (New-InputNode 0 'In1');Put $inner (New-SetFactNode 1 'PTFRPH3_Entered' 1);Put $inner (New-SetFactNode 2 'PTFRPH3_Ready' 1);Put $inner (Pause 3 (New-FactCondition 'PTFRPH3_Hold' 1 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal)))
Link $inner 0 1;Link $inner 1 2;Link $inner 2 3
$owner=[WolvenKit.RED4.Types.questPhaseNodeDefinition]::new();$owner.Id=[uint16]3
for($i=0;$i -lt 2;$i++){$p=$native.PhasePrefabs[$i].DeepCopy();$p.PrefabNodeRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($full[$i]);$owner.PhaseInstancePrefabs.Add($p)}
Set-RedHandleProperty $owner PhaseGraph $inner
[void](New-QuestSocket $owner 'CutDestination' ([WolvenKit.RED4.Types.Enums+questSocketType]::CutDestination));[void](New-QuestSocket $owner 'In1' ([WolvenKit.RED4.Types.Enums+questSocketType]::Input))
$outer=[WolvenKit.RED4.Types.questGraphDefinition]::new();Put $outer (New-InputNode 0 'In1');Put $outer (Pause 1 $guard);Put $outer (New-SetFactNode 2 'PTFRPH3_Claimed' 1);Put $outer $owner;Link $outer 0 1;Link $outer 1 2;Link $outer 2 3 'In1'
$root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();$root.CookingPlatform=[WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC;Set-RedHandleProperty $root Graph $outer
$file=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$file.RootChunk=$root
New-Item -ItemType Directory $C|Out-Null;Copy-Item (Join-Path $B 'archive_source') (Join-Path $C 'archive_source') -Recurse;Copy-Item (Join-Path $B 'package') (Join-Path $C 'package') -Recurse
$depot='towercontinued\phone_studios_ph3\studio_support.questphase';$raw=Join-Path (Join-Path $C 'archive_source') $depot;Write-Cr2wFile $file $raw;Export-Cr2wJson (Read-Cr2wFile $raw) (Join-Path $C 'owner_readback_01.json')
$xl=Join-Path $C 'package/archive/pc/mod/zzzz_PTFR_Combined.archive.xl';$x=[IO.File]::ReadAllText($xl);$nl=if($x.Contains("`r`n")){"`r`n"}else{"`n"};$entry=@("    - path: $depot",'      parent: ep1\quest\ep1.quest','      input:','        node: [1]','        socket: Out') -join $nl
if($x.Contains($depot) -or [regex]::Matches($x,'(?m)^streaming:').Count -ne 1){throw 'XL anchor drift'}
[IO.File]::WriteAllText($xl,$x.Replace('streaming:',$entry+$nl+'streaming:'),[Text.UTF8Encoding]::new($false))
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$s=[IO.File]::Create((Join-Path $C 'package/archive/pc/mod/zzzz_PTFR_Combined.archive'))
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new((Join-Path $C 'archive_source')),$s)){throw 'Pack failed'}}finally{$s.Dispose()}
@{status='BUILT_NOT_INSTALLED';depot=$depot;facts=$facts;prefabs=$full;native_source=$nativeRow[0];native_capture='diagnostics/phone_expansion_ph3_20261029_01/native_04';root_prefabs=0;new_owner_prefabs=2;native_fact_writes=0;script_changes=0}|ConvertTo-Json -Depth 12|Set-Content (Join-Path $C 'build_01.json') -Encoding utf8NoBOM
'PH3_BUILT_NOT_INSTALLED'
