param([string]$OutputName='experiments/enrollment_01')
# PRIVATE EXPERIMENT ONLY. This does not establish a complete news owner/lease repair.
$ErrorActionPreference='Stop'
$ws=(Get-Location).Path;$homeDir=Join-Path $ws 'prealpha/quest_restoration_qr7/worker_b';$out=Join-Path $homeDir $OutputName
if(Test-Path -LiteralPath $out){throw 'Fresh output required'}
New-Item -ItemType Directory -Path $out -Force|Out-Null
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$pins=Get-Content -Raw -LiteralPath (Join-Path $homeDir 'raw_inputs_01.json')|ConvertFrom-Json
$native=@($pins|Where-Object {$_.depot -ceq 'ep1\quest\main_quests\q302\scenes\q302_05_bar.scene'})[0]
$current=@($pins|Where-Object {$_.depot -ceq 'towercontinued\b0_story_eight\ronald.scene'})[0]
foreach($p in @($native,$current)){if((Get-FileHash -LiteralPath $p.raw).Hash -cne $p.raw_sha256){throw 'Pinned scene changed'}}
$n=Read-Cr2wFile $native.raw;$c=Read-Cr2wFile $current.raw
$nn=@($n.RootChunk.SceneGraph.Chunk.Graph|Where-Object {$_.Chunk.NodeId.Id.ToString() -eq '839'})[0].Chunk
$cn=@($c.RootChunk.SceneGraph.Chunk.Graph|Where-Object {$_.Chunk.NodeId.Id.ToString() -eq '839'})[0].Chunk
if($nn.Options.Count -ne 6 -or $cn.Options.Count -ne 6){throw 'Native option identities changed'}
foreach($i in @(3,4)){
 if($cn.OutputSockets[$i].Destinations.Count -ne 0 -or $nn.OutputSockets[$i].Destinations.Count -ne 1){throw 'Exact lost native destination changed'}
 $cn.Options[$i]=$nn.Options[$i].DeepCopy()
 $cn.OutputSockets[$i]=$nn.OutputSockets[$i].DeepCopy()
}
$raw=Join-Path $out 'ronald.scene';$json=Join-Path $out 'ronald.scene.json'
Write-Cr2wFile $c $raw
Export-Cr2wJson (Read-Cr2wFile $raw) $json
@{status='PRIVATE_EXPERIMENT_NOT_APPROVED';native=$native;current=$current;raw=$raw;raw_sha256=(Get-FileHash -LiteralPath $raw).Hash;json=$json;json_sha256=(Get-FileHash -LiteralPath $json).Hash;changes=@('native choice839 option3 condition/destination','native choice839 option4 condition/destination');not_proven=@('isolated news owner','marker-only lease','saved-owner arbitration');production_changes=0}|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $out 'NOT_FOR_INTEGRATION.json') -Encoding utf8
Write-Output 'Private enrollment experiment serialized/read back; not approved for integration'
