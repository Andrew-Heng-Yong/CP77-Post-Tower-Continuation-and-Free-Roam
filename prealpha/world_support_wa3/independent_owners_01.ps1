# Independent cooked-owner audit. Never trusts builder readback counts or edge lists.
param([string]$ManifestName='manifest_01.json',[string]$OutputName='independent_owners_01.json')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$mp=Join-Path $PSScriptRoot $ManifestName;$m=Get-Content $mp -Raw|ConvertFrom-Json -Depth 100
if($m.status -cne 'WA3_REVIEWED_NATIVE_SUPPORT_COHORT'){throw 'Manifest incomplete'}
$out=Join-Path $PSScriptRoot ('candidate_01/'+$OutputName);if(Test-Path $out){throw 'Preserve independent proof'}
$checks=[Collections.Generic.List[string]]::new();$pins=[Collections.Generic.List[object]]::new();$rows=@()
function Check($label,$ok){if(!$ok){throw $label};$checks.Add($label)}
function Pin($p){$pins.Add(@{path=[IO.Path]::GetFullPath($p);sha256=(Get-FileHash -LiteralPath $p).Hash})}
function Json($x){return [WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($x,[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())}
function AssertWrite($node,$fact,$value){Check ('Private write '+$fact) ($node.GetType().Name -ceq 'questFactsDBManagerNodeDefinition' -and $node.Type.Chunk.GetType().Name -ceq 'questSetVar_NodeType' -and $node.Type.Chunk.FactName.ToString() -ceq $fact -and [int]$node.Type.Chunk.Value -eq $value -and $node.Type.Chunk.SetExactValue.ToString() -ceq 'True')}
$common=@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;q307_active=0;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;PTFRBASE_Suspended=0;q305_johnny_scene_active=0;q115_point_of_no_return=0;q000_done=1}
Check 'Unique owner ids' (@($m.groups.id|Select-Object -Unique).Count -eq $m.groups.Count)
Check 'Unique owner prefabs' (@($m.groups.owner_prefab|Select-Object -Unique).Count -eq $m.groups.Count)
Check 'Unique owner prefixes' (@($m.groups.prefix|Select-Object -Unique).Count -eq $m.groups.Count)
foreach($cohort in @($m.groups|Group-Object native_binary)){
 $nativePath=[string]$cohort.Name;if(![IO.Path]::IsPathRooted($nativePath)){$nativePath=Join-Path $ws $nativePath}
 $digest=(Get-FileHash -LiteralPath $nativePath).Hash
 Check 'Native binary pinned' (@($cohort.Group|Where-Object native_binary_sha256 -cne $digest).Count -eq 0)
 $depot='towercontinued\world_support_wa3\support_'+$digest.Substring(0,12).ToLower()+'.questphase'
 $path=Join-Path $PSScriptRoot ('candidate_01/source/'+$depot)
 $native=Read-Cr2wFile $nativePath;$file=Read-Cr2wFile $path;$g=$file.RootChunk.Graph.Chunk
 Check 'Exact outer node count' ($g.Nodes.Count -eq 1+6*$cohort.Count)
 Check 'Input type and name' ((Get-QuestNode $g 0).GetType().Name -ceq 'questInputNodeDefinition' -and (Get-QuestNode $g 0).SocketName.ToString() -ceq 'In1')
 $allEdges=@();$sequence=0
 foreach($row in @($cohort.Group|Sort-Object id)){
  $id=$row.id;$prefix=[string]$row.prefix;$base=100+10*$sequence;$sequence++
  Check "$id exact namespaced prefix" ($prefix -ceq "PTFRWA3_${id}_")
  $original=$null;$ng=$native.RootChunk.Graph.Chunk;$parts=@($row.node_path.Split('/')|Select-Object -Skip 1)
  for($i=0;$i -lt $parts.Count;$i++){$original=Get-QuestNode $ng ([int]$parts[$i]);if($i -lt $parts.Count-1){$ng=$original.PhaseGraph.Chunk}}
  $owner=Get-QuestNode $g ($base+5)
  Check "$id phase owner" ($owner.GetType().Name -ceq 'questPhaseNodeDefinition' -and $owner.PhaseInstancePrefabs.Count -eq 1 -and $original.PhaseInstancePrefabs.Count -ge 1)
  $mapped=[string]$row.prefab
  $leaves=@($original.PhaseInstancePrefabs)
  if($leaves.Count -gt 1){$leaves=@($leaves|Where-Object {$ref=$_.PrefabNodeRef.ToString();$ref -ceq $mapped -or $ref -ceq $mapped.Substring($mapped.LastIndexOf('/')+1) -or ($ref.StartsWith('$/') -and [WolvenKit.RED4.Types.NodeRef]::CalculateHash($ref) -eq [WolvenKit.RED4.Types.NodeRef]::CalculateHash($mapped))})}
  Check "$id exactly one native leaf selected" ($leaves.Count -eq 1)
  $sourceRef=$leaves[0].PrefabNodeRef.ToString()
  $hashEqual=$sourceRef.StartsWith('$/') -and $mapped.StartsWith('$/') -and [WolvenKit.RED4.Types.NodeRef]::CalculateHash($sourceRef) -eq [WolvenKit.RED4.Types.NodeRef]::CalculateHash($mapped)
  Check "$id native reference is exact, engine-equivalent or explicitly repaired" ($row.identity_repaired -or $sourceRef -ceq $mapped -or $sourceRef -ceq $mapped.Substring($mapped.LastIndexOf('/')+1) -or $hashEqual)
  Check "$id exact approved owner engine ref" ([WolvenKit.RED4.Types.NodeRef]::CalculateHash($owner.PhaseInstancePrefabs[0].PrefabNodeRef.ToString()) -eq [WolvenKit.RED4.Types.NodeRef]::CalculateHash([string]$row.owner_prefab))
  $nativePrefab=$leaves[0].DeepCopy();$nativePrefab.PrefabNodeRef=$owner.PhaseInstancePrefabs[0].PrefabNodeRef
  Check "$id exact native prefab properties except approved ref" ((Json $owner.PhaseInstancePrefabs[0]) -ceq (Json $nativePrefab))
  $inner=$owner.PhaseGraph.Chunk
  Check "$id inner3nodes" ($inner.Nodes.Count -eq 3)
  Check "$id inner exact input" ((Get-QuestNode $inner 0).GetType().Name -ceq 'questInputNodeDefinition' -and (Get-QuestNode $inner 0).SocketName.ToString() -ceq 'In1')
  Check "$id inner2edges" ((@(Get-GraphEdges $inner|Sort-Object)-join '|') -ceq '0.Out -> 1.In|1.Out -> 2.In')
  AssertWrite (Get-QuestNode $inner 1) ($prefix+'Entered') 1
  $hold=(Get-QuestNode $inner 2).Condition.Chunk
  Check "$id Hold is pause" ((Get-QuestNode $inner 2).GetType().Name -ceq 'questPauseConditionNodeDefinition')
  Check "$id persistent Hold1" ($hold.GetType().Name -ceq 'questFactsDBCondition' -and $hold.Type.Chunk.GetType().Name -ceq 'questVarComparison_ConditionType' -and $hold.Type.Chunk.FactName.ToString() -ceq ($prefix+'Hold') -and [int]$hold.Type.Chunk.Value -eq 1 -and $hold.Type.Chunk.ComparisonType.ToString() -ceq 'Equal')
  $guard=(Get-QuestNode $g ($base+1)).Condition.Chunk
  Check "$id gate is pause" ((Get-QuestNode $g ($base+1)).GetType().Name -ceq 'questPauseConditionNodeDefinition')
  Check "$id AND guard count" ($guard.GetType().Name -ceq 'questLogicalCondition' -and $guard.Operation.ToString() -ceq 'AND' -and $guard.Conditions.Count -eq 16+@($row.native_admission_facts).Count)
  $expected=@();foreach($key in $common.Keys){$expected+=($key+'=Equal='+$common[$key])}
  foreach($suffix in @('Request','Claimed','Entered','Hold')){$value=if($suffix -eq 'Request'){1}else{0};$expected+=($prefix+$suffix+'=Equal='+$value)}
  foreach($f in $row.native_admission_facts){$cmp=[string]$f.comparison;$value=[int]$f.value;if($cmp -eq 'Greater'){$cmp='GreaterOrEqual';$value++};$expected+=($f.fact+'='+$cmp+'='+$value)}
  $actual=@();foreach($condition in $guard.Conditions){$cond=$condition.Chunk;Check "$id onlyfactguard" ($cond.GetType().Name -ceq 'questFactsDBCondition' -and $cond.Type.Chunk.GetType().Name -ceq 'questVarComparison_ConditionType');$t=$cond.Type.Chunk;$actual+=($t.FactName.ToString()+'='+$t.ComparisonType.ToString()+'='+[int]$t.Value)}
  Check "$id exact16plusnativeguards" ((@($actual|Sort-Object)-join '|') -ceq (@($expected|Sort-Object)-join '|'))
  AssertWrite (Get-QuestNode $g $base) ($prefix+'Ready') 1
  AssertWrite (Get-QuestNode $g ($base+2)) ($prefix+'Claimed') 1
  AssertWrite (Get-QuestNode $g ($base+3)) ($prefix+'Request') 0
  AssertWrite (Get-QuestNode $g ($base+4)) ($prefix+'Ready') 0
  $allEdges+=('0.Out -> '+$base+'.In')
  for($i=0;$i -lt 5;$i++){$allEdges+=(($base+$i).ToString()+'.Out -> '+($base+$i+1)+$(if($i -eq 4){'.In1'}else{'.In'}))}
 }
 Check 'Exact one-way claim-before-prefab edges' ((@(Get-GraphEdges $g|Sort-Object)-join '|') -ceq (@($allEdges|Sort-Object)-join '|'))
 Pin $path;Pin $nativePath;$rows+=@{depot=$depot;sha256=(Get-FileHash -LiteralPath $path).Hash;owners=$cohort.Count}
}
Pin $mp;Pin $PSCommandPath
@{status='PASS';owners=$m.groups.Count;checks_passed=$checks.Count;checks=$checks;resources=$rows;pins=$pins;game_writes=0;save_writes=0}|ConvertTo-Json -Depth 30|Set-Content -LiteralPath $out -Encoding utf8NoBOM
@{status='PASS';owners=$m.groups.Count;checks=$checks.Count}|ConvertTo-Json
