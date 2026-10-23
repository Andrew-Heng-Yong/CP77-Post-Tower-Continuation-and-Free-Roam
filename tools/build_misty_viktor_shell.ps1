param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\misty_viktor_world'
$source=Join-Path $WorkspaceRoot 'archive\misty_viktor_world\source'
$out=Join-Path $WorkspaceRoot 'build\MistyViktorShell'
New-Item -ItemType Directory -Force -Path $audit,$source,$out | Out-Null
$plan=Get-Content -LiteralPath (Join-Path $audit 'geometry_selection.json') -Raw | ConvertFrom-Json
if($plan.status -ne 'INERT_GEOMETRY_SELECTION_ONLY_NOT_BUILT_OR_INSTALLED'){throw 'Unreviewed selection'}
$options=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new()
function CloneFile($file){
  $j=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize([WolvenKit.Common.Conversion.RedFileDto]::new($file,$false),$script:options)
  return [WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Deserialize([WolvenKit.Common.Conversion.RedFileDto],$j,$script:options).Data
}
function ReadWorld($path){
  $stream=[IO.File]::OpenRead($path)
  try{
    $reader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($stream)
    $handler=[WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e) return ($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])}
    $reader.add_ParsingError($handler);$file=$null
    if($reader.ReadFile([ref]$file,$true).ToString() -ne 'NoError'){throw 'World parse failure'}
    return $file
  }finally{$stream.Dispose()}
}
$blockPath=Join-Path $WorkspaceRoot 'research\phase2b_p4\staging_scan\ep1_1_nightcity\raw\base\worlds\03_night_city\_compiled\default\blocks\all.streamingblock'
$originalBlock=ReadWorld $blockPath
$block=CloneFile $originalBlock
$block.RootChunk.Descriptors.Clear()
$records=[Collections.Generic.List[object]]::new()
$resourcePaths=[Collections.Generic.List[string]]::new()
$privateName='PTFRMV_ZetatechShell'
$owner='$/03_night_city/c_watson/little_china/loc_mystic_mistys_ripperdoc_prefabH2DWJJI/#loc_mystic_mistys_ripperdoc_env'
$slot=0
foreach($row in $plan.source_ranges){
  $raw=Join-Path $WorkspaceRoot $row.raw_path
  if((Get-FileHash -LiteralPath $raw).Hash -ne $row.raw_sha256){throw 'Source changed'}
  $original=ReadWorld $raw;$file=CloneFile $original;$root=$file.RootChunk
  $oldNodes=@($root.Nodes);$oldData=@($root.NodeData.Data)
  $root.Nodes.Clear();$root.NodeData.Data.Clear()
  $ranges=[Activator]::CreateInstance($root.VariantIndices.GetType())
  [void]$ranges.Add([WolvenKit.RED4.Types.CInt32]::op_Implicit(0))
  $root.VariantIndices=$ranges
  $variantNodes=[Activator]::CreateInstance($root.VariantNodes.GetType())
  $emptyRange=[Activator]::CreateInstance($root.VariantNodes.GetType().GetGenericArguments()[0])
  [void]$variantNodes.Add($emptyRange)
  $root.VariantNodes=$variantNodes
  $indices=@{};$ordinal=0
  foreach($item in $row.selected){
    $old=[int]$item.node_index
    if($oldNodes[$old].Chunk.GetType().Name -ne $item.type){throw 'Node selection differs'}
    if(-not $indices.ContainsKey($old)){
      $indices[$old]=$root.Nodes.Count
      [void]$root.Nodes.Add($oldNodes[$old])
    }
    $data=$oldData[[int]$item.data_index]
    $data.NodeIndex=[WolvenKit.RED4.Types.CUInt16]::op_Implicit([uint16]$indices[$old])
    # New placement identity; do not copy the vanilla placement's identity.
    $data.Id=[uint64](710000000000000 + ($slot*10000) + $ordinal)
    $data.QuestPrefabRefHash=[WolvenKit.RED4.Types.NodeRef]::op_Implicit('')
    [void]$root.NodeData.Data.Add($data);$ordinal++
  }
  $depot="towercontinued\misty_viktor_world\shell_$slot.streamingsector"
  if($root.VariantIndices.Count -ne 1){throw 'Private range missing before serialization'}
  Write-Cr2wFile $file (Join-Path $source $depot)
  $readback=ReadWorld (Join-Path $source $depot)
  Export-Cr2wJson $readback (Join-Path $audit "shell_$slot.json")
  $rowBlockPath=Join-Path $WorkspaceRoot ($row.source_block.Replace('\json\','\raw\') -replace '\.json$','')
  $rowBlock=ReadWorld $rowBlockPath
  $descriptor=$rowBlock.RootChunk.Descriptors[[int]$row.descriptor_index].DeepCopy()
  $sourceVariants=@($descriptor.Variants | Where-Object {$_.Name.ToString() -eq 'q307_zetatech' -and $_.RangeIndex.ToString() -eq $row.variant.rangeIndex.ToString()})
  if($sourceVariants.Count -ne 1){throw 'Source descriptor variant is not unique'}
  $variant=$sourceVariants[0].DeepCopy()
  $descriptor.Variants.Clear()
  $variant.Name=[WolvenKit.RED4.Types.CName]::op_Implicit($privateName)
  $variant.NodeRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($owner)
  $variant.EnabledByDefault=$false
  $variant.RangeIndex=[WolvenKit.RED4.Types.CUInt32]::op_Implicit(0)
  $variant.ParentVariantID=[WolvenKit.RED4.Types.CUInt32]::op_Implicit(0)
  $variant.VariantId=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]3917072701)
  [void]$descriptor.Variants.Add($variant)
  $descriptor.NumNodeRanges=[WolvenKit.RED4.Types.CUInt32]::op_Implicit(1)
  $property=$descriptor.GetType().GetProperty('Data')
  $descriptor.Data=[Activator]::CreateInstance($property.PropertyType,[object[]]@([WolvenKit.RED4.Types.ResourcePath]::op_Implicit($depot)))
  [void]$block.RootChunk.Descriptors.Add($descriptor)
  $resourcePaths.Add($depot)
  $records.Add([pscustomobject]@{depot=$depot;source=$row.raw_path;selected=@($row.selected);nodes=$root.Nodes.Count;instances=$root.NodeData.Data.Count})
  $slot++
}
$blockDepot='towercontinued\misty_viktor_world\shell.streamingblock'
Write-Cr2wFile $block (Join-Path $source $blockDepot)
Export-Cr2wJson (ReadWorld (Join-Path $source $blockDepot)) (Join-Path $audit 'shell_block.json')
$resourcePaths.Add($blockDepot)
# Deliberately do not install/register this geometry-only offline artifact.
# A guarded native variant controller and rollback must pass separately first.
$hash=[WolvenKit.Common.Services.HashService]::new();$hash.Load()
$archive=Join-Path $out 'TowerContinued_MistyViktorShell.archive'
$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hash,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hash,[ref]$packed).ToString() -ne 'NoError'){throw 'Archive reopen failed'}
if(@(Compare-Object @($resourcePaths|Sort-Object) @($packed.Files.Values|ForEach-Object {$_.Name}|Sort-Object)).Count){throw 'Packed scope mismatch'}
$manifest=[ordered]@{status='OFFLINE_GEOMETRY_ARTIFACT_ONLY_NOT_REGISTERED_OR_INSTALLED';archive=$archive;sha256=(Get-FileHash $archive).Hash;resources=@($resourcePaths);sectors=@($records);private_variant=$privateName;variant_owner=$owner;vanilla_variant_writes=@();entities=0;actors=0;live_tested=$false;pending=@('roundtrip identity/collision tests','native guarded controller','additive registration','safe live access')}
[IO.File]::WriteAllText((Join-Path $audit 'shell_manifest.json'),($manifest|ConvertTo-Json -Depth 8))
[pscustomobject]@{status=$manifest.status;sha256=$manifest.sha256;resources=$manifest.resources}|ConvertTo-Json -Depth 3
