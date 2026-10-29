# One exact native prefab-only owner, same lifecycle and gates as W3.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$out=Join-Path $PSScriptRoot 'candidate_01'
$proofPath=Join-Path $PSScriptRoot 'coverage_review/support_assessment_01.json'
$proof=Get-Content -LiteralPath $proofPath -Raw|ConvertFrom-Json -Depth 100
if($proof.checks_passed -ne 40){throw 'Support proof drift'}
$nativePath=Join-Path $PSScriptRoot 'coverage_review/shooting_sources_01/basegame_4_gamedata.archive/ce_std_arr_phase.questphase'
if((Get-FileHash -LiteralPath $nativePath).Hash -cne $proof.candidate250.native_binary_sha256){throw 'Native source drift'}
$native=Read-Cr2wFile $nativePath
$original=Get-QuestNode ((Get-QuestNode $native.RootChunk.Graph.Chunk 24).PhaseGraph.Chunk) 95
if($original.PhaseInstancePrefabs.Count -ne 1 -or $original.PhaseInstancePrefabs[0].PrefabNodeRef.ToString() -cne $proof.candidate250.prefab){throw 'Exact native prefab identity drift'}
$relative='towercontinued\world_actions_wa2\group250_support.questphase'
$dest=Join-Path (Join-Path $out 'source') $relative
if(Test-Path -LiteralPath $dest){throw 'Preserve candidate resource'}
[void][IO.Directory]::CreateDirectory((Split-Path $dest -Parent))
$template=Read-Cr2wFile (Join-Path $ws 'prealpha/coaster_jean_jc1/candidate_01/archive_source/towercontinued/sidejobs_s30/entries/mq006_rollercoaster.questphase')
$pauseTemplate=Get-QuestNode $template.RootChunk.Graph.Chunk 65003
function Put($g,$n){Add-RedHandle $g.Nodes $n}
function Link($g,$a,$b,$i='In'){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $a) 'Out') (Get-QuestSocket (Get-QuestNode $g $b) $i))}
function Pause($id,$condition){
 $n=$pauseTemplate.DeepCopy();$n.Id=[uint16]$id
 foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()}
 Set-RedHandleProperty $n Condition $condition
 return $n
}
$prefix='PTFRWW2_250_'
$facts=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;q307_active=0;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;PTFRBASE_Suspended=0;q305_johnny_scene_active=0;q115_point_of_no_return=0;q000_done=1}
$facts[$prefix+'Request']=1;$facts[$prefix+'Claimed']=0;$facts[$prefix+'Entered']=0;$facts[$prefix+'Hold']=0
$guard=[WolvenKit.RED4.Types.questLogicalCondition]::new();$guard.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
foreach($key in $facts.Keys){Add-RedHandle $guard.Conditions (New-FactCondition $key $facts[$key] ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))}
$inner=[WolvenKit.RED4.Types.questGraphDefinition]::new()
Put $inner (New-InputNode 0 'In1');Put $inner (New-SetFactNode 1 ($prefix+'Entered') 1)
Put $inner (Pause 2 (New-FactCondition ($prefix+'Hold') 1 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal)))
Link $inner 0 1;Link $inner 1 2
$owner=[WolvenKit.RED4.Types.questPhaseNodeDefinition]::new();$owner.Id=[uint16]105
$owner.PhaseInstancePrefabs.Add($original.PhaseInstancePrefabs[0].DeepCopy())
Set-RedHandleProperty $owner PhaseGraph $inner
[void](New-QuestSocket $owner 'CutDestination' ([WolvenKit.RED4.Types.Enums+questSocketType]::CutDestination))
[void](New-QuestSocket $owner 'In1' ([WolvenKit.RED4.Types.Enums+questSocketType]::Input))
$outer=[WolvenKit.RED4.Types.questGraphDefinition]::new()
Put $outer (New-InputNode 0 'In1');Put $outer (New-SetFactNode 100 ($prefix+'Ready') 1)
Put $outer (Pause 101 $guard);Put $outer (New-SetFactNode 102 ($prefix+'Claimed') 1)
Put $outer (New-SetFactNode 103 ($prefix+'Request') 0);Put $outer (New-SetFactNode 104 ($prefix+'Ready') 0);Put $outer $owner
Link $outer 0 100;Link $outer 100 101;Link $outer 101 102;Link $outer 102 103;Link $outer 103 104;Link $outer 104 105 'In1'
$root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();$root.CookingPlatform=[WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC
Set-RedHandleProperty $root Graph $outer
$file=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$file.RootChunk=$root
Write-Cr2wFile $file $dest
$read=Read-Cr2wFile $dest
if($read.RootChunk.Graph.Chunk.Nodes.Count -ne 7){throw 'Readback outer count'}
$ro=Get-QuestNode $read.RootChunk.Graph.Chunk 105
if($ro.PhaseGraph.Chunk.Nodes.Count -ne 3 -or $ro.PhaseInstancePrefabs[0].PrefabNodeRef.ToString() -cne $proof.candidate250.prefab){throw 'Readback support ownership'}
Export-Cr2wJson $read (Join-Path $out 'support_owner_readback_01.json')
$summary=@{status='BUILT_EXACT_GROUP250_SUPPORT_OWNER';resource=$relative;path=$dest;sha256=(Get-FileHash -LiteralPath $dest).Hash;prefix=$prefix;outer_nodes=7;inner_nodes=3;guards=16;native_binary_sha256=$proof.candidate250.native_binary_sha256;prefab=$proof.candidate250.prefab;game_writes=0;save_writes=0}
[IO.File]::WriteAllText((Join-Path $out 'support_owner_proof_01.json'),($summary|ConvertTo-Json -Depth 15)+"`n",[Text.UTF8Encoding]::new($false))
$summary|ConvertTo-Json -Depth 15
