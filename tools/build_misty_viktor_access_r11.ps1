param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\misty_viktor_world'
$prior=Get-Content (Join-Path $audit 'access_r10_manifest.json') -Raw|ConvertFrom-Json
$doorWorld=Get-Content (Join-Path $audit 'r11_doors_manifest.json') -Raw|ConvertFrom-Json
$streetWorld=Get-Content (Join-Path $audit 'r11_street_world_manifest.json') -Raw|ConvertFrom-Json
$out=Join-Path $WorkspaceRoot 'build\MistyViktorAccessR11'
$source=Join-Path $out 'source'
New-Item -ItemType Directory -Force $source|Out-Null
$resources=[Collections.Generic.List[string]]::new()
foreach($depot in $prior.resources){
 $src=Join-Path $WorkspaceRoot ('build\MistyViktorAccessR10\source\'+$depot)
 $dst=Join-Path $source $depot
 New-Item -ItemType Directory -Force (Split-Path -Parent $dst)|Out-Null
 Copy-Item -LiteralPath $src -Destination $dst -Force;$resources.Add($depot)
}
foreach($worldPart in @($doorWorld,$streetWorld)){
 foreach($depot in $worldPart.resources){
  $src=Join-Path $worldPart.source_root $depot
  $dst=Join-Path $source $depot
  New-Item -ItemType Directory -Force (Split-Path -Parent $dst)|Out-Null
  Copy-Item -LiteralPath $src -Destination $dst -Force;$resources.Add($depot)
 }
}
$phaseDepot='towercontinued\misty_viktor_world\shell_optin.questphase'
$phase=Read-Cr2wFile (Join-Path $source $phaseDepot);$graph=$phase.RootChunk.Graph.Chunk
if($graph.Nodes.Count -ne 50){throw 'R10 controller changed'}
$viktor=Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\q307_extracted\raw\ep1\quest\main_quests\q307\phases\q307_06_viktor.questphase')
$pauseTemplate=(Get-QuestNode $graph 31).DeepCopy()
$inputTemplate=Join-Path $source $phaseDepot

# Retain old node IDs for saved-controller compatibility. The obsolete R10
# door branch is retired: no fresh fork and no outgoing edges from its nodes.
# A saved wait may finish, but cannot dispatch any further R10 door actions.
$oldBranch=31..43
foreach($node in $graph.Nodes){foreach($socket in $node.Chunk.Sockets){$socket.Chunk.Connections.Clear()}}
$mainEdges=@($prior.edges|Where-Object {$_[0] -notin $oldBranch -and $_[2] -notin $oldBranch})
foreach($e in $mainEdges){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $graph $e[0]) $e[1]) (Get-QuestSocket (Get-QuestNode $graph $e[2]) 'In'))}
(Get-QuestNode $graph 30).Type.Chunk.Value=[int32]11
$stop=(Get-QuestNode $graph 5).Condition.Chunk
$migration=@($stop.Conditions|Where-Object {$_.Chunk.Type.Chunk.FactName.ToString() -eq 'PTFRMV_AccessRevision'})
if($migration.Count -ne 1){throw 'R10 migration guard changed'}
$migration[0].Chunk.Type.Chunk.Value=[int32]11
$clerk=@((Get-QuestNode $viktor.RootChunk.Graph.Chunk 30).Actions|Where-Object {$_.Type.Chunk.CommunityEntryName.ToString() -eq 'q307_zetatech_clerk'})
if($clerk.Count -ne 1 -or $clerk[0].Type.Chunk.Action.ToString() -ne 'Reactivate' -or $clerk[0].Type.Chunk.SpawnerReference.ToString() -ne '#q307_com_main'){throw 'Clerk precedent changed'}
[void](Get-QuestNode $graph 44).Actions.Add($clerk[0].DeepCopy())
(Get-QuestNode $graph 45).Type.Chunk.FactName='PTFRMV_InteriorNPCRequests'
Write-Cr2wFile $phase (Join-Path $source $phaseDepot)
Export-Cr2wJson (Read-Cr2wFile (Join-Path $source $phaseDepot)) (Join-Path $audit 'access_r11_shell_phase.json')

