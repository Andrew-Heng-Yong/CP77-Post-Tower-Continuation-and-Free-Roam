param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$research=Join-Path $WorkspaceRoot 'research\b0_story_zane'
$audit=Get-Content (Join-Path $research 'audit.json') -Raw|ConvertFrom-Json
$source=Join-Path $WorkspaceRoot 'archive\b0_story_zane\source'
$out=Join-Path $WorkspaceRoot 'build\B0_StoryZane'
$val=Join-Path $research 'validation'
New-Item -ItemType Directory -Force -Path $source,$out,$val|Out-Null
foreach($kind in @('owner','scene')){if((Get-FileHash (Join-Path $WorkspaceRoot $audit.$kind)).Hash -ne $audit.($kind+'_sha256')){throw 'Audit source changed'}}
$ownerRaw=Join-Path $WorkspaceRoot 'research\phase2b_p4\vendor_owner\raw\base\quest\default_dialogs.questphase'
$sceneRaw=Join-Path $WorkspaceRoot 'research\b0_vendor_rollout\special_scene_sources\raw\base\open_world\vendors\city_center\downtown\cct_dtn_cloth_01\cct_dtn_cloth_01.scene'
$vendor=Read-Cr2wFile $ownerRaw
$base=Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\q307_extracted\raw\base\quest\cyberpunk2077.questphase')
$prefix='PTFRB0ZAN_'
$sceneDepot='towercontinued\b0_story_zane\zane_service.scene'
$depot='towercontinued\b0_story_zane\zane_service.questphase'
function ClearSockets($n){foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()}}
function Link($g,$from,$socket,$to,$dest='In'){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $from) $socket) (Get-QuestSocket (Get-QuestNode $g $to) $dest))}
function Inc($id,$suffix){$n=New-SetFactNode $id ($prefix+$suffix) 1;$n.Type.Chunk.SetExactValue=$false;return $n}
function Eq($name,$value){return New-FactCondition $name $value ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal)}
function Pause($id,$condition){$n=(Get-QuestNode $base.RootChunk.Graph.Chunk 106).DeepCopy();$n.Id=[uint16]$id;ClearSockets $n;Set-RedHandleProperty $n Condition $condition;return $n}
function And(){ $c=[WolvenKit.RED4.Types.questLogicalCondition]::new();$c.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND;return $c }
# Preserve authored choices, audio, animations and earned discount. The copied
# service must not consume Bullets' first-meeting progression event.
$scene=Read-Cr2wFile $sceneRaw
$sn=@($scene.RootChunk.SceneGraph.Chunk.Graph|Where-Object {$_.Chunk.NodeId.Id.ToString() -eq '43'})
if($sn.Count -ne 1 -or $sn[0].Chunk.QuestNode.Chunk.Type.Chunk.FactName.ToString() -ne 'mq030_zane_met'){throw 'Scene writer drift'}
$sn[0].Chunk.QuestNode.Chunk.Type.Chunk.FactName=$prefix+'ServiceMet'
Write-Cr2wFile $scene (Join-Path $source $sceneDepot)
Export-Cr2wJson (Read-Cr2wFile (Join-Path $source $sceneDepot)) (Join-Path $val 'zane_service.scene.json')
$phase=(Get-QuestNode (Get-QuestNode $vendor.RootChunk.Graph.Chunk 7).PhaseGraph.Chunk 25).DeepCopy()
$phase.Id=[uint16]5;ClearSockets $phase
$outer=$phase.PhaseGraph.Chunk;$inner=(Get-QuestNode $outer 2).PhaseGraph.Chunk
# Handover only after native departure/despawn returns and player is outside.
# A pending quest lease also blocks fresh shop activation. Future quest code
# must wait for Released=1/OwnerActive=0 before creating any competing owner.
Add-RedHandle $outer.Nodes (New-ConditionNode 200 (Eq ($prefix+'QuestOwns') 0))
Add-RedHandle $outer.Nodes (New-SetFactNode 201 ($prefix+'Inside') 1)
Add-RedHandle $outer.Nodes (New-SetFactNode 202 ($prefix+'Inside') 0)
$release=And
Add-RedHandle $release.Conditions (Eq ($prefix+'QuestOwns') 1)
Add-RedHandle $release.Conditions (Eq ($prefix+'Inside') 0)
Add-RedHandle $release.Conditions (Get-QuestNode $inner 9).Condition.Chunk.DeepCopy()
Add-RedHandle $outer.Nodes (Pause 203 $release)
Add-RedHandle $outer.Nodes (Inc 204 'Entries')
Add-RedHandle $outer.Nodes (Inc 205 'Exits')
Add-RedHandle $inner.Nodes (Inc 200 'SceneRequests')
foreach($pair in @(@($outer,'root/node7/node25'),@($inner,'root/node7/node25/node2'))){
 $g=$pair[0];$route=$pair[1]
 foreach($h in $g.Nodes){ClearSockets $h.Chunk}
 foreach($e in $audit.graphs.$route.edges){
  $to=$e.destination_node_id;$dest=$e.destination_socket
  if($route -eq 'root/node7/node25'){
   if($e.source_node_id -eq 4){$to=200;$dest='In'}
   if($e.source_node_id -eq 2){$to=202;$dest='In'}
  }elseif($e.source_node_id -eq 13){$to=200;$dest='In'}
  Link $g $e.source_node_id $e.source_socket $to $dest
 }
}
Link $outer 0 Out 203
Link $outer 200 True 201;Link $outer 201 Out 204;Link $outer 204 Out 2 main_in
Link $outer 202 Out 205;Link $outer 205 Out 4
Link $outer 203 Out 5 Inactive
Link $inner 200 Out 3 cct_dtn_cloth_01_start
$sceneNode=Get-QuestNode $inner 3
$resourcePath=[WolvenKit.RED4.Types.ResourcePath]::op_Implicit($sceneDepot)
$sceneNode.SceneFile=[Activator]::CreateInstance($sceneNode.GetType().GetProperty('SceneFile').PropertyType,[object[]]@($resourcePath))
$guard=And
foreach($f in $audit.common_guards.PSObject.Properties){Add-RedHandle $guard.Conditions (Eq $f.Name $f.Value)}
foreach($f in @('PTFRBASE_Suspended',($prefix+'Suspended'),($prefix+'Excluded'),($prefix+'QuestOwns'))){Add-RedHandle $guard.Conditions (Eq $f 0)}
Add-RedHandle $guard.Conditions (Eq ($prefix+'Enabled') 1)
Add-RedHandle $guard.Conditions (New-FactCondition 'cct_dtn_cloth_01_default_on' 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Greater))
$g=[WolvenKit.RED4.Types.questGraphDefinition]::new()
foreach($n in @((New-InputNode 0 'In1'),(New-SetFactNode 1 ($prefix+'Ready') 1),(Pause 2 $guard),(New-SetFactNode 3 ($prefix+'OwnerActive') 1),(Inc 4 'OwnerStarts'),$phase,(New-SetFactNode 6 ($prefix+'OwnerActive') 0),(New-SetFactNode 7 ($prefix+'Released') 1),(New-SetFactNode 8 ($prefix+'Released') 0),(New-SetFactNode 9 ($prefix+'Inside') 0))){Add-RedHandle $g.Nodes $n}
foreach($e in @(@(0,'Out',1,'In'),@(1,'Out',2,'In'),@(2,'Out',3,'In'),@(3,'Out',8,'In'),@(8,'Out',4,'In'),@(4,'Out',5,'In1'),@(5,'Out1',6,'In'),@(6,'Out',9,'In'),@(9,'Out',7,'In'),@(7,'Out',2,'In'))){Link $g $e[0] $e[1] $e[2] $e[3]}
$root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();$root.CookingPlatform=[WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC;Set-RedHandleProperty $root Graph $g
$resource=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$resource.RootChunk=$root
Write-Cr2wFile $resource (Join-Path $source $depot)
Export-Cr2wJson (Read-Cr2wFile (Join-Path $source $depot)) (Join-Path $val 'zane_service.questphase.json')
if(@(Get-ChildItem $source -Recurse -File).Count -ne 2){throw 'Scope drift'}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$archive=Join-Path $out 'TowerContinued_B0_StoryZane.archive';$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -ne 'NoError' -or $packed.Files.Count -ne 2){throw 'Readback failed'}
foreach($e in $packed.Files.Values){$m=[IO.MemoryStream]::new();try{$e.Extract($m);if($e.Name -notin @($depot,$sceneDepot) -or [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($m.ToArray())) -ne (Get-FileHash (Join-Path $source $e.Name)).Hash){throw 'Packed bytes differ'}}finally{$m.Dispose()}}
$xl=@('quest:','  phases:',"    - path: $depot",'      parent: ep1\quest\ep1.quest','      input:','        node: [1]','        socket: Out') -join "`n"
[IO.File]::WriteAllText((Join-Path $WorkspaceRoot 'archive\b0_story_zane\TowerContinued_B0_StoryZane.archive.xl'),$xl+"`n")
$report=@{status='BUILT_NOT_INSTALLED';archive_sha256=(Get-FileHash $archive).Hash;resources=@($depot,$sceneDepot);audit_sha256=(Get-FileHash (Join-Path $research 'audit.json')).Hash;owner_raw_sha256=(Get-FileHash $ownerRaw).Hash;scene_raw_sha256=(Get-FileHash $sceneRaw).Hash;vanilla_replacements=@();live='NOT_TESTED'}
[IO.File]::WriteAllText((Join-Path $val 'build_manifest.json'),($report|ConvertTo-Json -Depth 6))
'BUILT: Zane service adapter and cooperative quest handover; no vanilla replacements'
