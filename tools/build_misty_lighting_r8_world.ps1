param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\misty_viktor_world'
$sourceDepot='base\worlds\03_night_city\_compiled\default\exterior_-25_18_0_0.streamingsector'
$sourceHash='F362B1A319F4FBBC007BDDA5168933E3FA7BF89D27FB22A6F9262B513886F207'
$out=Join-Path $WorkspaceRoot 'build\MistyLightingR8'
$source=Join-Path $out 'source'
$privateSector='towercontinued\misty_viktor_lighting_r8\cold.streamingsector'
$privateBlock='towercontinued\misty_viktor_lighting_r8\cold.streamingblock'
$variantName='PTFRMV_R8_Cold'
$variantOwner='$/03_night_city/c_watson/little_china/wlc_02/#wlc_02_b_env'
$variantId=[uint32]3980092802
$originalTargets=@(
 @{datum=3901;node=3362;type='worldStaticLightNode';group='police'},
 @{datum=3902;node=3363;type='worldStaticLightNode';group='police'},
 @{datum=3903;node=3364;type='worldStaticLightNode';group='police'},
 @{datum=3904;node=3365;type='worldStaticLightNode';group='police'},
 @{datum=3905;node=3366;type='worldStaticLightNode';group='police'},
 @{datum=3906;node=3367;type='worldStaticLightNode';group='police'},
 @{datum=3907;node=3368;type='worldStaticLightNode';group='police'},
 @{datum=3921;node=3382;type='worldStaticLightNode';group='pink'},
 @{datum=3923;node=3384;type='worldStaticLightNode';group='pink'},
 @{datum=3943;node=3404;type='worldStaticLightNode';group='pink'},
 @{datum=3945;node=3406;type='worldStaticMeshNode';group='pink'},
 @{datum=3946;node=3407;type='worldStaticMeshNode';group='pink'}
)
$coldTargets=@(
 @{datum=3542;node=3113;type='worldStaticLightNode'},
 @{datum=3543;node=3114;type='worldStaticLightNode'},
 @{datum=3544;node=3115;type='worldStaticLightNode'},
 @{datum=3547;node=3118;type='worldStaticMeshNode'},
 @{datum=3548;node=3119;type='worldStaticMeshNode'}
)

# Read the pinned official source, not the previously installed S1 override.
$record=@(Get-Content (Join-Path $audit 'r7_lighting_sources.json') -Raw|ConvertFrom-Json|Where-Object {$_.Resource -eq $sourceDepot})
if($record.Count -ne 1 -or $record[0].Sha256 -ne $sourceHash){throw 'Original sector provenance changed'}
$hash=[WolvenKit.Common.Services.HashService]::new();$hash.Load();$archive=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($record[0].Archive,$hash,[ref]$archive).ToString() -ne 'NoError'){throw 'Cannot open official archive'}
$entry=@($archive.Files.Values|Where-Object {$_.Name -eq $sourceDepot})
if($entry.Count -ne 1){throw 'Original sector not unique'}
$memory=[IO.MemoryStream]::new()
try{
 $entry[0].Extract($memory)
 if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($memory.ToArray())) -ne $sourceHash){throw 'Official sector bytes changed'}
 $memory.Position=0
 $reader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($memory)
 $handler=[WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e) return ($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])}
 $reader.add_ParsingError($handler);$file=$null
 if($reader.ReadFile([ref]$file,$true).ToString() -ne 'NoError'){throw 'Official sector decode failed'}
}finally{$memory.Dispose()}
$root=$file.RootChunk
if($root.Nodes.Count -ne 3941 -or $root.NodeData.Data.Count -ne 4534){throw 'Official sector counts changed'}

