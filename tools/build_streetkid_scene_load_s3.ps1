param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),
      [string]$WolvenKitRoot='C:\Users\Ayong\Documents\WolvenKit-8.20.0')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -WolvenKitRoot $WolvenKitRoot -HelpersOnly
. (Join-Path $PSScriptRoot 'streetkid_scene_identity.ps1')
$prior=Join-Path $WorkspaceRoot 'archive\b0_streetkid_seat_mirror_s2\source\towercontinued\streetkid_seat_mirror_s2'
$source=Join-Path $WorkspaceRoot 'archive\b0_streetkid_scene_load_s3\source'
$build=Join-Path $WorkspaceRoot 'build\Streetkid_Scene_Load_S3'
$audit=Join-Path $WorkspaceRoot 'research\b0_streetkid_scene_load_s3'
$prefix='towercontinued\streetkid_scene_load_s3'
$sceneDepot="$prefix\load.scene"
$ownerDepot="$prefix\owner.questphase"
$gateDepot="$prefix\gate.questphase"
$archiveName='TowerContinued_Streetkid_Scene_Load_S3.archive'
$repairManifest=Get-Content (Join-Path $WorkspaceRoot 'research\b0_streetkid_seat_mirror_s2\build_manifest.json') -Raw|ConvertFrom-Json
if ($repairManifest.status -notin @('WORKSPACE_REPAIR_UNVALIDATED_NOT_FOR_INSTALL','ACTION_TEST_BUILT_AFTER_S3_PASS') -or -not $repairManifest.repaired_metadata -or -not $repairManifest.crash_actor_index_fixed) { throw 'Actor-index repair contract not present' }
New-Item -ItemType Directory -Force -Path $source,$build,$audit|Out-Null
$scene=Read-Cr2wFile (Join-Path $prior 'seat_mirror.scene')
$root=$scene.RootChunk
$g=$root.SceneGraph.Chunk.Graph
function Find([int]$id) {
  $n=@($g|Where-Object {$_.Chunk.NodeId.Id.ToString() -eq $id.ToString()})
  if($n.Count -ne 1){throw "Scene node $id missing"}; return $n[0].Chunk
}
$start=(Find 1).DeepCopy(); $section=(Find 8).DeepCopy(); $end=(Find 2000).DeepCopy()
$g.Clear()
$start.OutputSockets[0].Destinations[0].NodeId.Id=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]8)
$section.OutputSockets[0].Destinations[0].NodeId.Id=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]2000)
for($i=1;$i -lt $section.OutputSockets.Count;$i++){$section.OutputSockets[$i].Destinations.Clear()}
$section.SectionDuration.Stu=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]2000)
$section.Events.Clear()
Add-RedHandle $g $start; Add-RedHandle $g $section; Add-RedHandle $g $end
$root.Workspots.Clear();$root.WorkspotInstances.Clear()
$root.ScreenplayStore.Lines.Clear();$root.ScreenplayStore.Options.Clear()
$root.LocStore.VdEntries.Clear();$root.LocStore.VpEntries.Clear()
$root.NotablePoints.Clear();$root.InterruptionScenarios.Clear()
$root.ResouresReferences.GameplayAnimNames.Clear();$root.ResouresReferences.GameplayAnimSets.Clear()
foreach($actor in $root.Actors){
  $old=$actor.SpawnDespawnParams.DynamicEntityUniqueName.ToString()
  $actor.SpawnDespawnParams.DynamicEntityUniqueName=[WolvenKit.RED4.Types.CName]::op_Implicit($old.Replace('PTFRSKS2','PTFRSKS3'))
}
foreach($symbol in $root.DebugSymbols.PerformersDebugSymbols){
  $old=$symbol.EntityRef.DynamicEntityUniqueName.ToString()
  if($old.Contains('PTFRSKS2')){$symbol.EntityRef.DynamicEntityUniqueName=[WolvenKit.RED4.Types.CName]::op_Implicit($old.Replace('PTFRSKS2','PTFRSKS3'))}
}
$root.DebugSymbols=[Activator]::CreateInstance($root.DebugSymbols.GetType())
$identityRepair=Repair-StreetkidSceneIdentity $scene
$scene=$identityRepair.File
$root=$scene.RootChunk
Write-Cr2wFile $scene (Join-Path $source $sceneDepot)
$gate=Read-Cr2wFile (Join-Path $prior 'gate.questphase')
$owner=Read-Cr2wFile (Join-Path $prior 'owner.questphase')
# S2 excludes S3 while actions run. Do not carry those exclusions into S3's
# own enable guard when reproducing the already-tested acquisition probe.
$inheritedGuard=(Get-QuestNode $gate.RootChunk.Graph.Chunk 2).Condition.Chunk.Conditions
for($i=$inheritedGuard.Count-1;$i -ge 0;$i--) {
  if($inheritedGuard[$i].Chunk.Type.Chunk.FactName.ToString() -in 'PTFRSKS3_Enabled','PTFRSKS3_Active') { $inheritedGuard.RemoveAt($i) }
}
foreach($file in $gate,$owner){
  foreach($handle in $file.RootChunk.Graph.Chunk.Nodes){
    $n=$handle.Chunk
    switch($n.GetType().Name){
      'questFactsDBManagerNodeDefinition' {
        $fact=$n.Type.Chunk.FactName.ToString()
        if(-not $fact.StartsWith('PTFRSKS2_')){throw "Unexpected writer $fact"}
        $n.Type.Chunk.FactName=[WolvenKit.RED4.Types.CString]::op_Implicit($fact.Replace('PTFRSKS2_','PTFRSKS3_'))
      }
      'questPauseConditionNodeDefinition' {
        foreach($c in $n.Condition.Chunk.Conditions){
          $fact=$c.Chunk.Type.Chunk.FactName.ToString()
          if($fact.StartsWith('PTFRSKS2_')){$c.Chunk.Type.Chunk.FactName=[WolvenKit.RED4.Types.CString]::op_Implicit($fact.Replace('PTFRSKS2_','PTFRSKS3_'))}
        }
      }
      'questPhaseNodeDefinition' {
        $path=[WolvenKit.RED4.Types.ResourcePath]::op_Implicit($ownerDepot)
        $n.PhaseResource=[Activator]::CreateInstance($n.GetType().GetProperty('PhaseResource').PropertyType,[object[]]@($path))
      }
      'questSceneNodeDefinition' {
        $path=[WolvenKit.RED4.Types.ResourcePath]::op_Implicit($sceneDepot)
        $n.SceneFile=[Activator]::CreateInstance($n.GetType().GetProperty('SceneFile').PropertyType,[object[]]@($path))
      }
    }
  }
}
Add-RedHandle (Get-QuestNode $gate.RootChunk.Graph.Chunk 2).Condition.Chunk.Conditions (New-FactCondition 'PTFRSKS2_Enabled' 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
# A native revision stamp lets CET refuse a stale/mismatched archive.
$gateGraph=$gate.RootChunk.Graph.Chunk
if(-not @($gateGraph.Nodes|Where-Object {$_.Chunk.Id.ToString() -eq '9'}).Count) {
  $revision=New-SetFactNode 9 'PTFRSKS3_Revision' 2
  Add-RedHandle $gateGraph.Nodes $revision
  $input=Get-QuestSocket (Get-QuestNode $gateGraph 0) 'Out'
  $boot=Get-QuestSocket (Get-QuestNode $gateGraph 1) 'In'
  $input.Connections.Clear();$boot.Connections.Clear()
  [void](Connect-QuestSockets $input (Get-QuestSocket $revision 'In'))
  [void](Connect-QuestSockets (Get-QuestSocket $revision 'Out') $boot)
}
Write-Cr2wFile $gate (Join-Path $source $gateDepot)
Write-Cr2wFile $owner (Join-Path $source $ownerDepot)
foreach($item in @(@{name='scene';depot=$sceneDepot},@{name='gate';depot=$gateDepot},@{name='owner';depot=$ownerDepot})){
  $file=Read-Cr2wFile (Join-Path $source $item.depot)
  Export-Cr2wJson $file (Join-Path $audit ($item.name+'.json'))
}
$check=Read-Cr2wFile (Join-Path $source $sceneDepot)
if($check.RootChunk.SceneGraph.Chunk.Graph.Count -ne 3 -or $check.RootChunk.Workspots.Count -ne 0 -or
  $check.RootChunk.WorkspotInstances.Count -ne 0 -or $check.RootChunk.Props.Count -ne 0 -or
  $check.RootChunk.ScreenplayStore.Options.Count -ne 0){throw 'S3 action-free scope changed'}
$expected=@($sceneDepot,$gateDepot,$ownerDepot)|Sort-Object
$actual=@(Get-ChildItem -LiteralPath $source -Recurse -File|ForEach-Object{[IO.Path]::GetRelativePath($source,$_.FullName)}|Sort-Object)
if(@(Compare-Object $expected $actual).Count){throw 'Unexpected S3 file'}
$hash=[WolvenKit.Common.Services.HashService]::new();$hash.Load()
$archivePath=Join-Path $build $archiveName
$stream=[IO.File]::Create($archivePath)
try{
  $writer=[WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hash,[WolvenKit.SerilogWrapper]::new())
  if(-not $writer.WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Archive build failed'}
}finally{$stream.Dispose()}
$reader=[WolvenKit.RED4.Archive.IO.ArchiveReader]::new();$archive=$null
if($reader.ReadArchive($archivePath,$hash,[ref]$archive).ToString() -ne 'NoError'){throw 'Archive reopen failed'}
$packed=@($archive.Files.Values|ForEach-Object{$_.Name}|Sort-Object)
if(@(Compare-Object $expected $packed).Count){throw 'Archive manifest differs'}
$crc=65535
foreach($byte in [Text.Encoding]::UTF8.GetBytes($gateDepot+':1')){
  $x=($crc -shr 8) -bxor $byte;$x=$x -bxor ($x -shr 4)
  $crc=(($crc -shl 8) -bxor ($x -shl 12) -bxor ($x -shl 5) -bxor $x) -band 65535
}
$ep1=Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\q307_extracted\raw\ep1\quest\ep1.quest')
if($crc -in 11985,51719 -or @($ep1.RootChunk.Graph.Chunk.Nodes|Where-Object{$_.Chunk.Id.ToString() -eq "$crc"}).Count){throw 'Native registration collision'}
Copy-Item -LiteralPath (Join-Path $WorkspaceRoot "archive\b0_streetkid_scene_load_s3\$archiveName.xl") -Destination ($archivePath+'.xl') -Force
$manifest=[ordered]@{status='ACTOR_INDEX_REPAIR_BUILT';revision=2;archive=$archiveName;sha256=(Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash;xl_sha256=(Get-FileHash -LiteralPath ($archivePath+'.xl') -Algorithm SHA256).Hash;registration_id=$crc;resources=$packed;story_fact_writes=@();vanilla_replacements=@();action_events=0;choices=0;workspots=0;duration_ms=2000;repaired_V_acquisition_only=$true;dense_actor_ids=@(0,1,2);crash_actor_index_fixed=$true;opt_in_fact='PTFRSKS3_Enabled'}
[IO.File]::WriteAllText((Join-Path $audit 'build_manifest.json'),($manifest|ConvertTo-Json -Depth 5),[Text.UTF8Encoding]::new($false))
$manifest|ConvertTo-Json -Depth 5
