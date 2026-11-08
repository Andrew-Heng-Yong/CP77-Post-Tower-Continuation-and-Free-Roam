param([string]$OutputName='experiments/markers_01')
# PRIVATE TWO-TRIGGER EXPERIMENT ONLY. It is not registered, packed or installed.
$ErrorActionPreference='Stop'
$ws=(Get-Location).Path;$homeDir=Join-Path $ws 'prealpha/quest_restoration_qr7/worker_b';$out=Join-Path $homeDir $OutputName
if(Test-Path -LiteralPath $out){throw 'Fresh output required'}
New-Item -ItemType Directory -Path $out -Force|Out-Null
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$source=(Get-Content -Raw -LiteralPath (Join-Path $homeDir 'bar_provider_02/manifest.json')|ConvertFrom-Json).providers[0]
$blockSource=(Get-Content -Raw -LiteralPath (Join-Path $ws 'prealpha/quest_restoration_qr7/shared/marker_providers_01/manifest.json')|ConvertFrom-Json).providers[1]
foreach($p in @($source,$blockSource)){if((Get-FileHash -LiteralPath $p.raw).Hash -cne $p.raw_sha256){throw 'Pinned native input changed'}}
$sector=Read-Cr2wFile $source.raw;$r=$sector.RootChunk;$nativeBytes=$r.NodeData.Buffer.GetBytes()
if($nativeBytes.Length -ne 75*144 -or $r.Nodes.Count -ne 75){throw 'Pinned native bar scope changed'}
$privateParent='$/03_night_city/#PTFRQR7_RonaldNewsMarkers'
$privateRefs=@(($privateParent+'/#PTFRQR7_RonaldArea02'),($privateParent+'/#PTFRQR7_RonaldArea02Closer'))
$sectorDepot='towercontinued\quest_restoration_qr7\ronald_news_markers.streamingsector'
$blockDepot='towercontinued\quest_restoration_qr7\ronald_news_markers.streamingblock'
$ns=@();$ds=@();$i=0
foreach($sourceIndex in @(1,3)){
 $n=$r.Nodes[$sourceIndex].DeepCopy();$d=$r.NodeData.Data[$sourceIndex].DeepCopy()
 if($n.Chunk.GetType().Name -ne 'worldTriggerAreaNode'){throw 'Source selection is not a trigger'}
 $packed=[BitConverter]::ToUInt32($nativeBytes,$sourceIndex*144+0x70)
 if(($packed -band 0x7ffff) -ne $sourceIndex){throw 'Current2.5 packed source index changed'}
 # WK9.1 calls bytes0x70 MaxStreamingDistance, but current source layout stores the index here.
 $newPacked=($packed -band 0xfff80000) -bor [uint32]$i
 $d.MaxStreamingDistance=[WolvenKit.RED4.Types.CFloat]::op_Implicit([BitConverter]::UInt32BitsToSingle($newPacked))
 $d.QuestPrefabRefHash=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($privateRefs[$i])
 $ns+=,$n;$ds+=,$d;$i++
}
$r.Nodes.Clear();$r.NodeData.Data.Clear();$r.NodeRefs.Clear()
foreach($n in $ns){[void]$r.Nodes.Add($n)}
foreach($d in $ds){[void]$r.NodeData.Data.Add($d)}
foreach($ref in $privateRefs){[void]$r.NodeRefs.Add([WolvenKit.RED4.Types.NodeRef]::op_Implicit($ref))}
$raw=Join-Path $out 'markers.NONPRODUCTION.streamingsector';$json=$raw+'.json'
Write-Cr2wFile $sector $raw;$back=Read-Cr2wFile $raw;Export-Cr2wJson $back $json
$buffer=Join-Path $out 'markers.NODESETUPS.bin';[IO.File]::WriteAllBytes($buffer,$back.RootChunk.NodeData.Buffer.GetBytes())
$block=Read-Cr2wFile $blockSource.raw;$descriptor=$block.RootChunk.Descriptors[1995].DeepCopy()
if($descriptor.Data.DepotPath.ToString() -cne $source.depot -or $descriptor.Category.ToString() -ne 'Quest' -or $descriptor.Variants.Count -ne 0){throw 'Pinned native bar descriptor changed'}
$descriptor.Data=[Activator]::CreateInstance($descriptor.GetType().GetProperty('Data').PropertyType,[object[]]@([WolvenKit.RED4.Types.ResourcePath]::op_Implicit($sectorDepot)))
$descriptor.QuestPrefabNodeRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($privateParent)
$block.RootChunk.Descriptors.Clear();[void]$block.RootChunk.Descriptors.Add($descriptor)
$blockRaw=Join-Path $out 'markers.NONPRODUCTION.streamingblock';$blockJson=$blockRaw+'.json'
Write-Cr2wFile $block $blockRaw;Export-Cr2wJson (Read-Cr2wFile $blockRaw) $blockJson
@{status='PRIVATE_TWO_TRIGGER_EXPERIMENT_NOT_REGISTERED';native=$source;native_block=$blockSource;private_parent=$privateParent;private_refs=$privateRefs;intended_sector_depot=$sectorDepot;intended_block_depot=$blockDepot;raw=$raw;raw_sha256=(Get-FileHash -LiteralPath $raw).Hash;json=$json;json_sha256=(Get-FileHash -LiteralPath $json).Hash;buffer=$buffer;buffer_sha256=(Get-FileHash -LiteralPath $buffer).Hash;block_raw=$blockRaw;block_raw_sha256=(Get-FileHash -LiteralPath $blockRaw).Hash;block_json=$blockJson;block_json_sha256=(Get-FileHash -LiteralPath $blockJson).Hash;candidate_writes=0;registered=$false}|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $out 'NOT_FOR_INTEGRATION.json') -Encoding utf8
Write-Output 'Private two-trigger experiment serialized/read back; unregistered'