$seen=[Collections.Generic.HashSet[uint64]]::new()
foreach($ref in $root.NodeRefs){[void]$seen.Add([WolvenKit.RED4.Types.NodeRef]::CalculateHash($ref.ToString()))}
$originalManifest=[Collections.Generic.List[object]]::new()
foreach($target in $originalTargets){
 $data=$root.NodeData.Data[$target.datum];$node=$root.Nodes[$target.node].Chunk
 if($data.NodeIndex.ToString() -ne "$($target.node)" -or $node.GetType().Name -ne $target.type){throw ('Original target identity changed: '+$target.datum)}
 if($data.QuestPrefabRefHash.ToString() -notin @('0','') -or $data.UkHash1.ToString() -notin @('0','')){throw ('Original target already referenced: '+$target.datum)}
 $alias="$/03_night_city/#PTFRMV_R8_Original_$($target.datum)"
 $aliasHash=[WolvenKit.RED4.Types.NodeRef]::CalculateHash($alias)
 if(-not $seen.Add($aliasHash)){throw ('Original alias collision: '+$alias)}
 $data.QuestPrefabRefHash=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($alias)
 [void]$root.NodeRefs.Add([WolvenKit.RED4.Types.NodeRef]::op_Implicit($alias))
 $originalManifest.Add([ordered]@{datum=$target.datum;node=$target.node;type=$target.type;group=$target.group;alias=$alias;alias_hash=$aliasHash.ToString()})
}
$originalPath=Join-Path $source $sourceDepot
Write-Cr2wFile $file $originalPath
$readback=Read-Cr2wFile $originalPath
Export-Cr2wJson $readback (Join-Path $audit 'lighting_r8_original_sector.json')
if($readback.RootChunk.Nodes.Count -ne 3941 -or $readback.RootChunk.NodeData.Data.Count -ne 4534 -or $readback.RootChunk.NodeRefs.Count -ne $root.NodeRefs.Count){throw 'Original sector readback failed'}

# Clone the five exact vanilla Tower Cold nodes into a private default-off
# sector. Their transforms, colors, materials and appearances remain authored.
$templateSector=Join-Path $WorkspaceRoot 'build\MistyViktorLightPOCWorld\source\towercontinued\misty_viktor_light_poc\light_poc.streamingsector'
$private=Read-Cr2wFile $templateSector;$privateRoot=$private.RootChunk
$privateRoot.Nodes.Clear();$privateRoot.NodeData.Data.Clear();$privateRoot.NodeRefs.Clear()
$coldManifest=[Collections.Generic.List[object]]::new()
for($i=0;$i -lt $coldTargets.Count;$i++){
 $target=$coldTargets[$i];$data=$root.NodeData.Data[$target.datum].DeepCopy();$node=$root.Nodes[$target.node].DeepCopy()
 if($data.NodeIndex.ToString() -ne "$($target.node)" -or $node.Chunk.GetType().Name -ne $target.type){throw ('Cold target identity changed: '+$target.datum)}
 if($data.QuestPrefabRefHash.ToString() -notin @('0','') -or $data.UkHash1.ToString() -notin @('0','')){throw ('Cold source already referenced: '+$target.datum)}
 $alias="$/03_night_city/#PTFRMV_R8_Cold_$($target.datum)"
 $aliasHash=[WolvenKit.RED4.Types.NodeRef]::CalculateHash($alias)
 if(-not $seen.Add($aliasHash)){throw ('Cold alias collision: '+$alias)}
 $node.Chunk.SourcePrefabHash=[WolvenKit.RED4.Types.CUInt64]::op_Implicit([uint64]0)
 $node.Chunk.DebugName=[WolvenKit.RED4.Types.CName]::op_Implicit("PTFRMV_R8_Cold_$($target.datum)")
 $data.Id=[uint64](750000000008100+$i)
 $data.NodeIndex=[WolvenKit.RED4.Types.CUInt16]::op_Implicit([uint16]$i)
 $data.QuestPrefabRefHash=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($alias)
 $data.UkHash1=[WolvenKit.RED4.Types.NodeRef]::op_Implicit('')
 [void]$privateRoot.Nodes.Add($node);[void]$privateRoot.NodeData.Data.Add($data)
 [void]$privateRoot.NodeRefs.Add([WolvenKit.RED4.Types.NodeRef]::op_Implicit($alias))
 $coldManifest.Add([ordered]@{datum=$target.datum;node=$target.node;type=$target.type;alias=$alias;alias_hash=$aliasHash.ToString();position=@([double]$data.Position.X.ToString(),[double]$data.Position.Y.ToString(),[double]$data.Position.Z.ToString())})
}
if($privateRoot.VariantIndices.Count -ne 2 -or $privateRoot.VariantIndices[0].ToString() -ne '0' -or $privateRoot.VariantIndices[1].ToString() -ne '0'){throw 'Private variant range template changed'}
$privatePath=Join-Path $source $privateSector
Write-Cr2wFile $private $privatePath
$privateReadback=Read-Cr2wFile $privatePath
Export-Cr2wJson $privateReadback (Join-Path $audit 'lighting_r8_cold_sector.json')
if($privateReadback.RootChunk.Nodes.Count -ne 5 -or $privateReadback.RootChunk.NodeData.Data.Count -ne 5 -or $privateReadback.RootChunk.NodeRefs.Count -ne 5){throw 'Private Cold readback scope failed'}

