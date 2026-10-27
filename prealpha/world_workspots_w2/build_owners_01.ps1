# Private prefab-only owners for exact, source-reviewed ambient support.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$manifestPath=Join-Path $PSScriptRoot 'manifest_02.json'
$manifest=Get-Content -LiteralPath $manifestPath -Raw|ConvertFrom-Json -Depth 80
if($manifest.status -cne 'EXACT_NATIVE_IDENTITY_CANDIDATES_NOT_DEPLOYABLE' -or $manifest.owner_count -ne 206){throw 'Input cohort changed'}
$out=Join-Path $PSScriptRoot 'candidate_01'
if(Test-Path -LiteralPath $out){throw 'Preserve candidate; use successor'}
[void][IO.Directory]::CreateDirectory($out)
$template=Read-Cr2wFile (Join-Path $ws 'prealpha/coaster_jean_jc1/candidate_01/archive_source/towercontinued/sidejobs_s30/entries/mq006_rollercoaster.questphase')
$pauseTemplate=Get-QuestNode $template.RootChunk.Graph.Chunk 65003
function Put($graph,$node){Add-RedHandle $graph.Nodes $node}
function Link($graph,$a,$b,$inputName='In') {[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $graph $a) 'Out') (Get-QuestSocket (Get-QuestNode $graph $b) $inputName))}
function Pause($id,$condition){
 $node=$pauseTemplate.DeepCopy();$node.Id=[uint16]$id
 foreach($socket in $node.Sockets){$socket.Chunk.Connections.Clear()}
 Set-RedHandleProperty $node Condition $condition
 return $node
}
$globals=[ordered]@{
 PostTowerFreeRoamActive=1;PTFRP0_DR13=1;q307_active=0;q307_done=1;
 q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;
 PTFRBASE_Suspended=0;q305_johnny_scene_active=0;q115_point_of_no_return=0;q000_done=1
}
$cache=@{};$proof=[Collections.Generic.List[object]]::new()
$groups=@($manifest.groups|Where-Object {$_.id -ne 183}|Group-Object native_binary)
foreach($cohort in $groups){
 $nativePath=Join-Path $ws $cohort.Name
 $nativeDigest=(Get-FileHash -LiteralPath $nativePath -Algorithm SHA256).Hash
 if(@($cohort.Group|Where-Object native_binary_sha256 -cne $nativeDigest).Count){throw "Native source drift $nativePath"}
 $native=Read-Cr2wFile $nativePath
 $outer=[WolvenKit.RED4.Types.questGraphDefinition]::new()
 Put $outer (New-InputNode 0 'In1')
 $sequence=0;$local=[Collections.Generic.List[object]]::new()
 foreach($g in @($cohort.Group|Sort-Object id)){
  $graph=$native.RootChunk.Graph.Chunk;$ids=@($g.node_path.Split('/')|Select-Object -Skip 1)
  $original=$null
  for($j=0;$j -lt $ids.Count;$j++){
   $original=Get-QuestNode $graph ([int]$ids[$j])
   if(-not $original){throw "Original owner absent $($g.id)"}
   if($j -lt $ids.Count-1){$graph=$original.PhaseGraph.Chunk}
  }
  if($original.PhaseInstancePrefabs.Count -ne 1){throw "Prefab count drift $($g.id)"}
  $sourceRef=$original.PhaseInstancePrefabs[0].PrefabNodeRef.ToString()
  $alias=$g.prefab.Substring($g.prefab.LastIndexOf('/')+1)
  if($sourceRef -cne $alias -and $sourceRef -cne $g.prefab){throw "Prefab identity mismatch $($g.id)"}
  $base=100+$sequence*10;$sequence+=1
  $prefix=[string]$g.prefix
  $facts=[ordered]@{};foreach($key in $globals.Keys){$facts[$key]=$globals[$key]}
  $facts[$prefix+'Request']=1;$facts[$prefix+'Claimed']=0
  $facts[$prefix+'Entered']=0;$facts[$prefix+'Hold']=0
  $guard=[WolvenKit.RED4.Types.questLogicalCondition]::new()
  $guard.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
  foreach($key in $facts.Keys){Add-RedHandle $guard.Conditions (New-FactCondition $key $facts[$key] ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))}
  $inner=[WolvenKit.RED4.Types.questGraphDefinition]::new()
  Put $inner (New-InputNode 0 'In1')
  Put $inner (New-SetFactNode 1 ($prefix+'Entered') 1)
  Put $inner (Pause 2 (New-FactCondition ($prefix+'Hold') 1 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal)))
  Link $inner 0 1;Link $inner 1 2
  $owner=[WolvenKit.RED4.Types.questPhaseNodeDefinition]::new();$owner.Id=[uint16]($base+5)
  $prefab=$original.PhaseInstancePrefabs[0].DeepCopy()
  $prefab.PrefabNodeRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit([string]$g.prefab)
  $owner.PhaseInstancePrefabs.Add($prefab)
  Set-RedHandleProperty $owner PhaseGraph $inner
  [void](New-QuestSocket $owner 'CutDestination' ([WolvenKit.RED4.Types.Enums+questSocketType]::CutDestination))
  [void](New-QuestSocket $owner 'In1' ([WolvenKit.RED4.Types.Enums+questSocketType]::Input))
  Put $outer (New-SetFactNode $base ($prefix+'Ready') 1)
  Put $outer (Pause ($base+1) $guard)
  Put $outer (New-SetFactNode ($base+2) ($prefix+'Claimed') 1)
  Put $outer (New-SetFactNode ($base+3) ($prefix+'Request') 0)
  Put $outer (New-SetFactNode ($base+4) ($prefix+'Ready') 0)
  Put $outer $owner
  Link $outer 0 $base;Link $outer $base ($base+1);Link $outer ($base+1) ($base+2)
  Link $outer ($base+2) ($base+3);Link $outer ($base+3) ($base+4);Link $outer ($base+4) ($base+5) 'In1'
  $local.Add([ordered]@{id=$g.id;prefix=$prefix;native_ref=$sourceRef;private_ref=$g.prefab;owner_node=$base+5})
 }
 $root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();$root.CookingPlatform=[WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC
 Set-RedHandleProperty $root Graph $outer
 $file=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$file.RootChunk=$root
 $stem=[IO.Path]::GetFileNameWithoutExtension($nativePath)
 $relative='towercontinued\world_workspots_w2\'+$stem+'_owners.questphase'
 $dest=Join-Path (Join-Path $out 'source') $relative
 [void][IO.Directory]::CreateDirectory((Split-Path $dest -Parent))
 Write-Cr2wFile $file $dest
 $read=Read-Cr2wFile $dest
 if($read.RootChunk.Graph.Chunk.Nodes.Count -ne 1+6*$local.Count){throw "Readback node count $stem"}
 foreach($g in $local){
  $ownerRead=Get-QuestNode $read.RootChunk.Graph.Chunk $g.owner_node
  if($ownerRead.PhaseInstancePrefabs.Count -ne 1 -or $ownerRead.PhaseInstancePrefabs[0].PrefabNodeRef.ToString() -cne $g.private_ref -or $ownerRead.PhaseGraph.Chunk.Nodes.Count -ne 3){throw "Readback owner mismatch $($g.id)"}
 }
 $proof.Add([ordered]@{source=$cohort.Name;resource=$relative;owners=$local.Count;nodes=$read.RootChunk.Graph.Chunk.Nodes.Count;sha256=(Get-FileHash -LiteralPath $dest -Algorithm SHA256).Hash;groups=@($local)})
}
if(($proof|Measure-Object owners -Sum).Sum -ne 205){throw 'Owner count mismatch'}
$summary=[ordered]@{status='PRIVATE_PREFAB_OWNERS_BUILT_NOT_PACKED_OR_INSTALLED';manifest_sha256=(Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash;owners=205;resources=$proof.Count;proofs=@($proof);game_writes=0;save_writes=0}
[IO.File]::WriteAllText((Join-Path $out 'owner_proof_01.json'),($summary|ConvertTo-Json -Depth 60)+"`n",[Text.UTF8Encoding]::new($false))
@{status=$summary.status;owners=$summary.owners;resources=$summary.resources}|ConvertTo-Json
