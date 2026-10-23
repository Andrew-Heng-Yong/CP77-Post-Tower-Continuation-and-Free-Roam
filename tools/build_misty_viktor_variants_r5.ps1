param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\misty_viktor_world'
$prior=Get-Content (Join-Path $audit 'cleanup_r4_manifest.json') -Raw|ConvertFrom-Json
$out=Join-Path $WorkspaceRoot 'build\MistyViktorVariantsR5'
$source=Join-Path $out 'source'
New-Item -ItemType Directory -Force $source|Out-Null
foreach($path in $prior.resources){
 $src=Join-Path $WorkspaceRoot ('build\MistyViktorCleanupR4\source\'+$path)
 $dst=Join-Path $source $path
 New-Item -ItemType Directory -Force (Split-Path -Parent $dst)|Out-Null
 Copy-Item -LiteralPath $src -Destination $dst -Force
}
function ReadWorld($path){
 $stream=[IO.File]::OpenRead($path)
 try{
  $reader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($stream)
  $handler=[WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e) return ($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])}
  $reader.add_ParsingError($handler);$file=$null
  if($reader.ReadFile([ref]$file,$true).ToString() -ne 'NoError'){throw "World parse failure: $path"}
  return $file
 }finally{$stream.Dispose()}
}
$sectorNames=@($prior.resources|Where-Object {$_ -match 'towercontinued\\misty_viktor_world\\(?:shell|street)_\d+\.streamingsector$'})
if($sectorNames.Count -ne 14){throw "Expected 14 private sectors, found $($sectorNames.Count)"}
foreach($depot in $sectorNames){
 $path=Join-Path $source $depot;$file=ReadWorld $path;$root=$file.RootChunk
 if($root.VariantIndices.Count -ne 1 -or $root.VariantIndices[0].ToString() -ne '0' -or $root.VariantNodes.Count -gt 1){throw "R4 private range drifted: $depot"}
 $ranges=[Activator]::CreateInstance($root.VariantIndices.GetType())
 [void]$ranges.Add([WolvenKit.RED4.Types.CInt32]::op_Implicit(0))
 [void]$ranges.Add([WolvenKit.RED4.Types.CInt32]::op_Implicit(0))
 $root.VariantIndices=$ranges
 if($root.VariantNodes.Count -eq 0){[void]$root.VariantNodes.Add([Activator]::CreateInstance($root.VariantNodes.GetType().GetGenericArguments()[0]))}
 Write-Cr2wFile $file $path
 $readback=ReadWorld $path
 if($readback.RootChunk.VariantIndices.Count -ne 2 -or $readback.RootChunk.VariantNodes.Count -lt 1 -or $readback.RootChunk.VariantNodes.Count -gt 2){throw "Private variant range serialization failed: $depot indices=$($readback.RootChunk.VariantIndices.Count) nodes=$($readback.RootChunk.VariantNodes.Count)"}
 Export-Cr2wJson (ReadWorld $path) (Join-Path $audit ("variants_r5_"+[IO.Path]::GetFileNameWithoutExtension($depot)+'.json'))
}
$blocks=@('towercontinued\misty_viktor_world\shell.streamingblock','towercontinued\misty_viktor_world\street.streamingblock')
foreach($depot in $blocks){
 $path=Join-Path $source $depot;$file=ReadWorld $path;$root=$file.RootChunk
 foreach($descriptor in $root.Descriptors){
  if($descriptor.NumNodeRanges.ToString() -ne '1' -or $descriptor.Variants.Count -ne 1 -or $descriptor.Variants[0].RangeIndex.ToString() -ne '0'){throw "R4 private descriptor drifted: $depot"}
  $descriptor.NumNodeRanges=[WolvenKit.RED4.Types.CUInt32]::op_Implicit(2)
  $descriptor.Variants[0].RangeIndex=[WolvenKit.RED4.Types.CUInt32]::op_Implicit(1)
 }
 Write-Cr2wFile $file $path
 Export-Cr2wJson (ReadWorld $path) (Join-Path $audit ("variants_r5_"+[IO.Path]::GetFileNameWithoutExtension($depot)+'.json'))
}
$phaseDepot='towercontinued\misty_viktor_world\shell_optin.questphase'
$phase=Read-Cr2wFile (Join-Path $source $phaseDepot)
$graph=$phase.RootChunk.Graph.Chunk
if($graph.Nodes.Count -ne 22){throw 'R4 native graph drifted'}
$revision=(Get-QuestNode $graph 18).Type.Chunk
if($revision.FactName.ToString() -ne 'PTFRMV_Revision' -or $revision.Value.ToString() -ne '4'){throw 'R4 revision drifted'}
$revision.Value=[int32]5
Write-Cr2wFile $phase (Join-Path $source $phaseDepot)
Export-Cr2wJson (Read-Cr2wFile (Join-Path $source $phaseDepot)) (Join-Path $audit 'variants_r5_phase.json')
$archive=Join-Path $out 'TowerContinued_MistyViktorShellOptIn.archive'
$hash=[WolvenKit.Common.Services.HashService]::new();$hash.Load()
$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hash,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'R5 archive pack failed'}}finally{$stream.Dispose()}
Copy-Item -LiteralPath ($prior.archive+'.xl') -Destination ($archive+'.xl') -Force
$packed=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hash,[ref]$packed).ToString() -ne 'NoError'){throw 'R5 archive reopen failed'}
if(@(Compare-Object @($prior.resources|Sort-Object) @($packed.Files.Values|ForEach-Object {$_.Name}|Sort-Object)).Count){throw 'R5 packed scope mismatch'}
$manifest=[ordered]@{status='BUILT_R5_PRIVATE_VARIANT_FIX_NOT_INSTALLED_OR_LIVE';archive=$archive;sha256=(Get-FileHash $archive).Hash;xl_sha256=(Get-FileHash ($archive+'.xl')).Hash;resources=$prior.resources;private_sector_count=$sectorNames.Count;private_block_count=$blocks.Count;default_range_node_count=0;controlled_range_index=1;street_passive_placements_retained=764;original_hide_action_retained=$true;police_filter_retained=$true;guards=$prior.guards;actors=0;native_scene_starts=0;story_fact_writes=0;live_tested=$false}
[IO.File]::WriteAllText((Join-Path $audit 'variants_r5_manifest.json'),($manifest|ConvertTo-Json -Depth 6))
[pscustomobject]@{status=$manifest.status;sha256=$manifest.sha256;private_sectors=$sectorNames.Count;resources=$prior.resources.Count}|ConvertTo-Json
