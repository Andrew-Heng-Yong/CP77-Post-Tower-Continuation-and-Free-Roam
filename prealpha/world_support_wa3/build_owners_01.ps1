# Native prefab support only; persistent admission receipts and no encounter restart.
param([string]$ManifestName='manifest_01.json',[string]$ProofName='owner_proof_01.json')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$manifestPath=Join-Path $PSScriptRoot $ManifestName
$manifest=Get-Content -LiteralPath $manifestPath -Raw|ConvertFrom-Json -Depth 100
if($manifest.status -cne 'WA3_REVIEWED_NATIVE_SUPPORT_COHORT'){throw 'Unapproved manifest'}
$out=Join-Path $PSScriptRoot 'candidate_01'
$template=Read-Cr2wFile (Join-Path $ws 'prealpha/coaster_jean_jc1/candidate_01/archive_source/towercontinued/sidejobs_s30/entries/mq006_rollercoaster.questphase')
$pauseTemplate=Get-QuestNode $template.RootChunk.Graph.Chunk 65003
function Put($g,$n){Add-RedHandle $g.Nodes $n}
function Link($g,$a,$b,$inputName='In'){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $a) 'Out') (Get-QuestSocket (Get-QuestNode $g $b) $inputName))}
function Pause($id,$condition){$n=$pauseTemplate.DeepCopy();$n.Id=[uint16]$id;foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()};Set-RedHandleProperty $n Condition $condition;return $n}
$globals=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;q307_active=0;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;PTFRBASE_Suspended=0;q305_johnny_scene_active=0;q115_point_of_no_return=0;q000_done=1}
$proof=@()
foreach($cohort in @($manifest.groups|Group-Object native_binary)){
 $nativePath=[string]$cohort.Name
 if(![IO.Path]::IsPathRooted($nativePath)){$nativePath=Join-Path $ws $nativePath}
 $nativeDigest=(Get-FileHash -LiteralPath $nativePath).Hash
 if(@($cohort.Group|Where-Object native_binary_sha256 -cne $nativeDigest).Count){throw 'Native phase source drift'}
 $native=Read-Cr2wFile $nativePath
 $outer=[WolvenKit.RED4.Types.questGraphDefinition]::new();Put $outer (New-InputNode 0 'In1')
 $sequence=0;$local=@()
 foreach($g in @($cohort.Group|Sort-Object id)){
  $graph=$native.RootChunk.Graph.Chunk;$ids=@($g.node_path.Split('/')|Select-Object -Skip 1);$original=$null
  for($j=0;$j -lt $ids.Count;$j++){$original=Get-QuestNode $graph ([int]$ids[$j]);if(!$original){throw "Missing owner $($g.id)"};if($j -lt $ids.Count-1){$graph=$original.PhaseGraph.Chunk}}
  $selectedPrefab=$null;$prefabIndex=-1
  $wantedSourceRef=[string]$g.prefab
  if($g.PSObject.Properties['native_prefab'] -and $g.native_prefab){$wantedSourceRef=[string]$g.native_prefab}
  for($pi=0;$pi -lt $original.PhaseInstancePrefabs.Count;$pi++){
   $candidateRef=$original.PhaseInstancePrefabs[$pi].PrefabNodeRef.ToString()
   $matches=$original.PhaseInstancePrefabs.Count -eq 1 -or $candidateRef -ceq $wantedSourceRef -or $candidateRef -ceq $wantedSourceRef.Substring($wantedSourceRef.LastIndexOf('/')+1) -or ($candidateRef.StartsWith('$/') -and $wantedSourceRef.StartsWith('$/') -and [WolvenKit.RED4.Types.NodeRef]::CalculateHash($candidateRef) -eq [WolvenKit.RED4.Types.NodeRef]::CalculateHash($wantedSourceRef))
   if($matches){if($null -ne $selectedPrefab){throw "Ambiguous native prefab $($g.id)"};$selectedPrefab=$original.PhaseInstancePrefabs[$pi];$prefabIndex=$pi}
  }
  if($null -eq $selectedPrefab){throw "Exact native prefab missing $($g.id)"}
  $sourceRef=$selectedPrefab.PrefabNodeRef.ToString()
  $hashEquivalent=$sourceRef.StartsWith('$/') -and [WolvenKit.RED4.Types.NodeRef]::CalculateHash($sourceRef) -eq [WolvenKit.RED4.Types.NodeRef]::CalculateHash([string]$g.prefab)
  if(!$g.identity_repaired -and !$hashEquivalent -and $sourceRef -cne $g.prefab -and $sourceRef -cne $g.prefab.Substring($g.prefab.LastIndexOf('/')+1)){throw "Unreviewed native prefab alias $($g.id): $sourceRef"}
  $base=100+$sequence*10;$sequence++;$prefix=[string]$g.prefix
  $facts=[ordered]@{};foreach($key in $globals.Keys){$facts[$key]=$globals[$key]}
  $facts[$prefix+'Request']=1;$facts[$prefix+'Claimed']=0;$facts[$prefix+'Entered']=0;$facts[$prefix+'Hold']=0
  $guard=[WolvenKit.RED4.Types.questLogicalCondition]::new();$guard.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
  foreach($key in $facts.Keys){Add-RedHandle $guard.Conditions (New-FactCondition $key $facts[$key] ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))}
  foreach($f in $g.native_admission_facts){
   $comparison=[WolvenKit.RED4.Types.Enums+EComparisonType]::Equal;$value=[int]$f.value
   if($f.comparison -ceq 'Greater'){$comparison=[WolvenKit.RED4.Types.Enums+EComparisonType]::GreaterOrEqual;$value++}elseif($f.comparison -cne 'Equal'){throw 'Unreviewed comparison'}
   Add-RedHandle $guard.Conditions (New-FactCondition $f.fact $value $comparison)
  }
  $inner=[WolvenKit.RED4.Types.questGraphDefinition]::new();Put $inner (New-InputNode 0 'In1');Put $inner (New-SetFactNode 1 ($prefix+'Entered') 1);Put $inner (Pause 2 (New-FactCondition ($prefix+'Hold') 1 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal)));Link $inner 0 1;Link $inner 1 2
  $owner=[WolvenKit.RED4.Types.questPhaseNodeDefinition]::new();$owner.Id=[uint16]($base+5)
  $prefab=$selectedPrefab.DeepCopy();$prefab.PrefabNodeRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit([string]$g.owner_prefab);$owner.PhaseInstancePrefabs.Add($prefab)
  Set-RedHandleProperty $owner PhaseGraph $inner
  [void](New-QuestSocket $owner 'CutDestination' ([WolvenKit.RED4.Types.Enums+questSocketType]::CutDestination));[void](New-QuestSocket $owner 'In1' ([WolvenKit.RED4.Types.Enums+questSocketType]::Input))
  Put $outer (New-SetFactNode $base ($prefix+'Ready') 1);Put $outer (Pause ($base+1) $guard);Put $outer (New-SetFactNode ($base+2) ($prefix+'Claimed') 1);Put $outer (New-SetFactNode ($base+3) ($prefix+'Request') 0);Put $outer (New-SetFactNode ($base+4) ($prefix+'Ready') 0);Put $outer $owner
  Link $outer 0 $base;Link $outer $base ($base+1);Link $outer ($base+1) ($base+2);Link $outer ($base+2) ($base+3);Link $outer ($base+3) ($base+4);Link $outer ($base+4) ($base+5) 'In1'
  $local+=@{id=$g.id;prefix=$prefix;native_ref=$sourceRef;native_prefab=$g.prefab;private_ref=$g.owner_prefab;owner_node=$base+5;guard_node=$base+1;guard_conditions=$guard.Conditions.Count;native_admission_facts=$g.native_admission_facts;native_ref_hash_equivalent=$hashEquivalent;native_prefab_index=$prefabIndex;native_prefab_count=$original.PhaseInstancePrefabs.Count}
 }
 $root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();$root.CookingPlatform=[WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC;Set-RedHandleProperty $root Graph $outer
 $file=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$file.RootChunk=$root
 $relative='towercontinued\world_support_wa3\support_'+$nativeDigest.Substring(0,12).ToLower()+'.questphase';$dest=Join-Path (Join-Path $out 'source') $relative
 if(Test-Path $dest){throw 'Preserve built owner resource'}
 [void][IO.Directory]::CreateDirectory((Split-Path $dest -Parent));Write-Cr2wFile $file $dest
 $read=Read-Cr2wFile $dest;if($read.RootChunk.Graph.Chunk.Nodes.Count -ne 1+6*$local.Count){throw 'Readback node count'}
 foreach($r in $local){$ownerRead=Get-QuestNode $read.RootChunk.Graph.Chunk $r.owner_node;if($ownerRead.PhaseInstancePrefabs.Count -ne 1 -or [WolvenKit.RED4.Types.NodeRef]::CalculateHash($ownerRead.PhaseInstancePrefabs[0].PrefabNodeRef.ToString()) -ne [WolvenKit.RED4.Types.NodeRef]::CalculateHash([string]$r.private_ref) -or $ownerRead.PhaseGraph.Chunk.Nodes.Count -ne 3){throw "Readback owner mismatch $($r.id)"}}
 $jp=Join-Path $out ('owner_readback_'+$nativeDigest.Substring(0,12).ToLower()+'.json');Export-Cr2wJson $read $jp
 $proof+=@{source=$nativePath;source_sha256=$nativeDigest;resource=$relative;owners=$local.Count;nodes=$read.RootChunk.Graph.Chunk.Nodes.Count;sha256=(Get-FileHash $dest).Hash;json=$jp;json_sha256=(Get-FileHash $jp).Hash;groups=$local}
}
$summary=@{status='PASS_WA3_PREFAB_OWNERS_BINARY_READBACK';manifest_sha256=(Get-FileHash $manifestPath).Hash;owners=($proof|Measure-Object owners -Sum).Sum;resources=$proof.Count;proofs=$proof;game_writes=0;save_writes=0}
[IO.File]::WriteAllText((Join-Path $out $ProofName),($summary|ConvertTo-Json -Depth 60)+"`n",[Text.UTF8Encoding]::new($false))
@{status=$summary.status;owners=$summary.owners;resources=$summary.resources}|ConvertTo-Json
