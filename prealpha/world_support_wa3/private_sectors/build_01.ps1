# Construct private quest support sectors; never replace a native world resource.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
$homeWA3=Split-Path $PSScriptRoot -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
function ReadWorld([string]$path){
 $stream=[IO.File]::OpenRead($path)
 try{$reader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($stream);$reader.add_ParsingError([WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e)return ($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])});$file=$null;if($reader.ReadFile([ref]$file,$true).ToString() -cne 'NoError'){throw 'Read failed'};return $file}finally{$stream.Dispose()}
}
function HashBytes([byte[]]$bytes){return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))}
function Json($object){return [WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($object,[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())}
$source=Join-Path $PSScriptRoot 'source_01';if(Test-Path -LiteralPath $source){throw 'Preserve private-sector evidence'}
[void][IO.Directory]::CreateDirectory($source)
$census=Get-Content -LiteralPath (Join-Path $homeWA3 'census_01.json') -Raw|ConvertFrom-Json -Depth 100
$extract=Get-Content -LiteralPath (Join-Path $homeWA3 'extracted_01/report_01.json') -Raw|ConvertFrom-Json -Depth 50
$blockReport=Get-Content -LiteralPath (Join-Path $homeWA3 'environment_variants/extract_01/report_01.json') -Raw|ConvertFrom-Json -Depth 50
$blockHit=@($blockReport.hits|Where-Object {$_.depot.EndsWith('all.streamingblock') -and [IO.Path]::GetFileName($_.archive) -ceq 'ep1_1_nightcity.archive'})[0]
if((Get-FileHash -LiteralPath $blockHit.raw).Hash -cne $blockHit.sha256){throw 'Native block drift'}
$nativeBlock=ReadWorld $blockHit.raw
$descriptors=@($nativeBlock.RootChunk.Descriptors)
$nativeBlock.RootChunk.Descriptors.Clear()
# This independent custom block index is checked against the previous package in verification.
$nativeBlock.RootChunk.Index.RldGridCell=[uint32]8425360
$rows=@();$resources=@()
foreach($spec in @(@{id=160;remove=@(42,43);nodes=44},@{id=161;remove=@(38);nodes=40})){
 $owner=@($census.rows|Where-Object id -eq $spec.id)[0]
 $hits=@($extract.hits|Where-Object resource -eq $owner.resource)
 if($hits.Count -ne 1 -or $hits[0].is_mod){throw 'Ambiguous native support source'}
 $hit=$hits[0];if((Get-FileHash -LiteralPath $hit.raw).Hash -cne $hit.sha256){throw 'Native sector drift'}
 $file=ReadWorld $hit.raw;$root=$file.RootChunk
 if($root.Nodes.Count -ne $spec.nodes -or $root.Version.ToString() -cne '68' -or $root.PersistentNodes.Count -ne 0 -or $root.VariantNodes.Count -ne 0 -or $root.VariantIndices.Count -ne 1){throw 'Unsupported native sector layout'}
 $raw=$root.NodeData.Buffer.GetBytes();if($raw.Length -ne $root.NodeData.Data.Count*144){throw 'Unsupported placement stride'}
 $originalNodes=@($root.Nodes|ForEach-Object {Json $_.Chunk})
 foreach($index in $spec.remove){$node=$root.Nodes[$index].Chunk;if($node.GetType().Name -cne 'worldPopulationSpawnerNode' -or $node.SpawnOnStart.ToString() -cne 'True'){throw 'Expected only automatic preview spawner removal'}}
 $bytes=[Collections.Generic.List[byte]]::new();$kept=@();$removed=@()
 for($i=0;$i -lt $root.NodeData.Data.Count;$i++){
  $offset=$i*144;$bits=[BitConverter]::ToUInt64($raw,$offset+0x70);$old=[int]($bits -band [uint64]0x7FFFF)
  if($old -ge $root.Nodes.Count){throw 'Raw node index out of range'}
  if($spec.remove -contains $old){$removed+=@{datum=$i;node=$old;record_sha256=HashBytes ([byte[]]$raw[$offset..($offset+143)])};continue}
  $new=$old-@($spec.remove|Where-Object {$_ -lt $old}).Count
  $record=[byte[]]$raw[$offset..($offset+143)]
  $replacement=($bits -band ([uint64]::MaxValue -bxor [uint64]0x7FFFF)) -bor [uint64]$new
  [Array]::Copy([BitConverter]::GetBytes($replacement),0,$record,0x70,8)
  $bytes.AddRange($record)
  $kept+=@{native_datum=$i;native_node=$old;private_node=$new;source_record_sha256=HashBytes ([byte[]]$raw[$offset..($offset+143)]);private_record_sha256=HashBytes $record}
 }
 if($removed.Count -ne $spec.remove.Count){throw 'Preview placements are not one per removed spawner'}
 foreach($index in @($spec.remove|Sort-Object -Descending)){$root.Nodes.RemoveAt($index)}
 $root.NodeData.Buffer.Data=$null
 $root.NodeData.Buffer.SetBytes($bytes.ToArray())
 $privateRef='$/03_night_city/towercontinued/world_support_wa3/group'+$spec.id+'_support'
 $hash=[WolvenKit.RED4.Types.NodeRef]::CalculateHash($privateRef)
 $depot='base\worlds\03_night_city\_compiled\default\quest_'+$hash.ToString('x16')+'.streamingsector'
 $out=Join-Path $source $depot;Write-Cr2wFile $file $out
 $read=ReadWorld $out
 $readBytes=$read.RootChunk.NodeData.Buffer.GetBytes()
 if((HashBytes $readBytes) -cne (HashBytes $bytes.ToArray()) -or $read.RootChunk.Nodes.Count -ne $spec.nodes-$spec.remove.Count){throw 'Opaque placement readback failed'}
 for($i=0;$i -lt $kept.Count;$i++){if((Json $read.RootChunk.Nodes[$kept[$i].private_node].Chunk) -cne $originalNodes[$kept[$i].native_node]){throw 'Retained node definition changed'}}
 if(@($read.RootChunk.Nodes|Where-Object {$_.Chunk.GetType().Name -eq 'worldPopulationSpawnerNode'}).Count){throw 'Private sector contains a population spawner'}
 $json=Join-Path $PSScriptRoot ('group'+$spec.id+'_readback_01.json');Export-Cr2wJson $read $json
 $descriptor=@($descriptors|Where-Object {$_.Data.DepotPath.ToString() -ceq $owner.resource})
 if($descriptor.Count -ne 1 -or $descriptor[0].QuestPrefabNodeRef.ToString() -cne $owner.resolved_prefab -or $descriptor[0].Category.ToString() -cne 'Quest' -or $descriptor[0].Variants.Count -ne 0){throw 'Native quest descriptor mismatch'}
 $d=$descriptor[0].DeepCopy();$d.QuestPrefabNodeRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($privateRef)
 $d.Data=[Activator]::CreateInstance($d.GetType().GetProperty('Data').PropertyType,[object[]]@([WolvenKit.RED4.Types.ResourcePath]::op_Implicit($depot)))
 [void]$nativeBlock.RootChunk.Descriptors.Add($d)
 $sha=(Get-FileHash -LiteralPath $out).Hash;$resources+=@{depot=$depot;sha256=$sha}
 $rows+=@{group=$spec.id;native_prefab=$owner.resolved_prefab;private_prefab=$privateRef;depot=$depot;node_ref_hash=$hash.ToString();native_raw=$hit.raw;native_sha256=$hit.sha256;private_sha256=$sha;native_nodes=$spec.nodes;private_nodes=$read.RootChunk.Nodes.Count;removed=$removed;retained=$kept;original_placement_sha256=HashBytes $raw;private_placement_sha256=HashBytes $readBytes;readback_json=$json;readback_json_sha256=(Get-FileHash -LiteralPath $json).Hash;native_descriptor=(Json $descriptor[0]|ConvertFrom-Json -Depth 30);private_descriptor=(Json $d|ConvertFrom-Json -Depth 30)}
}
$blockDepot='towercontinued\world_support_wa3\filtered_support.streamingblock';$blockOut=Join-Path $source $blockDepot
Write-Cr2wFile $nativeBlock $blockOut
$blockRead=ReadWorld $blockOut;if($blockRead.RootChunk.Descriptors.Count -ne 2){throw 'Private block readback failed'}
$blockJson=Join-Path $PSScriptRoot 'block_readback_01.json';Export-Cr2wJson $blockRead $blockJson
$resources+=@{depot=$blockDepot;sha256=(Get-FileHash -LiteralPath $blockOut).Hash}
$proof=@{status='PRIVATE_FILTERED_SUPPORT_SERIALIZED_PENDING_INDEPENDENT_VERIFICATION';rows=$rows;resources=$resources;streaming_blocks=@($blockDepot);sector_bindings=@($rows|ForEach-Object {@{depot=$_.depot;prefab_ref=$_.private_prefab;node_ref_hash=$_.node_ref_hash}});native_block=$blockHit.raw;native_block_sha256=$blockHit.sha256;block_readback_json=$blockJson;block_readback_json_sha256=(Get-FileHash -LiteralPath $blockJson).Hash;native_world_overrides=0;retained_workspot_ids_changed=0;game_writes=0;save_writes=0}
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'build_proof_01.json'),($proof|ConvertTo-Json -Depth 45)+"`n",[Text.UTF8Encoding]::new($false))
@{status=$proof.status;resources=$resources.Count;groups=@(160,161)}|ConvertTo-Json
