Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
$wa=Split-Path $PSScriptRoot -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
function ReadWorld([string]$path){
 $stream=[IO.File]::OpenRead($path)
 try{$reader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($stream);$reader.add_ParsingError([WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e)return ($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])});$file=$null;if($reader.ReadFile([ref]$file,$true).ToString() -cne 'NoError'){throw 'Read failed'};return $file}finally{$stream.Dispose()}
}
function HashBytes([byte[]]$bytes){return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))}
function Json($object){return [WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($object,[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())}
$core=Get-Content -LiteralPath (Join-Path $wa 'combat_review/filters_core_spec_01.json') -Raw|ConvertFrom-Json -Depth 70
$extra=Get-Content -LiteralPath (Join-Path $wa 'combat_review/filters_additional_spec_01.json') -Raw|ConvertFrom-Json -Depth 70
$payload=Get-Content -LiteralPath (Join-Path $wa 'combat_review/payload_assessment_02.json') -Raw|ConvertFrom-Json -Depth 70
if($core.status -cne 'PASS_CORE_NEW_OWNER_TRIGGER_FILTER_SPEC' -or $core.owners -ne 222 -or $extra.groups.Count -ne 94 -or $payload.status -cne 'PASS_ADDITIONAL94_PASSIVE_SUPPORT_PAYLOADS' -or $payload.private_filter_ids.Count -ne 94){throw 'Filter audit incomplete'}
$source=Join-Path $PSScriptRoot 'source_comprehensive_08';if(Test-Path -LiteralPath $source){throw 'Preserve comprehensive source evidence'}
[void][IO.Directory]::CreateDirectory($source)
$blockReport=Get-Content -LiteralPath (Join-Path $wa 'environment_variants/extract_02/report_01.json') -Raw|ConvertFrom-Json -Depth 50
$blockHits=@($blockReport.hits|Where-Object {$_.depot.EndsWith('all.streamingblock') -and [IO.Path]::GetFileName($_.archive) -ceq 'ep1_1_nightcity.archive'})
if($blockHits.Count -ne 1){throw 'Native default streaming block unresolved'}
$blockHit=$blockHits[0];if((Get-FileHash -LiteralPath $blockHit.raw).Hash -cne $blockHit.sha256){throw 'Native block drift'}
$block=ReadWorld $blockHit.raw;$descriptors=@($block.RootChunk.Descriptors);$block.RootChunk.Descriptors.Clear()
$specs=@($core.rows)+@($extra.groups);$rows=@();$resources=@();$seen=[Collections.Generic.HashSet[int]]::new()
foreach($spec in $specs){
 $id=if($spec.PSObject.Properties.Name -contains 'group'){[int]$spec.group}else{[int]$spec.id}
 if(!$seen.Add($id)){throw ('Duplicate group '+$id)}
 if($id -eq 1013){continue} # WolvenKit 9.1 cannot read this native dynamic worldNode sector.
 $rawPath=if($spec.PSObject.Properties.Name -contains 'support_sector_raw'){[string]$spec.support_sector_raw}else{[string]$spec.sector_raw}
 $rawHash=if($spec.PSObject.Properties.Name -contains 'support_sector_sha256'){[string]$spec.support_sector_sha256}else{[string]$spec.sector_sha256}
 $nativePrefab=[string]$spec.native_prefab
 $nativeResource=if($spec.PSObject.Properties.Name -contains 'support_sector_resource'){[string]$spec.support_sector_resource}else{[string]$spec.sector_resource}
 if((Get-FileHash -LiteralPath $rawPath).Hash -cne $rawHash){throw ('Native sector drift '+$id)}
 $file=ReadWorld $rawPath;$root=$file.RootChunk;$remove=@($spec.drop_nodes|ForEach-Object {[int]$_}|Sort-Object -Unique)
 if($root.Version.ToString() -cne '68' -or ($null -ne $root.PersistentNodes -and $root.PersistentNodes.Count -ne 0) -or $root.VariantIndices.Count -lt 1 -or @($root.VariantNodes|Where-Object {$_.Count -ne 0}).Count -ne 0){throw ('Unsupported sector layout '+$id)}
 if($root.Nodes.Count -ne [int]$(if($spec.PSObject.Properties.Name -contains 'native_node_count'){$spec.native_node_count}else{$root.Nodes.Count})){throw ('Node count drift '+$id)}
 $nativeNodes=@($root.Nodes|ForEach-Object {Json $_.Chunk});$raw=$root.NodeData.Buffer.GetBytes()
 if($raw.Length -ne $root.NodeData.Data.Count*144){throw ('Placement stride drift '+$id)}
 foreach($index in $remove){
  if($index -lt 0 -or $index -ge $root.Nodes.Count){throw ('Removed index out of range '+$id)}
  $type=$root.Nodes[$index].Chunk.GetType().Name
  if($type -cne 'worldTriggerAreaNode' -and $id -eq 1246 -and $index -in @(29,34) -and $type -ceq 'worldPopulationSpawnerNode'){$true|Out-Null}
  elseif($type -cne 'worldTriggerAreaNode' -and $id -in @(160,161,1000,1004)){$true|Out-Null}
  elseif($type -cne 'worldTriggerAreaNode'){throw ('Unexpected removed node type '+$id+'/'+$index+'/'+$type)}
 }
 $bytes=[Collections.Generic.List[byte]]::new();$kept=@();$removed=@()
 for($i=0;$i -lt $root.NodeData.Data.Count;$i++){
  $offset=$i*144;$bits=[BitConverter]::ToUInt64($raw,$offset+0x70);$old=[int]($bits -band [uint64]0x7FFFF)
  if($old -ge $root.Nodes.Count){throw ('Opaque node index out of range '+$id)}
  if($remove -contains $old){$removed+=@{datum=$i;native_node=$old;sha256=HashBytes ([byte[]]$raw[$offset..($offset+143)])};continue}
  $new=$old-@($remove|Where-Object {$_ -lt $old}).Count
  $record=[byte[]]$raw[$offset..($offset+143)]
  $replacement=($bits -band ([uint64]::MaxValue -bxor [uint64]0x7FFFF)) -bor [uint64]$new
  [Array]::Copy([BitConverter]::GetBytes($replacement),0,$record,0x70,8);$bytes.AddRange($record)
  $kept+=@{native_datum=$i;native_node=$old;private_node=$new;native_sha256=HashBytes ([byte[]]$raw[$offset..($offset+143)]);private_sha256=HashBytes $record}
 }
 if($removed.Count -ne $remove.Count){throw ('Removed placement mismatch '+$id)}
 $variantBefore=@($root.VariantIndices|ForEach-Object {[int]$_.ToString()})
 foreach($index in @($remove|Sort-Object -Descending)){$root.Nodes.RemoveAt($index)}
 for($v=0;$v -lt $root.VariantIndices.Count;$v++){
  $oldVariant=$variantBefore[$v];if($oldVariant -lt 0 -or $oldVariant -gt $nativeNodes.Count){throw ('Variant index out of range '+$id)}
  $newVariant=$oldVariant-@($remove|Where-Object {$_ -lt $oldVariant}).Count
  $root.VariantIndices[$v]=[WolvenKit.RED4.Types.CInt32]::op_Implicit([int]$newVariant)
 }
 $root.NodeData.Buffer.Data=$null;$root.NodeData.Buffer.SetBytes($bytes.ToArray())
 $privateRef='$/03_night_city/towercontinued/world_support_wa3/group'+$id+'_support'
 $hash=[WolvenKit.RED4.Types.NodeRef]::CalculateHash($privateRef)
 $depot='base\worlds\03_night_city\_compiled\default\quest_'+$hash.ToString('x16')+'.streamingsector'
 $out=Join-Path $source $depot;Write-Cr2wFile $file $out
 $read=ReadWorld $out;if(@(Compare-Object @($root.VariantIndices|ForEach-Object {$_.ToString()}) @($read.RootChunk.VariantIndices|ForEach-Object {$_.ToString()})).Count){throw ('Variant index readback drift '+$id)};$readBytes=$read.RootChunk.NodeData.Buffer.GetBytes()
 if((HashBytes $readBytes) -cne (HashBytes $bytes.ToArray()) -or $read.RootChunk.Nodes.Count -ne $nativeNodes.Count-$remove.Count){throw ('Readback structure drift '+$id)}
 foreach($p in $kept){if((Json $read.RootChunk.Nodes[$p.private_node].Chunk) -cne $nativeNodes[$p.native_node]){throw ('Retained definition drift '+$id+'/'+$p.native_node)}}
 $desc=@($descriptors|Where-Object {$_.Data.DepotPath.ToString() -ceq $nativeResource})
 $authored=$nativePrefab.Replace('/rancho_coronado/','/#rancho_coronado/')
 if($desc.Count -ne 1 -or $desc[0].QuestPrefabNodeRef.ToString() -cnotin @($nativePrefab,$authored) -or $desc[0].Category.ToString() -cne 'Quest' -or $desc[0].Variants.Count -ne $(if($null -eq $root.VariantNodes){0}else{$root.VariantNodes.Count})){throw ('Native descriptor mismatch '+$id)}
 $copy=$desc[0].DeepCopy();$copy.QuestPrefabNodeRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($privateRef)
 $copy.Data=[Activator]::CreateInstance($copy.GetType().GetProperty('Data').PropertyType,[object[]]@([WolvenKit.RED4.Types.ResourcePath]::op_Implicit($depot)))
 [void]$block.RootChunk.Descriptors.Add($copy)
 $newHash=(Get-FileHash -LiteralPath $out).Hash;$resources+=@{depot=$depot;sha256=$newHash}
 $rows+=@{group=$id;native_prefab=$nativePrefab;prefab_ref=$privateRef;native_resource=$nativeResource;native_raw=$rawPath;native_sha256=$rawHash;depot=$depot;sha256=$newHash;node_ref_hash=$hash.ToString();native_nodes=$nativeNodes.Count;private_nodes=$read.RootChunk.Nodes.Count;drop_nodes=$remove;variant_indices_before=$variantBefore;variant_indices_after=@($read.RootChunk.VariantIndices|ForEach-Object {[int]$_.ToString()});removed=$removed;retained=$kept;native_placement_sha256=HashBytes $raw;private_placement_sha256=HashBytes $readBytes;native_descriptor=(Json $desc[0]|ConvertFrom-Json -Depth 30);private_descriptor=(Json $copy|ConvertFrom-Json -Depth 30)}
 if($rows.Count%25 -eq 0){Write-Host ('Filtered '+$rows.Count+'/'+$specs.Count)}
}
$blockDepot='towercontinued\world_support_wa3\filtered_support_comprehensive.streamingblock';$blockOut=Join-Path $source $blockDepot
Write-Cr2wFile $block $blockOut;$blockRead=ReadWorld $blockOut
if($blockRead.RootChunk.Descriptors.Count -ne $rows.Count){throw 'Block descriptor readback mismatch'}
$resources+=@{depot=$blockDepot;sha256=(Get-FileHash -LiteralPath $blockOut).Hash}
$proof=@{status='COMPREHENSIVE_PRIVATE_SUPPORT_SERIALIZED_PENDING_INDEPENDENT_VERIFICATION';groups=$rows;resources=$resources;streaming_blocks=@($blockDepot);sector_bindings=@($rows|ForEach-Object {@{depot=$_.depot;prefab_ref=$_.prefab_ref;node_ref_hash=$_.node_ref_hash}});native_block=$blockHit.raw;native_block_sha256=$blockHit.sha256;block_sha256=(Get-FileHash -LiteralPath $blockOut).Hash;native_world_overrides=0;retained_workspot_ids_changed=0;game_writes=0;save_writes=0}
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'build_comprehensive_proof_08.json'),($proof|ConvertTo-Json -Depth 45)+"`n",[Text.UTF8Encoding]::new($false))
@{status=$proof.status;groups=$rows.Count;resources=$resources.Count}|ConvertTo-Json