# New registration gives access its own one-time startup, independent of
# saved R10 waits and the world owner's release/reacquire loop.
$file=Read-Cr2wFile $inputTemplate;$graph=$file.RootChunk.Graph.Chunk;$graph.Nodes.Clear()
$facts=[ordered]@{};foreach($p in $prior.guards.psobject.Properties){$facts[$p.Name]=[int]$p.Value}
$facts['PTFRMV_Applied']=1;$facts['PTFRMV_AccessRevision']=11
function Fact([string]$name,[int]$value,[bool]$inverse=$false){
 $cmp=if($inverse){[WolvenKit.RED4.Types.Enums+EComparisonType]::NotEqual}else{[WolvenKit.RED4.Types.Enums+EComparisonType]::Equal}
 return New-FactCondition $name $value $cmp
}
function Logic([string]$op,$children){
 $c=[WolvenKit.RED4.Types.questLogicalCondition]::new();$c.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::$op
 foreach($child in $children){Add-RedHandle $c.Conditions $child};return $c
}
function Guard([bool]$inverse=$false){
 $children=[Collections.Generic.List[object]]::new()
 foreach($key in $script:facts.Keys){$children.Add((Fact $key $script:facts[$key] $inverse))}
 return Logic $(if($inverse){'OR'}else{'AND'}) $children
}
function Loaded([string]$ref,[bool]$inverse=$false){
 $c=[WolvenKit.RED4.Types.questNodeLoadingCondition]::new();$c.ObjectRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($ref);$c.Inverted=$inverse;return $c
}
function LoadingGroup($refs,[bool]$inverse=$false){
 $parts=[Collections.Generic.List[object]]::new();foreach($ref in $refs){$parts.Add((Loaded $ref $inverse))}
 return Logic $(if($inverse){'OR'}else{'AND'}) $parts
}
function Pause([int]$id,$condition){
 $n=$script:pauseTemplate.DeepCopy();$n.Id=[uint16]$id;foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()};Set-RedHandleProperty $n Condition $condition;return $n
}
function Counter([int]$id,[string]$name){$n=New-SetFactNode $id $name 1;$n.Type.Chunk.SetExactValue=$false;return $n}
function Door([int]$id,[string]$ref,[string]$action){
 $n=(Get-QuestNode $script:viktor.RootChunk.Graph.Chunk 19).DeepCopy();$n.Id=[uint16]$id
 foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()}
 $p=$n.Type.Chunk.Params[0].Chunk
 if($p.DeviceControllerClass.ToString() -ne 'DoorControllerPS' -or $p.ActionProperties.Count){throw 'Door precedent changed'}
 $p.ObjectRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($ref);$p.DeviceAction=[WolvenKit.RED4.Types.CName]::op_Implicit($action);return $n
}
. (Join-Path $PSScriptRoot 'build_zetatech_street_entries_r11.ps1') -WorkspaceRoot $WorkspaceRoot
$street=Get-Content (Join-Path $audit 'street_entries_r11.json') -Raw|ConvertFrom-Json
$edges=[Collections.Generic.List[object]]::new()
function Add($node){Add-RedHandle $script:graph.Nodes $node;return [int]::Parse($node.Id.ToString())}
function Link([int]$from,[string]$socket,[int]$to){$script:edges.Add(@($from,$socket,$to));[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $script:graph $from) $socket) (Get-QuestSocket (Get-QuestNode $script:graph $to) 'In'))}
[void](Add (New-InputNode 0 'In1'));[void](Add (New-SetFactNode 1 'PTFRMV11_Registered' 1));Link 0 'Out' 1
$rear='$/03_night_city/c_watson/little_china/loc_mystic_mistys_ripperdoc_prefabH2DWJJI/#loc_mystic_mistys_ripperdoc_gameplay/single_door_1_prefab6TT3B7Y/#q115_misty_door_back'
$doorSpecs=@(
 @{name='Front';ref='$/03_night_city/#PTFRMV_ZetatechFrontDoor';start=10;close=$true},
 @{name='Inner';ref='$/03_night_city/#PTFRMV_ZetatechInnerDoor';start=30;close=$true},
 @{name='Rear';ref=$rear;start=50;close=$false}
)
foreach($d in $doorSpecs){
 $i=$d.start;$prefix='PTFRMV11_'+$d.name
 [void](Add (Pause $i (Logic 'AND' @((Guard),(Loaded $d.ref)))))
 [void](Add (New-ConditionNode ($i+1) (Logic 'AND' @((Guard),(Loaded $d.ref)))))
 [void](Add (Door ($i+2) $d.ref $(if($d.close){'ForceCloseImmediate'}else{'ForceUnlock'})))
 [void](Add (Door ($i+3) $d.ref 'ForceUnlock'))
 [void](Add (Counter ($i+4) ($prefix+'Requests')))
 [void](Add (New-SetFactNode ($i+5) ($prefix+'Ready') 1))
 [void](Add (Pause ($i+6) (Logic 'OR' @((Guard $true),(Loaded $d.ref $true)))))
 [void](Add (New-SetFactNode ($i+7) ($prefix+'Ready') 0))
 Link 1 'Out' $i;Link $i 'Out' ($i+1);Link ($i+1) 'False' $i
 if($d.close){Link ($i+1) 'True' ($i+2);Link ($i+2) 'Out' ($i+3)}else{Link ($i+1) 'True' ($i+3)}
 Link ($i+3) 'Out' ($i+4);Link ($i+4) 'Out' ($i+5);Link ($i+5) 'Out' ($i+6);Link ($i+6) 'Out' ($i+7);Link ($i+7) 'Out' $i
}
$spots=@($streetWorld.entries|ForEach-Object {$_.private_workspot_ref})
if($spots.Count -ne 4){throw 'Expected four independently audited pavement entries'}
[void](Add (Pause 70 (Logic 'AND' @((Guard),(LoadingGroup $spots)))))
[void](Add (New-ConditionNode 71 (Logic 'AND' @((Guard),(LoadingGroup $spots)))))
$activate=New-ZetatechStreetEntryNode 72 'Reactivate'
foreach($action in $activate.Actions){$action.Type.Chunk.SpawnerReference=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($streetWorld.private_spawner)}
[void](Add $activate)
[void](Add (Counter 73 'PTFRMV11_StreetRequests'))
[void](Add (New-SetFactNode 74 'PTFRMV11_StreetReady' 1))
[void](Add (Pause 75 (Logic 'OR' @((Guard $true),(LoadingGroup $spots $true)))))
$deactivate=New-ZetatechStreetEntryNode 76 'Deactivate'
foreach($action in $deactivate.Actions){$action.Type.Chunk.SpawnerReference=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($streetWorld.private_spawner)}
[void](Add $deactivate)
[void](Add (Counter 77 'PTFRMV11_StreetReleases'))
[void](Add (New-SetFactNode 78 'PTFRMV11_StreetReady' 0))
Link 1 'Out' 70;Link 70 'Out' 71;Link 71 'False' 70;Link 71 'True' 72
foreach($i in 72..77){Link $i 'Out' ($i+1)};Link 78 'Out' 70
$accessDepot='towercontinued\misty_viktor_world\access_r11.questphase'
Write-Cr2wFile $file (Join-Path $source $accessDepot);$resources.Add($accessDepot)
Export-Cr2wJson (Read-Cr2wFile (Join-Path $source $accessDepot)) (Join-Path $audit 'access_r11_phase.json')
$xl=Get-Content ($prior.archive+'.xl')
$anchor='    - towercontinued\misty_viktor_world\trucks_alley_r7.streamingblock'
$xl=@($xl|ForEach-Object {$_;if($_ -eq $anchor){'    - towercontinued\misty_viktor_world\doors_r11.streamingblock';'    - '+$streetWorld.block_depot}})
$xl+=@(('    - path: '+$accessDepot),'      parent: ep1\quest\ep1.quest','      input:','        node: [1]','        socket: Out')
$archive=Join-Path $out 'TowerContinued_MistyViktorShellOptIn.archive'
[IO.File]::WriteAllLines(($archive+'.xl'),$xl,[Text.UTF8Encoding]::new($false))
$hash=[WolvenKit.Common.Services.HashService]::new();$hash.Load();$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hash,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'R11 pack failed'}}finally{$stream.Dispose()}
$packed=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hash,[ref]$packed).ToString() -ne 'NoError'){throw 'R11 reopen failed'}
if(@(Compare-Object @($resources|Sort-Object) @($packed.Files.Values|ForEach-Object {$_.Name}|Sort-Object)).Count){throw 'R11 resource scope mismatch'}
foreach($entry in $packed.Files.Values){
 $memory=[IO.MemoryStream]::new()
 try{$entry.Extract($memory);$packedHash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($memory.ToArray()))}
 finally{$memory.Dispose()}
 if($packedHash -ne (Get-FileHash -LiteralPath (Join-Path $source $entry.Name)).Hash){throw ('R11 packed byte mismatch: '+$entry.Name)}
}
$manifest=[ordered]@{status='BUILT_R11_DOORS_STREET_COUNTERSTAFF_LIVE_PENDING';archive=$archive;sha256=(Get-FileHash $archive).Hash;xl_sha256=(Get-FileHash ($archive+'.xl')).Hash;resources=@($resources);guards=$facts;main_edges=$mainEdges;access_edges=@($edges);door_specs=$doorSpecs;access_revision=11;compatibility_revision=7;retired_r10_nodes=$oldBranch;street_entries=$street.entries;interior_entries=@('q307_alley_extra_01','q307_zetatech_clerk');original_world_overrides=0;story_writes=0;scene_starts=0;live_tested=$false}
$manifest['package_byte_readback_pass']=$true
$manifest['private_street_spawner']=$streetWorld.private_spawner
$manifest['private_street_spots']=$spots
[IO.File]::WriteAllText((Join-Path $audit 'access_r11_manifest.json'),($manifest|ConvertTo-Json -Depth 12),[Text.UTF8Encoding]::new($false))
[pscustomobject]$manifest|Select-Object status,sha256,xl_sha256,access_revision|ConvertTo-Json