$templateBlock=Join-Path $WorkspaceRoot 'build\MistyViktorLightPOCWorld\source\towercontinued\misty_viktor_light_poc\light_poc.streamingblock'
$block=Read-Cr2wFile $templateBlock;$descriptor=$block.RootChunk.Descriptors[0]
if($block.RootChunk.Descriptors.Count -ne 1 -or $descriptor.Variants.Count -ne 1 -or $descriptor.Variants[0].EnabledByDefault.ToString() -ne 'False'){throw 'Private block template changed'}
$variant=$descriptor.Variants[0]
$variant.Name=[WolvenKit.RED4.Types.CName]::op_Implicit($variantName)
$variant.NodeRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($variantOwner)
$variant.VariantId=[WolvenKit.RED4.Types.CUInt32]::op_Implicit($variantId)
$descriptor.Data=[Activator]::CreateInstance($descriptor.GetType().GetProperty('Data').PropertyType,[object[]]@([WolvenKit.RED4.Types.ResourcePath]::op_Implicit($privateSector)))
foreach($item in $coldManifest){for($i=0;$i -lt 3;$i++){
 $axis=@('X','Y','Z')[$i]
 if($item.position[$i] -lt [double]$descriptor.StreamingBox.Min.$axis.ToString() -or $item.position[$i] -gt [double]$descriptor.StreamingBox.Max.$axis.ToString()){throw ('Cold target outside private descriptor: '+$item.datum)}
}}
$blockPath=Join-Path $source $privateBlock
Write-Cr2wFile $block $blockPath
$blockReadback=Read-Cr2wFile $blockPath
Export-Cr2wJson $blockReadback (Join-Path $audit 'lighting_r8_cold_block.json')
if($blockReadback.RootChunk.Descriptors.Count -ne 1 -or $blockReadback.RootChunk.Descriptors[0].Variants[0].Name.ToString() -ne $variantName -or $blockReadback.RootChunk.Descriptors[0].Variants[0].EnabledByDefault.ToString() -ne 'False'){throw 'Private Cold block readback failed'}
$manifest=[ordered]@{
 status='BUILT_R8_WORLD_SOURCE_NOT_INSTALLED';source_sha256=$sourceHash;source_archive=$record[0].Archive
 original_depot=$sourceDepot;original_path=$originalPath;original_sha256=(Get-FileHash $originalPath).Hash
 original_targets=@($originalManifest);original_alias_count=12;original_properties_changed=0;original_variant_writes=0
 cold_sector_depot=$privateSector;cold_sector_path=$privatePath;cold_sector_sha256=(Get-FileHash $privatePath).Hash
 cold_block_depot=$privateBlock;cold_block_path=$blockPath;cold_block_sha256=(Get-FileHash $blockPath).Hash
 cold_targets=@($coldManifest);cold_clone_count=5;private_variant=$variantName;private_variant_owner=$variantOwner;private_variant_id=$variantId;private_variant_default_off=$true
 original_scene_starts=0;story_fact_writes=0;gameplay_commands_executed=0;installed=$false;live_tested=$false
}
[IO.File]::WriteAllText((Join-Path $audit 'lighting_r8_world_manifest.json'),($manifest|ConvertTo-Json -Depth 20),[Text.UTF8Encoding]::new($false))
[pscustomobject]$manifest|Select-Object status,original_alias_count,cold_clone_count,original_sha256,cold_sector_sha256,cold_block_sha256|ConvertTo-Json
