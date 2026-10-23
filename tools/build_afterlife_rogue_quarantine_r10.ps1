param(
 [string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),
 [string]$OutputPath=''
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\afterlife_world\interactions_r10\scene_review'
if(-not $OutputPath){$OutputPath=Join-Path $WorkspaceRoot 'build\AfterlifeInteractionsR10\source\towercontinued\afterlife_interactions_r8\rogue.scene'}
$sourcePath=Join-Path $WorkspaceRoot 'build\AfterlifeInteractionsR9\source\towercontinued\afterlife_interactions_r8\rogue.scene'
$prior=Read-Cr2wFile $sourcePath
$priorHash=(Get-FileHash -LiteralPath $sourcePath).Hash
# Preserve the saved quest scene node's known entry/exit names and IDs, but
# replace its acquisition/action-bearing resource with an empty passthrough.
# Runtime false alone cannot protect a scene request resumed from a saved node.
$root=[WolvenKit.RED4.Types.scnSceneResource]::new()
$root.CookingPlatform=$prior.RootChunk.CookingPlatform
$root.Version=$prior.RootChunk.Version
$root.SceneCategoryTag=$prior.RootChunk.SceneCategoryTag
$root.SceneSolutionHash=$prior.RootChunk.SceneSolutionHash.DeepCopy()
$graph=[WolvenKit.RED4.Types.scnSceneGraph]::new()
$start=@($prior.RootChunk.SceneGraph.Chunk.Graph|Where-Object {$_.Chunk.NodeId.Id.ToString() -eq '1'})[0].Chunk.DeepCopy()
$end=@($prior.RootChunk.SceneGraph.Chunk.Graph|Where-Object {$_.Chunk.NodeId.Id.ToString() -eq '2'})[0].Chunk.DeepCopy()
if($start.GetType().Name -ne 'scnStartNode' -or $end.GetType().Name -ne 'scnEndNode'){throw 'Unexpected quarantine endpoints'}
if($start.OutputSockets.Count -ne 1 -or $start.OutputSockets[0].Destinations.Count -ne 2){throw 'Unexpected original start fanout'}
$destination=$start.OutputSockets[0].Destinations[0].DeepCopy()
$destination.NodeId.Id=[uint32]2
$destination.IsockStamp.Name=[uint16]0
$destination.IsockStamp.Ordinal=[uint16]0
$start.OutputSockets[0].Destinations.Clear()
[void]$start.OutputSockets[0].Destinations.Add($destination)
foreach($s in $end.OutputSockets){$s.Destinations.Clear()}
Add-RedHandle $graph.Graph $start
Add-RedHandle $graph.Graph $end
[void]$graph.StartNodes.Add($start.NodeId.DeepCopy())
[void]$graph.EndNodes.Add($end.NodeId.DeepCopy())
Set-RedHandleProperty $root SceneGraph $graph
[void]$root.EntryPoints.Add($prior.RootChunk.EntryPoints[0].DeepCopy())
[void]$root.ExitPoints.Add($prior.RootChunk.ExitPoints[0].DeepCopy())
if($root.EntryPoints[0].Name.ToString() -ne 'in' -or $root.ExitPoints[0].Name.ToString() -ne 'local_out'){throw 'Saved scene socket identity changed'}
$file=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new()
$file.RootChunk=$root
Write-Cr2wFile $file $OutputPath
$readback=Read-Cr2wFile $OutputPath
Export-Cr2wJson $readback (Join-Path $audit 'rogue_quarantine.scene.json')
if($readback.RootChunk.Actors.Count -ne 0 -or $readback.RootChunk.PlayerActors.Count -ne 0 -or $readback.RootChunk.SceneGraph.Chunk.Graph.Count -ne 2){throw 'Quarantine scope drift'}
if((Get-FileHash -LiteralPath $sourcePath).Hash -ne $priorHash){throw 'Historical R9 scene changed'}
[pscustomobject]@{status='ROGUE_SCENE_QUARANTINE_BUILT_NOT_LIVE';path=$OutputPath;sha256=(Get-FileHash -LiteralPath $OutputPath).Hash;source_sha256=$priorHash;entry='in';exit='local_out';actors=0;nodes=2;purpose='Saved-node containment, not crash cause proof'}
