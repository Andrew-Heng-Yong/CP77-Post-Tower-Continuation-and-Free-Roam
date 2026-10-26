Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$candidate=Join-Path $PSScriptRoot 'candidate_02'
$out=Join-Path $candidate 'visual_04'
if(Test-Path -LiteralPath $out){throw 'Visual candidate exists; use successor'}
New-Item -ItemType Directory -Path $out -Force|Out-Null
$prior=Get-Content -LiteralPath (Join-Path $candidate 'visual_03/proof.json') -Raw|ConvertFrom-Json
foreach($m in @($prior.sweet_dreams,$prior.sinnerman)){$p=Join-Path $candidate ('visual_03/'+$m.depot);if((Get-FileHash -LiteralPath $p).Hash -cne $m.patched_sha256){throw ('Prior visual drift '+$m.depot)};$q=Join-Path $out $m.depot;New-Item -ItemType Directory -Path (Split-Path $q -Parent) -Force|Out-Null;Copy-Item -LiteralPath $p -Destination $q}
$sweet=Read-Cr2wFile (Join-Path $out $prior.sweet_dreams.depot)
$sweetRoot=$sweet.RootChunk
$sweetTemplate=@($sweetRoot.SceneGraph.Chunk.Graph|Where-Object {$_.Chunk.NodeId.Id.ToString() -ceq '158'})[0].Chunk.QuestNode.Chunk.ParamsV1.Chunk
$sweetData=@($sweetRoot.Workspots|Where-Object {$_.Chunk.DataId.Id.ToString() -ceq '4231323113'})[0].Chunk
$sweetInstance=@($sweetRoot.WorkspotInstances|Where-Object {$_.WorkspotInstanceId.Id.ToString() -ceq '3131'})[0]
$ground='towercontinued\sidejobs_s29\native\base\workspots\main_characters\johnny\johnny__stand_ground_cigarette__idle__01.workspot'
$walk='towercontinued\sidejobs_s29\native\base\workspots\main_characters\johnny\ground\johnny__walk_ground_cigarette__aggressive__01.workspot'
$privateKold='towercontinued\sidejob_repair_sr1\workspots\sq006__johnny__stand_cigarette__stand_around__01.workspot'
$base='diagnostics/stefan_lipsync_20261025_01/installed_audit_01/scenes/00000000_TowerContinued_SideJobs_S29.archive'
$cases=@(
 @{depot='towercontinued\sidejobs_s29\native\base\quest\side_quests\sq025\scenes\sq025_07_resurgence.scene';id='12772498349548735763';sha='7874E068FFCB83180DAA16E94E0DB4D6547F0D1D56C0026C20629EF6B60ACCEC';anchor='#sq025_ws_johnny_resurgence';nodes=@(298,305,408);instance=4298;kind='ground'},
 @{depot='towercontinued\sidejobs_s29\native\base\quest\minor_quests\mq018\scenes\mq018_07_protein.scene';id='7916485406720080517';sha='2D16A900B0ACB57386A59C13948E938136B75303C46D779AF1CEA34FC667FDF9';anchor='#mq018_ws_johnny_protein_stairs';nodes=@(292,312,315,327,330,333);instance=4292;kind='ground'},
 @{depot='towercontinued\sidejobs_s29\native\base\quest\minor_quests\mq059\scenes\mq059_play_vos.scene';id='14754961886327623219';sha='521DE6C1F25CC62503E6653BD60E3199368462FE2E3AFFCBA8AF0DCAC29B001E';anchor='#loc1_Johnny_corpses';nodes=@(178);instance=178;kind='freedom'},
 @{depot='towercontinued\sidejobs_s29\native\base\quest\minor_quests\mq016\scenes\mq016_01_freezer.scene';id='3808959417876599003';sha='6C9E2EE22A98D39FDDC3370BCB7EAFC72D59ED62C3C224788CA8A1D121853F6C';anchor='#mq016_ws_johnny_at_coffin';nodes=@(318);instance=6318;kind='kold'}
)
function Node($root,[int]$id){$matches=@($root.SceneGraph.Chunk.Graph|Where-Object {$_.Chunk.NodeId.Id.ToString() -ceq $id.ToString()});if($matches.Count -ne 1){throw "Scene node $id ambiguous"};return $matches[0].Chunk}
function ConvertWorld($root,[int]$id,[int]$instance,[string]$anchor,$template){
 $node=(Node $root $id).QuestNode.Chunk;$old=$node.ParamsV1.Chunk
 if($old.GetType().Name -cne 'questUseWorkspotParamsV1' -or $old.WorkspotNode.ToString() -cne $anchor){throw "World node $id changed"}
 $new=$template.DeepCopy()
 foreach($p in $old.GetType().GetProperties()){$name=$p.Name;$target=$new.GetType().GetProperty($name);if($null -ne $target -and $target.CanWrite -and $name -cne 'WorkspotNode'){$target.SetValue($new,$p.GetValue($old))}}
 $new.WorkspotInstanceId.Id=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]$instance)
 $new.PlayAtActorLocation=$false
 $new.WorkspotNode=[WolvenKit.RED4.Types.NodeRef]::op_Implicit('')
 Set-RedHandleProperty $node ParamsV1 $new
}
$rows=@()
foreach($case in $cases){
 $src=Join-Path $ws ($base+'/'+$case.id+'.scene');if((Get-FileHash -LiteralPath $src).Hash -cne $case.sha){throw ('Source drift '+$case.depot)}
 $file=Read-Cr2wFile $src;$root=$file.RootChunk
 if($case.kind -ceq 'freedom'){
  $spot=@($root.Workspots|Where-Object {$_.Chunk.DataId.Id.ToString() -ceq '3111754765'});if($spot.Count -ne 1 -or $spot[0].Chunk.WorkspotResource.DepotPath.ToString() -cne 'base\workspots\main_characters\johnny\ground\johnny__walk_ground_cigarette__aggressive__01.workspot'){throw 'Freedom smoking workspot changed'}
  $spot[0].Chunk.WorkspotResource.DepotPath=[WolvenKit.RED4.Types.ResourcePath]::op_Implicit($walk)
  $node=(Node $root 178).QuestNode.Chunk.ParamsV1.Chunk;if($node.WorkspotInstanceId.Id.ToString() -cne '178' -or $node.WorkspotNode.ToString() -cne $case.anchor){throw 'Freedom workspot call changed'}
 }else{
  if(@($root.WorkspotInstances|Where-Object {$_.WorkspotInstanceId.Id.ToString() -ceq $case.instance.ToString()}).Count -ne 0){throw ('Instance ID used '+$case.depot)}
  if($case.kind -ceq 'ground'){$data=$sweetData.DeepCopy();$instance=$sweetInstance.DeepCopy();$template=$sweetTemplate}
  else{
   $donor=@($root.Workspots|Where-Object {$_.Chunk.DataId.Id.ToString() -ceq '310558781'});$inst=@($root.WorkspotInstances|Where-Object {$_.WorkspotInstanceId.Id.ToString() -ceq '602'})
   if($donor.Count -ne 1 -or $inst.Count -ne 1){throw 'KOLD donor changed'}
   $data=$donor[0].Chunk.DeepCopy();$data.DataId.Id=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]3237006318)
   $data.WorkspotResource.DepotPath=[WolvenKit.RED4.Types.ResourcePath]::op_Implicit($privateKold)
   $instance=$inst[0].DeepCopy();$instance.DataId.Id=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]3237006318)
   $template=(Node $root 602).QuestNode.Chunk.ParamsV1.Chunk
  }
  Add-RedHandle $root.Workspots $data
  $instance.WorkspotInstanceId.Id=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]$case.instance)
  $instance.PlayAtActorLocation=$false
  $instance.OriginMarker.NodeRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($case.anchor)
  $root.WorkspotInstances.Add($instance)
  foreach($id in $case.nodes){ConvertWorld $root $id $case.instance $case.anchor $template}
 }
 $raw=Join-Path $out $case.depot;New-Item -ItemType Directory -Path (Split-Path $raw -Parent) -Force|Out-Null;Write-Cr2wFile $file $raw
 Export-Cr2wJson (Read-Cr2wFile $raw) ($raw+'.json')
 $rows+=@{depot=$case.depot;source_sha256=$case.sha;patched_sha256=(Get-FileHash -LiteralPath $raw).Hash;nodes=$case.nodes;instance=$case.instance;anchor=$case.anchor;kind=$case.kind}
}
$koldSrc=Join-Path $candidate 'kold_workspot_source_01/memoryresident_1_general.workspot'
if((Get-FileHash -LiteralPath $koldSrc).Hash -cne 'F0E067A325FD370CFFD5B68BFCC00A5B2FA0EC480868BE03A94A014FECC24EE6'){throw 'KOLD native workspot drift'}
$kold=Read-Cr2wFile $koldSrc
$filter=$kold.RootChunk.NodesToInit[0].Chunk.Nodes[0].Chunk.Node.Node.Chunk
if($filter.EventFilterType.ToString() -cne 'Default'){throw 'KOLD native event filter changed'}
$filter.EventFilterType=[Enum]::Parse($filter.EventFilterType.GetType(),'Mute')
$koldRaw=Join-Path $out $privateKold;New-Item -ItemType Directory -Path (Split-Path $koldRaw -Parent) -Force|Out-Null;Write-Cr2wFile $kold $koldRaw
Export-Cr2wJson (Read-Cr2wFile $koldRaw) ($koldRaw+'.json')
$proof=[ordered]@{status='WORKSPACE_VISUAL_SEVEN_RESOURCE_SUCCESSOR_NOT_INSTALLED';prior_visual_proof_sha256=(Get-FileHash -LiteralPath (Join-Path $candidate 'visual_03/proof.json')).Hash;prior=@($prior.sweet_dreams,$prior.sinnerman);additional=$rows;new_private_kold=[ordered]@{depot=$privateKold;native_sha256=(Get-FileHash -LiteralPath $koldSrc).Hash;patched_sha256=(Get-FileHash -LiteralPath $koldRaw).Hash};game_writes=0;save_writes=0}
[IO.File]::WriteAllText((Join-Path $out 'proof.json'),($proof|ConvertTo-Json -Depth 40),[Text.UTF8Encoding]::new($false))
$proof|Select-Object status,@{n='additional_count';e={$_.additional.Count}},new_private_kold|ConvertTo-Json -Depth 20
