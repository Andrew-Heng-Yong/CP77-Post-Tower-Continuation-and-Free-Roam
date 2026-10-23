param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\misty_viktor_world'
$out=Join-Path $WorkspaceRoot 'build\MistyViktorShellOptIn'
$source=Join-Path $out 'source'
New-Item -ItemType Directory -Force -Path $out,$source|Out-Null
$tests=Get-Content -LiteralPath (Join-Path $audit 'shell_tests.json') -Raw|ConvertFrom-Json
$shell=Get-Content -LiteralPath (Join-Path $audit 'shell_manifest.json') -Raw|ConvertFrom-Json
if($tests.status -ne 'PASS_OFFLINE_INERT_GEOMETRY_ONLY_NOT_REGISTERED_INSTALLED_OR_LIVE_TESTED' -or $tests.archive_sha256 -ne $shell.sha256){throw 'Geometry tests absent/stale'}
$resources=[Collections.Generic.List[string]]::new()
foreach($path in $shell.resources){
  $src=Join-Path $WorkspaceRoot ('archive\misty_viktor_world\source\'+$path)
  $dst=Join-Path $source $path
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dst)|Out-Null
  Copy-Item -LiteralPath $src -Destination $dst -Force
  $resources.Add($path)
}
$foundation=Read-Cr2wFile (Join-Path $WorkspaceRoot 'archive\b0_ordinary_mirrors_c5_red_dirt\source\towercontinued\ordinary_mirrors_c5_red_dirt\m42_gate.questphase')
$cleanup=Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\q307_extracted\raw\ep1\quest\main_quests\q307\phases\q307_cleanup.questphase')
$options=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new()
$j=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize([WolvenKit.Common.Conversion.RedFileDto]::new($foundation,$false),$options)
$file=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Deserialize([WolvenKit.Common.Conversion.RedFileDto],$j,$options).Data
if($file.RootChunk.PhasePrefabs.Count -ne 0){throw 'Unexpected prefab acquisition'}
$pauseTemplate=(Get-QuestNode $file.RootChunk.Graph.Chunk 1).DeepCopy()
$toggleTemplate=(Get-QuestNode $cleanup.RootChunk.Graph.Chunk 22).DeepCopy()
$params=@($toggleTemplate.Type.Chunk.Params|Where-Object {$_.GetType().Name -eq 'questTogglePrefabVariant_NodeTypeParams' -and @($_.VariantStates|Where-Object {$_.Name.ToString() -eq 'q307_zetatech'}).Count})
if($params.Count -ne 1){throw 'Vanilla toggle precedent not unique'}
$single=$params[0].DeepCopy()
if($single.VariantStates.Count -ne 1){throw 'Unexpected multi-state precedent'}
$single.PrefabNodeRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($shell.variant_owner)
$single.VariantStates[0].Name=[WolvenKit.RED4.Types.CName]::op_Implicit($shell.private_variant)
$toggleTemplate.Type.Chunk.Params.Clear();[void]$toggleTemplate.Type.Chunk.Params.Add($single)
$facts=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;q307_active=0;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;q305_johnny_scene_active=0;q115_point_of_no_return=0;PTFRBASE_Suspended=0;PTFRWORLD_Suspended=0;PTFRMV_Enabled=1;PTFRMV_Suspended=0;PTFRMV_QuestOwns=0}
function Condition([bool]$inverse){
  $condition=[WolvenKit.RED4.Types.questLogicalCondition]::new()
  $condition.Operation=if($inverse){[WolvenKit.RED4.Types.Enums+questLogicalOperation]::OR}else{[WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND}
  $comparison=if($inverse){[WolvenKit.RED4.Types.Enums+EComparisonType]::NotEqual}else{[WolvenKit.RED4.Types.Enums+EComparisonType]::Equal}
  foreach($name in $script:facts.Keys){Add-RedHandle $condition.Conditions (New-FactCondition $name $script:facts[$name] $comparison)}
  return $condition
}
function Pause($id,$condition){$node=$script:pauseTemplate.DeepCopy();$node.Id=[uint16]$id;foreach($socket in $node.Sockets){$socket.Chunk.Connections.Clear()};Set-RedHandleProperty $node Condition $condition;return $node}
function Toggle($id,[bool]$visible){$node=$script:toggleTemplate.DeepCopy();$node.Id=[uint16]$id;foreach($socket in $node.Sockets){$socket.Chunk.Connections.Clear()};$node.Type.Chunk.Params[0].VariantStates[0].Show=$visible;return $node}
function Counter($id,$name){$node=New-SetFactNode $id $name 1;$node.Type.Chunk.SetExactValue=$false;return $node}
$g=$file.RootChunk.Graph.Chunk;$g.Nodes.Clear()
foreach($node in @((New-InputNode 0 'In1'),(New-SetFactNode 1 'PTFRMV_Registered' 1),(Pause 2 (Condition $false)),(Toggle 3 $true),(New-SetFactNode 4 'PTFRMV_Applied' 1),(Pause 5 (Condition $true)),(Toggle 6 $false),(New-SetFactNode 7 'PTFRMV_Applied' 0),(Counter 8 'PTFRMV_Acquires'),(Counter 9 'PTFRMV_Releases'))){Add-RedHandle $g.Nodes $node}
foreach($edge in @(@(0,1),@(1,2),@(2,3),@(3,8),@(8,4),@(4,5),@(5,6),@(6,9),@(9,7),@(7,2))){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $edge[0]) 'Out') (Get-QuestSocket (Get-QuestNode $g $edge[1]) 'In'))}
$depot='towercontinued\misty_viktor_world\shell_optin.questphase'
Write-Cr2wFile $file (Join-Path $source $depot)
Export-Cr2wJson (Read-Cr2wFile (Join-Path $source $depot)) (Join-Path $audit 'shell_optin.json')
$resources.Add($depot)
$crc=65535;foreach($byte in [Text.Encoding]::UTF8.GetBytes($depot+':1')){$x=($crc -shr 8) -bxor $byte;$x=$x -bxor ($x -shr 4);$crc=(($crc -shl 8) -bxor ($x -shl 12) -bxor ($x -shl 5) -bxor $x) -band 65535}
$parent=Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\q307_extracted\raw\ep1\quest\ep1.quest')
if(@($parent.RootChunk.Graph.Chunk.Nodes|Where-Object {$_.Chunk.Id.ToString() -eq "$crc"}).Count){throw 'Parent registration ID collision'}
$xl=@('streaming:','  blocks:','    - towercontinued\misty_viktor_world\shell.streamingblock','quest:','  phases:',"    - path: $depot",'      parent: ep1\quest\ep1.quest','      input:','        node: [1]','        socket: Out')
$hash=[WolvenKit.Common.Services.HashService]::new();$hash.Load()
$archive=Join-Path $out 'TowerContinued_MistyViktorShellOptIn.archive';$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hash,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
[IO.File]::WriteAllLines(($archive+'.xl'),$xl,[Text.UTF8Encoding]::new($false))
$manifest=[ordered]@{status='BUILT_OPTIN_GEOMETRY_CANDIDATE_NOT_INSTALLED';archive=$archive;sha256=(Get-FileHash $archive).Hash;xl_sha256=(Get-FileHash ($archive+'.xl')).Hash;resources=@($resources);registration_id=$crc;guards=$facts;private_variant=$shell.private_variant;variant_owner=$shell.variant_owner;native_scene_starts=0;story_fact_writes=0;vanilla_replacements=@();live_tested=$false}
[IO.File]::WriteAllText((Join-Path $audit 'optin_manifest.json'),($manifest|ConvertTo-Json -Depth 5))
$manifest|ConvertTo-Json -Depth 3
