Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$out=Join-Path $PSScriptRoot 'independent_01.json'
if(Test-Path $out){throw 'Preserve independent verification'}
$checks=[Collections.Generic.List[string]]::new();$pins=[Collections.Generic.List[object]]::new()
function Check([string]$name,[bool]$ok){if(!$ok){throw $name};$checks.Add($name)}
function Json($x){return [WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($x,[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())}
function Pin([string]$p){$pins.Add(@{path=[IO.Path]::GetFullPath($p);sha256=(Get-FileHash -LiteralPath $p).Hash})}
$specs=@(@{id=200;walk=@(14,3);event=19},@{id=202;walk=@(14,6);event=19},@{id=210;walk=@(14,15);event=19},@{id=461;walk=@(35,4,36);event=13})
$rows=@();$common=@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;q307_active=0;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;PTFRBASE_Suspended=0;q305_johnny_scene_active=0;q115_point_of_no_return=0;q000_done=1}
foreach($s in $specs){
 $id=$s.id;$prefix="PTFRWA3ENV_${id}_";$old="PTFRWW2_${id}_"
 $stem=if($id -eq 461){'base_open_world_combat_events_westbrook_japan_town_ce_wbr_jpn_phase.questphase'}else{'base_open_world_combat_events_pacifica_west_wind_estate_ce_pac_wwd_phase.questphase'}
 $nativePath=Join-Path $ws ('diagnostics/world_npc_idle_20261026_01/combat_owners/'+$stem)
 $native=Read-Cr2wFile $nativePath;$g=$native.RootChunk.Graph.Chunk
 foreach($n in $s.walk){$g=(Get-QuestNode $g $n).PhaseGraph.Chunk}
 $expected=Get-QuestNode $g $s.event
 $rel="towercontinued/world_support_wa3/environment_${id}.questphase";$path=Join-Path (Split-Path $PSScriptRoot -Parent) ('candidate_01/source/'+$rel)
 $f=Read-Cr2wFile $path;$c=$f.RootChunk.Graph.Chunk;$actual=Get-QuestNode $c $s.event
 Check "$id exact native world-event payload" ((Json $actual.Type.Chunk) -ceq (Json $expected.Type.Chunk))
 Check "$id only visibility event" ($actual.Type.Chunk.GetType().Name -ceq 'questTogglePrefabVariant_NodeType')
 Check "$id nine nodes" ($c.Nodes.Count -eq 9)
 $expectedEdges=@('0.Out -> 1.In','1.Out -> 2.In','2.Out -> 3.In','3.Out -> 4.In','4.Out -> 5.In',("5.Out -> "+$s.event+'.In'),($s.event.ToString()+'.Out -> 7.In'),'7.Out -> 8.In')|Sort-Object
 Check "$id exactly bounded one-way edges" ((@(Get-GraphEdges $c|Sort-Object)-join '|') -ceq ($expectedEdges -join '|'))
 $guard=(Get-QuestNode $c 2).Condition.Chunk
 Check "$id AND gate" ($guard.GetType().Name -ceq 'questLogicalCondition' -and $guard.Operation.ToString() -ceq 'AND' -and $guard.Conditions.Count -eq 17)
 $facts=@{}+$common;$facts[$old+'Claimed']=1;$facts[$old+'Entered']=1;$facts[$old+'Hold']=0;$facts[$prefix+'Claimed']=0
 $conditions=@($guard.Conditions|ForEach-Object {$_.Chunk});$found=@{}
 foreach($condition in $conditions){
  $j=Json $condition|ConvertFrom-Json -Depth 30
  if($condition.GetType().Name -eq 'questFactsDBCondition'){
   $t=$condition.Type.Chunk
   Check "$id fact is equality" ($t.GetType().Name -ceq 'questVarComparison_ConditionType' -and $t.ComparisonType.ToString() -ceq 'Equal')
   $found[$t.FactName.ToString()]=[int]$t.Value
  }
 }
 Check "$id all16 exact facts" (($found|ConvertTo-Json -Compress) -and $found.Count -eq 16)
 foreach($name in $facts.Keys){Check "$id guard $name" ($found.ContainsKey($name) -and $found[$name] -eq $facts[$name])}
 $ready=@($conditions|Where-Object {$_.GetType().Name -eq 'questSpawnerCondition'})
 Check "$id native Ready gate" ($ready.Count -eq 1 -and $ready[0].Type.Chunk.GetType().Name -ceq 'questSpawnerReady_ConditionType')
 $writes=@{};foreach($node in $c.Nodes){if($node.Chunk.GetType().Name -eq 'questFactsDBManagerNodeDefinition'){$t=$node.Chunk.Type.Chunk;$writes[$t.FactName.ToString()]=[int]$t.Value}}
 Check "$id five private fact writes" ($writes.Count -eq 4 -and $writes[$prefix+'Claimed'] -eq 1 -and $writes[$prefix+'Entered'] -eq 1 -and $writes[$prefix+'Finished'] -eq 1 -and $writes[$prefix+'Ready'] -eq 0)
 foreach($name in $writes.Keys){Check "$id no native fact write $name" ($name.StartsWith($prefix))}
 Check "$id terminal Hold pause" ((Get-QuestNode $c 8).Condition.Chunk.Type.Chunk.FactName.ToString() -ceq ($prefix+'Hold'))
 Pin $path;Pin $nativePath;$rows+=@{depot=$rel.Replace('/','\');sha256=(Get-FileHash $path).Hash;id=$id}
}
Pin $PSCommandPath
@{status='PASS';checks=$checks;check_count=$checks.Count;resources=$rows;pins=$pins;game_writes=0;save_writes=0}|ConvertTo-Json -Depth 30|Set-Content -LiteralPath $out -Encoding utf8NoBOM
@{status='PASS';checks=$checks.Count}|ConvertTo-Json
