param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\misty_viktor_world'
$out=Join-Path $WorkspaceRoot 'build\MistyViktorAccessR2'
$source=Join-Path $out 'source'
$prior=Get-Content (Join-Path $audit 'revision1\optin_manifest.json') -Raw|ConvertFrom-Json
New-Item -ItemType Directory -Force $source|Out-Null
foreach($path in $prior.resources){
  $src=Join-Path $WorkspaceRoot ('build\MistyViktorShellOptIn\source\'+$path)
  $dst=Join-Path $source $path
  New-Item -ItemType Directory -Force (Split-Path -Parent $dst)|Out-Null
  Copy-Item -LiteralPath $src -Destination $dst -Force
}
$depot='towercontinued\misty_viktor_world\shell_optin.questphase'
$file=Read-Cr2wFile (Join-Path $source $depot)
$g=$file.RootChunk.Graph.Chunk
$original=@($g.Nodes|ForEach-Object {$_.Chunk.DeepCopy()})
foreach($n in $original){foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()}}
$cleanup=Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\q307_extracted\raw\ep1\quest\main_quests\q307\phases\q307_cleanup.questphase')
$viktor=Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\q307_extracted\raw\ep1\quest\main_quests\q307\phases\q307_06_viktor.questphase')
$rear='$/03_night_city/c_watson/little_china/loc_mystic_mistys_ripperdoc_prefabH2DWJJI/#loc_mystic_mistys_ripperdoc_gameplay/single_door_1_prefab6TT3B7Y/#q115_misty_door_back'
$neon='$/03_night_city/c_watson/little_china/loc_mystic_mistys_ripperdoc_prefabH2DWJJI/#loc_mystic_mistys_ripperdoc_env/loc_mystic_mistys_ripperdoc_exterior_prefabIWBVVYQ/#mystic_mistys_exterior_001'
function Neon($id,[bool]$show){
  $n=(Get-QuestNode $script:cleanup.RootChunk.Graph.Chunk 22).DeepCopy();$n.Id=[uint16]$id
  foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()}
  $p=@($n.Type.Chunk.Params|Where-Object {$_.GetType().Name -eq 'questTogglePrefabVariant_NodeTypeParams' -and @($_.VariantStates|Where-Object {$_.Name.ToString() -eq 'neon_hide'}).Count})
  if($p.Count -ne 1 -or $p[0].VariantStates.Count -ne 1){throw 'Ambiguous neon precedent'}
  $single=$p[0].DeepCopy();$single.PrefabNodeRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($script:neon)
  $single.VariantStates[0].Show=$show;$n.Type.Chunk.Params.Clear();[void]$n.Type.Chunk.Params.Add($single)
  return $n
}
function Door($id,$sourceId,$action){
  $n=(Get-QuestNode $script:viktor.RootChunk.Graph.Chunk $sourceId).DeepCopy();$n.Id=[uint16]$id
  foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()}
  if($n.Type.Chunk.Params.Count -ne 1){throw 'Unexpected door action count'}
  $p=$n.Type.Chunk.Params[0].Chunk
  if($p.ObjectRef.ToString() -ne '#q115_misty_door_back' -or $p.DeviceControllerClass.ToString() -ne 'DoorControllerPS' -or $p.ActionProperties.Count -ne 0){throw 'Unexpected rear-door precedent'}
  $p.ObjectRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($script:rear)
  $p.DeviceAction=[WolvenKit.RED4.Types.CName]::op_Implicit($action)
  return $n
}
function Counter($id,$name){$n=New-SetFactNode $id $name 1;$n.Type.Chunk.SetExactValue=$false;return $n}
# Restore known q307 baseline ONLY during explicit opt-out in the same Tower
# sandbox. If ownership/suspension/ending guards invalidate, yield without
# writing vanilla door/sign state over the new owner. No synchronous lease claim.
$restore=$original[2].Condition.Chunk.DeepCopy()
$keep=@($restore.Conditions|Where-Object {$_.Chunk.Type.Chunk.FactName.ToString() -ne 'PTFRMV_Enabled'})
$restore.Conditions.Clear();foreach($c in $keep){[void]$restore.Conditions.Add($c)}
$g.Nodes.Clear();foreach($n in $original){Add-RedHandle $g.Nodes $n}
foreach($n in @((Neon 10 $false),(Door 11 20 'ForceUnlock'),(Counter 12 'PTFRMV_AccessRequests'),(New-ConditionNode 13 $restore),(Door 14 19 'ForceCloseImmediate'),(Door 15 20 'ForceLock'),(Neon 16 $true),(Counter 17 'PTFRMV_RestoreRequests'),(New-SetFactNode 18 'PTFRMV_Revision' 2))){Add-RedHandle $g.Nodes $n}
$edges=@(@(0,'Out',1),@(1,'Out',18),@(18,'Out',2),@(2,'Out',3),@(3,'Out',10),@(10,'Out',11),@(11,'Out',12),@(12,'Out',8),@(8,'Out',4),@(4,'Out',5),@(5,'Out',13),@(13,'True',14),@(14,'Out',15),@(15,'Out',16),@(16,'Out',17),@(17,'Out',6),@(13,'False',6),@(6,'Out',9),@(9,'Out',7),@(7,'Out',2))
foreach($e in $edges){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $e[0]) $e[1]) (Get-QuestSocket (Get-QuestNode $g $e[2]) 'In'))}
Write-Cr2wFile $file (Join-Path $source $depot)
Export-Cr2wJson (Read-Cr2wFile (Join-Path $source $depot)) (Join-Path $audit 'access_r2.json')
$hash=[WolvenKit.Common.Services.HashService]::new();$hash.Load()
$archive=Join-Path $out 'TowerContinued_MistyViktorShellOptIn.archive';$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hash,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hash,[ref]$packed).ToString() -ne 'NoError'){throw 'Archive reopen failed'}
if(@(Compare-Object @($prior.resources|Sort-Object) @($packed.Files.Values|ForEach-Object {$_.Name}|Sort-Object)).Count){throw 'Packed scope mismatch'}
Copy-Item -LiteralPath ($prior.archive+'.xl') -Destination ($archive+'.xl') -Force
$manifest=[ordered]@{status='BUILT_R2_OPTIN_NOT_INSTALLED_OR_LIVE';archive=$archive;sha256=(Get-FileHash $archive).Hash;xl_sha256=(Get-FileHash ($archive+'.xl')).Hash;resources=$prior.resources;guards=$prior.guards;registration_id=$prior.registration_id;rear_door=$rear;neon_owner=$neon;edges=$edges;geometry_changed=$false;story_fact_writes=0;live_tested=$false}
[IO.File]::WriteAllText((Join-Path $audit 'access_r2_manifest.json'),($manifest|ConvertTo-Json -Depth 6))
$manifest|Select-Object status,sha256,geometry_changed|ConvertTo-Json
