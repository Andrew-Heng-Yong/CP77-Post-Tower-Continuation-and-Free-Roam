param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly

$audit=Join-Path $WorkspaceRoot 'research\misty_viktor_world'
$sourceDepot='base\worlds\03_night_city\_compiled\default\exterior_-25_18_0_0.streamingsector'
$sourceHash='F362B1A319F4FBBC007BDDA5168933E3FA7BF89D27FB22A6F9262B513886F207'
$alias='$/03_night_city/#PTFRMV_OriginalPoliceLight01'
$out=Join-Path $WorkspaceRoot 'build\MistyOriginalLampAliasS1'
$source=Join-Path $out 'source'
$target=Join-Path $source $sourceDepot

$records=@(Get-Content (Join-Path $audit 'r7_lighting_sources.json') -Raw | ConvertFrom-Json | Where-Object {$_.Resource -eq $sourceDepot})
if($records.Count -ne 1 -or $records[0].Sha256 -ne $sourceHash){throw 'Official sector provenance drifted'}
$hash=[WolvenKit.Common.Services.HashService]::new();$hash.Load()
$archive=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($records[0].Archive,$hash,[ref]$archive).ToString() -ne 'NoError'){throw 'Cannot open official EP1 archive'}
$entries=@($archive.Files.Values | Where-Object {$_.Name -eq $sourceDepot})
if($entries.Count -ne 1){throw 'Official sector not unique in archive'}
$memory=[IO.MemoryStream]::new()
try{
 $entries[0].Extract($memory)
 if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($memory.ToArray())) -ne $sourceHash){throw 'Official sector bytes changed'}
 $memory.Position=0
 $reader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($memory)
 $handler=[WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e) return ($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])}
 $reader.add_ParsingError($handler);$file=$null
 if($reader.ReadFile([ref]$file,$true).ToString() -ne 'NoError'){throw 'Official sector decode failed'}
}finally{$memory.Dispose()}
$root=$file.RootChunk
if($root.Nodes.Count -ne 3941 -or $root.NodeData.Data.Count -ne 4534){throw 'Sector counts changed'}
$placement=$root.NodeData.Data[3901]
$light=$root.Nodes[3362].Chunk
if($placement.NodeIndex.ToString() -ne '3362' -or $light.GetType().Name -ne 'worldStaticLightNode' -or $light.DebugName.ToString() -ne '{L_Police_Tape_}01'){throw 'Singleton lamp identity changed'}
if($placement.QuestPrefabRefHash.ToString() -notin @('0','') -or $placement.UkHash1.ToString() -notin @('0','')){throw 'Singleton lamp already named'}
$aliasHash=[WolvenKit.RED4.Types.NodeRef]::CalculateHash($alias)
foreach($ref in $root.NodeRefs){
 if($ref.ToString() -eq $alias -or [WolvenKit.RED4.Types.NodeRef]::CalculateHash($ref.ToString()) -eq $aliasHash){throw 'NodeRef identity collision'}
}
$placement.QuestPrefabRefHash=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($alias)
[void]$root.NodeRefs.Add([WolvenKit.RED4.Types.NodeRef]::op_Implicit($alias))
Write-Cr2wFile $file $target
$readback=Read-Cr2wFile $target
Export-Cr2wJson $readback (Join-Path $audit 'original_lamp_alias_s1_sector.json')
if($readback.RootChunk.Nodes.Count -ne 3941 -or $readback.RootChunk.NodeData.Data.Count -ne 4534 -or $readback.RootChunk.NodeData.Data[3901].QuestPrefabRefHash.ToString() -ne $alias -or $readback.RootChunk.NodeRefs[$readback.RootChunk.NodeRefs.Count-1].ToString() -ne $alias){throw 'Alias readback mismatch'}
$manifest=[ordered]@{
 status='BUILT_SINGLETON_ORIGINAL_ALIAS_SOURCE_ONLY_NOT_INSTALLED'
 source_depot=$sourceDepot;source_sha256=$sourceHash;source_archive=$records[0].Archive
 target=$target;target_sha256=(Get-FileHash -LiteralPath $target).Hash
 exported_json=Join-Path $audit 'original_lamp_alias_s1_sector.json'
 alias=$alias;alias_hash=$aliasHash.ToString();placement_index=3901;node_index=3362
 expected_node_count=3941;expected_placement_count=4534;original_ref_count=$root.NodeRefs.Count-1
 allowed_changes=@('nodeData.Data[3901].QuestPrefabRefHash','nodeRefs append one entry')
 original_light_properties_changed=0;original_variants_changed=0;original_quest_writers_changed=0
 installed=$false;live_tested=$false
}
[IO.File]::WriteAllText((Join-Path $audit 'original_lamp_alias_s1_manifest.json'),($manifest|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
[pscustomobject]$manifest | Select-Object status,target_sha256,alias,alias_hash | ConvertTo-Json
