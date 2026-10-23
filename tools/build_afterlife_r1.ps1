param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\afterlife_world'
$out=Join-Path $WorkspaceRoot 'build\AfterlifeR1'
$source=Join-Path $out 'source'
$rogue=Get-Content (Join-Path $audit 'rogue_world_manifest.json') -Raw|ConvertFrom-Json -Depth 100
$patrons=Get-Content (Join-Path $audit 'patrons_manifest.json') -Raw|ConvertFrom-Json -Depth 100
$dancers=Get-Content (Join-Path $audit 'dancers_manifest.json') -Raw|ConvertFrom-Json -Depth 100
$facts=[ordered]@{};foreach($p in $dancers.guards.psobject.Properties){$facts[$p.Name]=[int]$p.Value};if($facts.Count -ne 15){throw 'Shared Afterlife guard count changed'}
$file=Read-Cr2wFile (Join-Path $WorkspaceRoot 'build\MistyViktorAccessR11\source\towercontinued\misty_viktor_world\access_r11.questphase')
$graph=$file.RootChunk.Graph.Chunk;$pauseTemplate=(Get-QuestNode $graph 70).DeepCopy();$graph.Nodes.Clear();$file.EmbeddedFiles.Clear();$file.RootChunk.PhasePrefabs.Clear()
$vanilla=Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\q307_extracted\raw\ep1\quest\main_quests\q307\phases\q307_06_viktor.questphase')
$spawnTemplate=(Get-QuestNode $vanilla.RootChunk.Graph.Chunk 30).DeepCopy()
$communityAction=@($spawnTemplate.Actions|Where-Object {$_.Type.Chunk.GetType().Name -eq 'questCommunityTemplate_NodeType' -and $_.Type.Chunk.CommunityEntryName.ToString() -eq 'q307_alley_extra_01'})[0].DeepCopy()
$misty=Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\q307_extracted\raw\ep1\quest\main_quests\q307\phases\q307_08_misty.questphase')
$spawnSetAction=(Get-QuestNode (Get-QuestNode $misty.RootChunk.Graph.Chunk 22).PhaseGraph.Chunk 8).Actions[0].DeepCopy()
if($spawnSetAction.Type.Chunk.GetType().Name -ne 'questSpawnSet_NodeType' -or $spawnSetAction.Type.Chunk.Reference.ToString() -ne '#rogue' -or $spawnSetAction.Type.Chunk.EntryName.ToString() -ne 'rogue'){throw 'Original Rogue handoff precedent changed'}
$cleanup=Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\q307_extracted\raw\ep1\quest\main_quests\q307\phases\q307_cleanup.questphase')
$toggleTemplate=(Get-QuestNode $cleanup.RootChunk.Graph.Chunk 22).DeepCopy()
$toggleParam=@($toggleTemplate.Type.Chunk.Params|Where-Object {$_.GetType().Name -eq 'questTogglePrefabVariant_NodeTypeParams' -and @($_.VariantStates|Where-Object {$_.Name.ToString() -eq 'q307_zetatech'}).Count})
if($toggleParam.Count -ne 1 -or $toggleParam[0].VariantStates.Count -ne 1){throw 'Private variant precedent changed'}
function Name([string]$s){return [WolvenKit.RED4.Types.CName]::op_Implicit($s)}
function Ref([string]$s){return [WolvenKit.RED4.Types.NodeRef]::op_Implicit($s)}
function Logic([string]$op,$children){$c=[WolvenKit.RED4.Types.questLogicalCondition]::new();$c.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::$op;foreach($v in $children){Add-RedHandle $c.Conditions $v};return $c}
function Fact([string]$name,[int]$value,[bool]$inverse=$false){return New-FactCondition $name $value $(if($inverse){[WolvenKit.RED4.Types.Enums+EComparisonType]::NotEqual}else{[WolvenKit.RED4.Types.Enums+EComparisonType]::Equal})}
function Guard([bool]$inverse=$false){$p=[Collections.Generic.List[object]]::new();foreach($key in $script:facts.Keys){$p.Add((Fact $key $script:facts[$key] $inverse))};return Logic $(if($inverse){'OR'}else{'AND'}) $p}
function Loaded([string]$ref,[bool]$inverse=$false){$c=[WolvenKit.RED4.Types.questNodeLoadingCondition]::new();$c.ObjectRef=Ref $ref;$c.Inverted=$inverse;return $c}
function State($row,[bool]$inverse=$false){
 $p=[Collections.Generic.List[object]]::new();$p.Add((Guard $inverse));$p.Add((Fact 'PTFRAL1_WorldApplied' 1 $inverse))
 foreach($ref in $row.refs){$p.Add((Loaded $ref $inverse))}
 if($row.role -eq 'rogue'){$p.Add((New-FactCondition 'rogue_default_on' 0 $(if($inverse){[WolvenKit.RED4.Types.Enums+EComparisonType]::LessOrEqual}else{[WolvenKit.RED4.Types.Enums+EComparisonType]::Greater})));$p.Add((Fact 'q116_rogue_dead' 0 $inverse))}
 return Logic $(if($inverse){'OR'}else{'AND'}) $p
}
function Pause([int]$id,$c){$n=$script:pauseTemplate.DeepCopy();$n.Id=[uint16]$id;foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()};Set-RedHandleProperty $n Condition $c;return $n}
function Counter([int]$id,[string]$name){$n=New-SetFactNode $id $name 1;$n.Type.Chunk.SetExactValue=$false;return $n}
$variants=@([ordered]@{name=$rogue.variant_name;owner=$rogue.variant_owner},[ordered]@{name=$patrons.variant_name;owner=$patrons.variant_owner})
function Variants([int]$id,[bool]$show){
 $n=$script:toggleTemplate.DeepCopy();$n.Id=[uint16]$id;foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()};$n.Type.Chunk.Params.Clear()
 foreach($v in $script:variants){$p=$script:toggleParam[0].DeepCopy();$p.PrefabNodeRef=Ref $v.owner;$p.VariantStates[0].Name=Name $v.name;$p.VariantStates[0].Show=$show;[void]$n.Type.Chunk.Params.Add($p)};return $n
}
function Spawn([int]$id,$row,[bool]$acquire){
 $n=$script:spawnTemplate.DeepCopy();$n.Id=[uint16]$id;foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()};$n.Actions.Clear()
 # The native action array preserves authored Deactivate->Reactivate ordering.
 # This is not claimed as a synchronous ownership lease against future adapters.
 if($acquire){
  if($row.original_type -eq 'spawnset'){$a=$script:spawnSetAction.DeepCopy();$a.Type.Chunk.Action=[WolvenKit.RED4.Types.Enums+populationSpawnerObjectCtrlAction]::Deactivate;$a.Type.Chunk.Reference=Ref $row.original_spawner;$a.Type.Chunk.EntryName=Name $row.original_entry;$a.Type.Chunk.PhaseName=Name $row.original_phase}
  elseif($row.original_type -eq 'community'){$a=$script:communityAction.DeepCopy();$a.Type.Chunk.Action=[WolvenKit.RED4.Types.Enums+populationSpawnerObjectCtrlAction]::Deactivate;$a.Type.Chunk.SpawnerReference=Ref $row.original_spawner;$a.Type.Chunk.CommunityEntryName=Name $row.original_entry;$a.Type.Chunk.CommunityEntryPhaseName=Name $row.original_phase}
  else{throw 'Unsupported original Afterlife owner type'}
  [void]$n.Actions.Add($a)
 }
 $a=$script:communityAction.DeepCopy();$a.Type.Chunk.Action=if($acquire){[WolvenKit.RED4.Types.Enums+populationSpawnerObjectCtrlAction]::Reactivate}else{[WolvenKit.RED4.Types.Enums+populationSpawnerObjectCtrlAction]::Deactivate}
 $a.Type.Chunk.SpawnerReference=Ref $row.private_spawner;$a.Type.Chunk.CommunityEntryName=Name $row.entry;$a.Type.Chunk.CommunityEntryPhaseName=Name $row.phase;[void]$n.Actions.Add($a);return $n
}
$rows=[Collections.Generic.List[object]]::new()
foreach($row in $patrons.entries){if($row.entry -match 'tiny_mike'){throw 'Tiny Mike is outside ambient repair scope'};$rows.Add($row)}
$rows.Add([pscustomobject]@{entry=$rogue.entry;phase=$rogue.phase;role='rogue';private_spawner=$rogue.private_community_ref;refs=@($rogue.workspot_ref);original_type='spawnset';original_spawner='#rogue';original_entry='rogue';original_phase='None'})
if($rows.Count -ne 28 -or @($rows|Where-Object {$_.role -eq 'emmerick'}).Count -ne 1){throw 'Afterlife population selection count changed'}
foreach($row in $rows){if($row.refs.Count -lt 1 -or $row.private_spawner -notmatch '^\$/03_night_city/#PTFR' -or @($row.refs|Where-Object {$_ -notmatch '^\$/03_night_city/#PTFR'}).Count){throw 'Private alias scope failed'}}
$edges=[Collections.Generic.List[object]]::new();$branches=[Collections.Generic.List[object]]::new()
function Add($n){Add-RedHandle $script:graph.Nodes $n}
function Link([int]$from,[string]$socket,[int]$to){$script:edges.Add(@($from,$socket,$to));[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $script:graph $from) $socket) (Get-QuestSocket (Get-QuestNode $script:graph $to) 'In'))}
Add (New-InputNode 0 'In1');Add (New-SetFactNode 1 'PTFRAL1_PopulationRegistered' 1);Add (New-SetFactNode 2 'PTFRAL1_WorldApplied' 0)
Link 0 'Out' 1;Link 1 'Out' 2
Add (Pause 10 (Guard));Add (New-ConditionNode 11 (Guard));Add (Variants 12 $true);Add (New-SetFactNode 13 'PTFRAL1_WorldApplied' 1)
Add (Pause 14 (Guard $true));Add (Variants 15 $false);Add (New-SetFactNode 16 'PTFRAL1_WorldApplied' 0)
Link 2 'Out' 10;Link 10 'Out' 11;Link 11 'False' 10;Link 11 'True' 12;foreach($i in 12..15){Link $i 'Out' ($i+1)};Link 16 'Out' 10
$index=0
foreach($row in $rows){
 $i=100+$index*20;$prefix=switch($row.role){'rogue'{'PTFRAL1_Rogue'}'emmerick'{'PTFRAL1_Emmerick'}default{'PTFRAL1_Population'}};$ready='PTFRAL1_Actor'+$index.ToString('00')+'Ready'
 Add (Pause $i (State $row));Add (New-ConditionNode ($i+1) (State $row));Add (Spawn ($i+2) $row $true);Add (Counter ($i+3) ($prefix+'Requests'));Add (New-SetFactNode ($i+4) $ready 1)
 Add (Pause ($i+5) (State $row $true));Add (Spawn ($i+6) $row $false);Add (Counter ($i+7) ($prefix+'Releases'));Add (New-SetFactNode ($i+8) $ready 0)
 Link 2 'Out' $i;Link $i 'Out' ($i+1);Link ($i+1) 'False' $i;Link ($i+1) 'True' ($i+2);foreach($j in 2..7){Link ($i+$j) 'Out' ($i+$j+1)};Link ($i+8) 'Out' $i
 $branches.Add([ordered]@{entry=$row.entry;phase=$row.phase;role=$row.role;start=$i;refs=@($row.refs);ready_fact=$ready;request_fact=($prefix+'Requests');release_fact=($prefix+'Releases');private_spawner=$row.private_spawner;original_type=$row.original_type;original_spawner=$row.original_spawner;original_entry=$row.original_entry;original_phase=$row.original_phase;availability=if($row.role -eq 'rogue'){@{rogue_default_on='>0';q116_rogue_dead='=0'}}else{@{}};acquire_actions=@('original Deactivate','private Reactivate');release_actions=@('private Deactivate')});$index++
}
$depot='towercontinued\afterlife_r1\population.questphase';Write-Cr2wFile $file (Join-Path $source $depot)
$phaseRead=Read-Cr2wFile (Join-Path $source $depot);Export-Cr2wJson $phaseRead (Join-Path $audit 'population_phase.json')
if($phaseRead.RootChunk.Graph.Chunk.Nodes.Count -ne 262 -or $phaseRead.RootChunk.PhasePrefabs.Count -ne 0 -or $phaseRead.EmbeddedFiles.Count -ne 0){throw 'Population controller scope/readback failed'}
$resources=[Collections.Generic.List[string]]::new();$payloads=[Collections.Generic.List[object]]::new();$resources.Add($depot)
foreach($bundle in @($rogue,$patrons,$dancers)){
 foreach($r in $bundle.resources){
  $from=Join-Path $bundle.source_root $r;$to=Join-Path $source $r
  if($r -notmatch '^towercontinued\\afterlife_r1\\' -or $resources.Contains($r)){throw 'Foreign or duplicate package resource'}
  $expected=if($bundle -eq $dancers){$dancers.sha256}else{@($bundle.hashes|Where-Object {$_.depot -eq $r})[0].sha256}
  if((Get-FileHash $from).Hash -ne $expected){throw "Source payload changed: $r"}
  New-Item -ItemType Directory -Force -Path (Split-Path $to)|Out-Null;Copy-Item -LiteralPath $from -Destination $to
  $resources.Add($r);$payloads.Add([ordered]@{depot=$r;source=$from;sha256=$expected})
 }
}
$payloads.Add([ordered]@{depot=$depot;source=(Join-Path $source $depot);sha256=(Get-FileHash (Join-Path $source $depot)).Hash})
$disk=@(Get-ChildItem -LiteralPath $source -File -Recurse|ForEach-Object {[IO.Path]::GetRelativePath($source,$_.FullName)})
if($resources.Count -ne 8 -or @(Compare-Object @($resources|Sort-Object) @($disk|Sort-Object)).Count){throw 'Source folder contains unexpected payloads'}
$archive=Join-Path $out 'TowerContinued_AfterlifeR1.archive'
$xl=@('streaming:','  blocks:',('    - '+$rogue.block_depot),('    - '+$patrons.block_depot),'quest:','  phases:',('    - path: '+$dancers.resources[0]),'      parent: ep1\quest\ep1.quest','      input:','        node: [1]','        socket: Out',('    - path: '+$depot),'      parent: ep1\quest\ep1.quest','      input:','        node: [1]','        socket: Out')
[IO.File]::WriteAllLines(($archive+'.xl'),$xl,[Text.UTF8Encoding]::new($false))
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Afterlife archive pack failed'}}finally{$stream.Dispose()}
$packed=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -ne 'NoError'){throw 'Afterlife archive reopen failed'}
if(@(Compare-Object @($resources|Sort-Object) @($packed.Files.Values|ForEach-Object {$_.Name}|Sort-Object)).Count){throw 'Packed resource scope mismatch'}
foreach($e in $packed.Files.Values){$ms=[IO.MemoryStream]::new();try{$e.Extract($ms);$ph=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($ms.ToArray()))}finally{$ms.Dispose()};if($ph -ne (Get-FileHash (Join-Path $source $e.Name)).Hash){throw 'Packed payload bytes differ'}}
$manifest=[ordered]@{status='BUILT_AFTERLIFE_R1_OFFLINE_LIVE_PENDING';source_root=$source;archive=$archive;sha256=(Get-FileHash $archive).Hash;xl_sha256=(Get-FileHash ($archive+'.xl')).Hash;resources=@($resources);payloads=@($payloads);world_blocks=@($rogue.block_depot,$patrons.block_depot);phases=@($dancers.resources[0],$depot);guards=$facts;population_phase=$depot;population_nodes=$graph.Nodes.Count;population_edges=@($edges);population_branches=@($branches);private_variants=$variants;world_branch=@{wait=10;recheck=11;enable=12;applied=13;stop_wait=14;disable=15;clear=16};registered_facts=@('PTFRAL1_DancersRegistered','PTFRAL1_PopulationRegistered');world_applied_fact='PTFRAL1_WorldApplied';dancers_manifest='research\afterlife_world\dancers_manifest.json';patrons_manifest='research\afterlife_world\patrons_manifest.json';rogue_manifest='research\afterlife_world\rogue_world_manifest.json';registration_parent='ep1\quest\ep1.quest';registration_node=@(1);registration_socket='Out';packed_readback_pass=$true;private_entries=$rows.Count;private_actors_max=([int]$patrons.maximum_actors+1);holographic_dancers=10;original_resource_overrides=0;story_writes=0;scene_starts=0;live_tested=$false}
[IO.File]::WriteAllText((Join-Path $audit 'manifest.json'),($manifest|ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false))
[pscustomobject]$manifest|Select-Object status,population_nodes,sha256,xl_sha256,packed_readback_pass|ConvertTo-Json
