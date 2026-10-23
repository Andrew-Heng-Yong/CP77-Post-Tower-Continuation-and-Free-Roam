param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\misty_viktor_world'
$world=Get-Content (Join-Path $audit 'population_r12_world_manifest.json') -Raw|ConvertFrom-Json
$prior=Get-Content (Join-Path $audit 'access_r11_manifest.json') -Raw|ConvertFrom-Json
$file=Read-Cr2wFile (Join-Path $WorkspaceRoot 'build\MistyViktorAccessR11\source\towercontinued\misty_viktor_world\access_r11.questphase')
$graph=$file.RootChunk.Graph.Chunk;$pauseTemplate=(Get-QuestNode $graph 70).DeepCopy();$graph.Nodes.Clear()
$vanilla=Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\q307_extracted\raw\ep1\quest\main_quests\q307\phases\q307_06_viktor.questphase')
$spawnTemplate=(Get-QuestNode $vanilla.RootChunk.Graph.Chunk 30).DeepCopy()
$entryTemplate=@($spawnTemplate.Actions|Where-Object {$_.Type.Chunk.GetType().Name -eq 'questCommunityTemplate_NodeType' -and $_.Type.Chunk.CommunityEntryName.ToString() -eq 'q307_alley_extra_01'})[0].DeepCopy()
$facts=[ordered]@{};foreach($p in $prior.guards.psobject.Properties){$facts[$p.Name]=[int]$p.Value}
function Logic([string]$op,$children){$c=[WolvenKit.RED4.Types.questLogicalCondition]::new();$c.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::$op;foreach($child in $children){Add-RedHandle $c.Conditions $child};return $c}
function Guard([bool]$inverse=$false){$children=[Collections.Generic.List[object]]::new();foreach($key in $script:facts.Keys){$children.Add((New-FactCondition $key $script:facts[$key] $(if($inverse){[WolvenKit.RED4.Types.Enums+EComparisonType]::NotEqual}else{[WolvenKit.RED4.Types.Enums+EComparisonType]::Equal})))};return Logic $(if($inverse){'OR'}else{'AND'}) $children}
function Loaded([string]$ref,[bool]$inverse=$false){$c=[WolvenKit.RED4.Types.questNodeLoadingCondition]::new();$c.ObjectRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($ref);$c.Inverted=$inverse;return $c}
function State($refs,[bool]$inverse=$false){$parts=[Collections.Generic.List[object]]::new();$parts.Add((Guard $inverse));foreach($ref in $refs){$parts.Add((Loaded $ref $inverse))};return Logic $(if($inverse){'OR'}else{'AND'}) $parts}
function Pause([int]$id,$condition){$n=$script:pauseTemplate.DeepCopy();$n.Id=[uint16]$id;foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()};Set-RedHandleProperty $n Condition $condition;return $n}
function Counter([int]$id,[string]$name){$n=New-SetFactNode $id $name 1;$n.Type.Chunk.SetExactValue=$false;return $n}
function Spawn([int]$id,[string]$action,$rows,[bool]$original=$false){
 $n=$script:spawnTemplate.DeepCopy();$n.Id=[uint16]$id;foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()};$n.Actions.Clear()
 foreach($row in $rows){$a=$script:entryTemplate.DeepCopy();$a.Type.Chunk.Action=[WolvenKit.RED4.Types.Enums+populationSpawnerObjectCtrlAction]::$action;$a.Type.Chunk.CommunityEntryName=[WolvenKit.RED4.Types.CName]::op_Implicit($row.entry);$a.Type.Chunk.CommunityEntryPhaseName=[WolvenKit.RED4.Types.CName]::op_Implicit($row.phase)
 $ref=if($original){if($row.role -eq 'guard'){'#q307_com_alley'}else{'#q307_com_main'}}else{$script:world.spawner}
 $a.Type.Chunk.SpawnerReference=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($ref);[void]$n.Actions.Add($a)};return $n
}
$edges=[Collections.Generic.List[object]]::new()
function Add($node){Add-RedHandle $script:graph.Nodes $node}
function Link([int]$from,[string]$socket,[int]$to){$script:edges.Add(@($from,$socket,$to));[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $script:graph $from) $socket) (Get-QuestSocket (Get-QuestNode $script:graph $to) 'In'))}
Add (New-InputNode 0 'In1');Add (New-SetFactNode 1 'PTFRMV12_Registered' 1);Link 0 'Out' 1
# Per-entry readiness avoids one missing workspot blocking other residents.
$branches=[Collections.Generic.List[object]]::new();$i=10
foreach($row in $world.entries){
 $refs=@($row.spot.ref);if($row.entry -eq 'q307_alley_extra_23'){$refs+= '$/03_night_city/#PTFRMV12_Wheelchair'}
 Add (Pause $i (State $refs));Add (New-ConditionNode ($i+1) (State $refs))
 Add (Spawn ($i+2) 'Reactivate' @($row));Add (Counter ($i+3) 'PTFRMV12_PopulationRequests')
 Add (Pause ($i+4) (State $refs $true));Add (Spawn ($i+5) 'Deactivate' @($row));Add (Counter ($i+6) 'PTFRMV12_PopulationReleases')
 Link 1 'Out' $i;Link $i 'Out' ($i+1);Link ($i+1) 'False' $i
 if($row.role -in @('guard','clerk')){Add (Spawn ($i+7) 'Deactivate' @($row) $true);Link ($i+1) 'True' ($i+7);Link ($i+7) 'Out' ($i+2)}else{Link ($i+1) 'True' ($i+2)}
 foreach($n in ($i+2)..($i+5)){Link $n 'Out' ($n+1)};Link ($i+6) 'Out' $i
 $branches.Add(@{entry=$row.entry;start=$i;refs=$refs;replaces_original=($row.role -in @('guard','clerk'))});$i+=10
}
Add (Pause 400 (State @($world.terry_spot.ref)));Add (New-ConditionNode 401 (State @($world.terry_spot.ref)))
Add (New-SetFactNode 402 'PTFRMV12_TerrySpotReady' 1);Add (Pause 403 (State @($world.terry_spot.ref) $true));Add (New-SetFactNode 404 'PTFRMV12_TerrySpotReady' 0)
Link 1 'Out' 400;Link 400 'Out' 401;Link 401 'False' 400;Link 401 'True' 402;Link 402 'Out' 403;Link 403 'Out' 404;Link 404 'Out' 400
$depot='towercontinued\zetatech_population_r12\population.questphase';Write-Cr2wFile $file (Join-Path $world.source $depot)
Export-Cr2wJson (Read-Cr2wFile (Join-Path $world.source $depot)) (Join-Path $audit 'r12_population_phase.json')
$resources=@($world.resources)+@($depot)
$archive=Join-Path (Split-Path -Parent $world.source) 'TowerContinued_ZetatechPopulationR12.archive'
$xl=@('streaming:','  blocks:',('    - '+$world.resources[2]),'quest:','  phases:',('    - path: '+$depot),'      parent: ep1\quest\ep1.quest','      input:','        node: [1]','        socket: Out')
[IO.File]::WriteAllLines(($archive+'.xl'),$xl,[Text.UTF8Encoding]::new($false))
$hash=[WolvenKit.Common.Services.HashService]::new();$hash.Load();$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hash,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($world.source),$stream)){throw 'R12 pack failed'}}finally{$stream.Dispose()}
$packed=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hash,[ref]$packed).ToString() -ne 'NoError'){throw 'R12 reopen failed'}
if(@(Compare-Object @($resources|Sort-Object) @($packed.Files.Values|ForEach-Object {$_.Name}|Sort-Object)).Count){throw 'R12 resource scope mismatch'}
foreach($entry in $packed.Files.Values){$memory=[IO.MemoryStream]::new();try{$entry.Extract($memory);$ph=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($memory.ToArray()))}finally{$memory.Dispose()};if($ph -ne (Get-FileHash (Join-Path $world.source $entry.Name)).Hash){throw 'Packed byte mismatch'}}
$manifest=[ordered]@{status='BUILT_R12_POPULATION_LIVE_PENDING';archive=$archive;sha256=(Get-FileHash $archive).Hash;xl_sha256=(Get-FileHash ($archive+'.xl')).Hash;resources=$resources;edges=@($edges);branches=@($branches);guards=$facts;nodes=$graph.Nodes.Count;packed_readback_pass=$true;original_deactivations=@('q307_alley_extra_01','q307_zetatech_clerk');r11_files_modified=0;story_writes=0;scene_starts=0;live_tested=$false}
[IO.File]::WriteAllText((Join-Path $audit 'population_r12_manifest.json'),($manifest|ConvertTo-Json -Depth 15),[Text.UTF8Encoding]::new($false))
[pscustomobject]$manifest|Select-Object status,nodes,sha256,xl_sha256|ConvertTo-Json
