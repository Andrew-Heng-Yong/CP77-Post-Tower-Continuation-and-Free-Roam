Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$out=Join-Path $PSScriptRoot 'independent_01.json';if(Test-Path $out){throw 'Preserve evidence'}
function Json($x){return [WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($x,[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())}
$checks=[Collections.Generic.List[string]]::new();function Check($label,$ok){if(!$ok){throw $label};$checks.Add($label)}
$nativePath=Join-Path $PSScriptRoot '../native_review/outside_phases_native_01/basegame_4_gamedata.archive/pac_wwd_phase.questphase'
$path=Join-Path $PSScriptRoot '../candidate_01/source/towercontinued/world_support_wa3/greeting_wwd.questphase'
$n=Read-Cr2wFile $nativePath;$ng=(Get-QuestNode $n.RootChunk.Graph.Chunk 3).PhaseGraph.Chunk
$c=Read-Cr2wFile $path;$g=$c.RootChunk.Graph.Chunk
$community='$/03_night_city/c_pacifica/#west_wind_estate_001/west_wind_estate_openworld_prefabZERJ55I/west_wind_estate_openworld_community_prefabVYVTSYI/#pac_wwd_ripper_com'
$trigger='$/03_night_city/c_pacifica/#west_wind_estate_001/wwd_service_points_prefabUGGY6KA/pac_wwd_ripdoc_01_prefabISH67RQ/pac_wwd_ripdoc_01_openworld_prefabANGY5VQ/#pac_wwd_ripdoc_01_tr_rec'
$prefix='PTFRWA3GREETING_WWD_'
Check 'Nine nodes only' ($g.Nodes.Count -eq 9)
$want=@('0.Out -> 100.In','100.Out -> 101.In','101.Out -> 102.In','102.Out -> 3.In','3.Out -> 9.In','9.True -> 4.In','4.Out -> 8.In','8.Out -> 7.In','7.Out -> 3.In')|Sort-Object
Check 'Exact entry and native cooldown loop edges' ((@(Get-GraphEdges $g|Sort-Object)-join '|') -ceq ($want -join '|'))
foreach($id in @(4,7,8,9)){
 $nativeNode=Get-QuestNode $ng $id;$node=Get-QuestNode $g $id
 foreach($s in $nativeNode.Sockets){$s.Chunk.Connections.Clear()};foreach($s in $node.Sockets){$s.Chunk.Connections.Clear()}
 if($id -eq 4){$nativeNode.Type.Chunk.Params[0].PuppetRef.Reference=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($community)}
 if($id -eq 9){$nativeNode.Condition.Chunk.Type.Chunk.ObjectRef.Reference=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($community)}
 Check "Exact native node$id payload with only qualified actor ref" ((Json $nativeNode) -ceq (Json $node))
}
$facts=@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;q307_active=0;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;PTFRBASE_Suspended=0;q305_johnny_scene_active=0;q115_point_of_no_return=0;q000_done=1}
foreach($id in @(100,3)){
 $guard=(Get-QuestNode $g $id).Condition.Chunk
 Check "$id AND gate14" ($guard.GetType().Name -ceq 'questLogicalCondition' -and $guard.Operation.ToString() -ceq 'AND' -and $guard.Conditions.Count -eq 14)
 $conds=@($guard.Conditions|ForEach-Object {$_.Chunk});$actual=@{}
 foreach($cond in $conds){if($cond.GetType().Name -eq 'questFactsDBCondition'){$t=$cond.Type.Chunk;Check "$id equality guard" ($t.GetType().Name -ceq 'questVarComparison_ConditionType' -and $t.ComparisonType.ToString() -ceq 'Equal');$actual[$t.FactName.ToString()]=[int]$t.Value}}
 foreach($key in $facts.Keys){Check "$id $key" ($actual.ContainsKey($key) -and $actual[$key] -eq $facts[$key])}
 Check "$id exact fact count" ($actual.Count -eq $(if($id -eq 100){13}else{12}))
 if($id -eq 100){Check 'Entry claim0 prevents replay' ($actual[$prefix+'Claimed'] -eq 0)}
 $ready=@($conds|Where-Object {$_.GetType().Name -eq 'questSpawnerCondition'})
 Check "$id exact native spawnerReady single entry" ($ready.Count -eq 1 -and $ready[0].Type.Chunk.GetType().Name -ceq 'questSpawnerReady_ConditionType' -and $ready[0].Type.Chunk.SpawnerReference.ToString() -ceq $community -and $ready[0].Type.Chunk.CommunityEntryNames.Count -eq 1 -and $ready[0].Type.Chunk.CommunityEntryNames[0].ToString() -ceq 'ripdoc_rec')
 if($id -eq 3){$nt=(Get-QuestNode $ng 3).Condition.Chunk;$nt.TriggerAreaRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($trigger);$tr=@($conds|Where-Object {$_.GetType().Name -eq $nt.GetType().Name});Check 'Loop preserves exact native triggercondition' ($tr.Count -eq 1 -and (Json $tr[0]) -ceq (Json $nt))}
}
$writes=@($g.Nodes|Where-Object {$_.Chunk.GetType().Name -eq 'questFactsDBManagerNodeDefinition'})
Check 'Only two private receipt writers' ($writes.Count -eq 2)
foreach($w in $writes){$t=$w.Chunk.Type.Chunk;Check 'Private receipt only no native reset' ($t.FactName.ToString() -in @(($prefix+'Claimed'),($prefix+'Entered')) -and [int]$t.Value -eq 1)}
Check 'No community controller spawn or reactivate node' (@($g.Nodes|Where-Object {$_.Chunk.GetType().Name -like '*Community*'}).Count -eq 0)
$pins=@($path,$nativePath,$PSCommandPath)|ForEach-Object {@{path=[IO.Path]::GetFullPath($_);sha256=(Get-FileHash -LiteralPath $_).Hash}}
@{status='PASS';check_count=$checks.Count;checks=$checks;resources=@(@{depot='towercontinued\world_support_wa3\greeting_wwd.questphase';sha256=(Get-FileHash $path).Hash});pins=$pins;game_writes=0;save_writes=0}|ConvertTo-Json -Depth 30|Set-Content -LiteralPath $out -Encoding utf8NoBOM
@{status='PASS';checks=$checks.Count}|ConvertTo-Json
