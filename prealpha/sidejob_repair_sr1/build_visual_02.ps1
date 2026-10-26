Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$out=Join-Path $PSScriptRoot 'candidate_02/visual_02'
if(Test-Path -LiteralPath $out){throw 'Visual candidate exists; use a successor'}
New-Item -ItemType Directory -Path $out -Force|Out-Null
$depot='towercontinued\sidejobs_s29\native\base\quest\minor_quests\mq036\scenes\mq036_scavengers.scene'
$src=Join-Path $ws 'diagnostics/stefan_lipsync_20261025_01/installed_audit_01/scenes/00000000_TowerContinued_SideJobs_S29.archive/1572008326021521841.scene'
if((Get-FileHash -LiteralPath $src).Hash -cne '5E971873D2F1BDD227954F9144823CAAEE0A1423D63A2B15F99FF0A78F5E8B26'){throw 'Sweet Dreams scene source drift'}
$file=Read-Cr2wFile $src;$root=$file.RootChunk
function SceneNode([int]$id){$n=@($root.SceneGraph.Chunk.Graph|Where-Object {$_.Chunk.NodeId.Id.ToString() -ceq $id.ToString()});if($n.Count -ne 1){throw "Scene node $id ambiguous"};return $n[0].Chunk}
$template=(SceneNode 131).QuestNode.Chunk.ParamsV1.Chunk
$instances=@($root.WorkspotInstances|Where-Object {$_.WorkspotInstanceId.Id.ToString() -ceq '131'})
if($instances.Count -ne 1 -or @($root.WorkspotInstances|Where-Object {$_.WorkspotInstanceId.Id.ToString() -ceq '3131'}).Count -ne 0){throw 'Private Johnny workspot instance changed'}
$instance=$instances[0].DeepCopy();$instance.WorkspotInstanceId.Id=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]3131)
$instance.PlayAtActorLocation=$false
$instance.OriginMarker.NodeRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit('#mq036_ws_johnny_exit')
$root.WorkspotInstances.Add($instance)
foreach($id in @(158,1073)){
 $node=(SceneNode $id).QuestNode.Chunk;$old=$node.ParamsV1.Chunk
 if($old.GetType().Name -cne 'questUseWorkspotParamsV1' -or $old.WorkspotNode.ToString() -cne '#mq036_ws_johnny_exit'){throw "World workspot node $id drift"}
 $new=$template.DeepCopy()
 foreach($property in $old.GetType().GetProperties()){
  $name=$property.Name;$target=$new.GetType().GetProperty($name)
  if($null -ne $target -and $target.CanWrite -and $name -notin @('WorkspotNode')){$target.SetValue($new,$property.GetValue($old))}
 }
 $new.WorkspotInstanceId.Id=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]3131)
 $new.PlayAtActorLocation=$false
 $new.WorkspotNode=[WolvenKit.RED4.Types.NodeRef]::op_Implicit('')
 Set-RedHandleProperty $node ParamsV1 $new
}
$raw=Join-Path $out $depot;Write-Cr2wFile $file $raw
$readback=Join-Path $out 'sweet_dreams_scene.json';Export-Cr2wJson (Read-Cr2wFile $raw) $readback
$proof=[ordered]@{status='WORKSPACE_VISUAL_SWEET_DREAMS_NOT_INSTALLED';depot=$depot;source_sha256=(Get-FileHash -LiteralPath $src).Hash;patched_sha256=(Get-FileHash -LiteralPath $raw).Hash;readback_sha256=(Get-FileHash -LiteralPath $readback).Hash;nodes=@(158,1073);new_instance=3131;private_workspot_instance=131;world_marker='#mq036_ws_johnny_exit';game_writes=0;save_writes=0}
[IO.File]::WriteAllText((Join-Path $out 'proof.json'),($proof|ConvertTo-Json -Depth 20),[Text.UTF8Encoding]::new($false))
$proof|ConvertTo-Json -Depth 20
