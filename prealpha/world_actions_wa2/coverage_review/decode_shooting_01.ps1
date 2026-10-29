$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
$wk=Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package'
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot $wk
$models=@'
using WolvenKit.RED4.Types;
namespace BAEnvReadOnly01 {
 public class worldCookedBendedMeshNode : worldNode, IDynamicClass {[RED("className")] public CName ClassName {get;set;}="worldCookedBendedMeshNode";}
 public class worldCookedAcousticSectorNode : worldNode, IDynamicClass {[RED("className")] public CName ClassName {get;set;}="worldCookedAcousticSectorNode";}
 public class worldCookedGenericProxyMeshNode : worldNode, IDynamicClass {[RED("className")] public CName ClassName {get;set;}="worldCookedGenericProxyMeshNode";}
 public class worldCookedStaticDecalNode : worldNode, IDynamicClass {[RED("className")] public CName ClassName {get;set;}="worldCookedStaticDecalNode";}
 public class worldCookedStaticMeshNode : worldNode, IDynamicClass {[RED("className")] public CName ClassName {get;set;}="worldCookedStaticMeshNode";}
 public class worldCookedCollisionNode : worldNode, IDynamicClass {[RED("className")] public CName ClassName {get;set;}="worldCookedCollisionNode";}
}
'@
Add-Type -TypeDefinition $models -ReferencedAssemblies ([WolvenKit.RED4.Types.RedBaseClass].Assembly.Location)
$types=@{'worldCookedBendedMeshNode'=[BAEnvReadOnly01.worldCookedBendedMeshNode];'worldCookedStaticMeshNode'=[BAEnvReadOnly01.worldCookedStaticMeshNode];'worldCookedCollisionNode'=[BAEnvReadOnly01.worldCookedCollisionNode];'worldCookedAcousticSectorNode'=[BAEnvReadOnly01.worldCookedAcousticSectorNode];'worldCookedGenericProxyMeshNode'=[BAEnvReadOnly01.worldCookedGenericProxyMeshNode];'worldCookedStaticDecalNode'=[BAEnvReadOnly01.worldCookedStaticDecalNode]}
foreach($entry in $types.GetEnumerator()) {
 [void][WolvenKit.RED4.Types.RedReflection]::AddRedType($entry.Value)
 $property=[WolvenKit.RED4.Types.RedReflection]::GetNativePropertyInfo($entry.Value,'ClassName')
 $property.GetType().GetProperty('IsIgnored').SetValue($property,$true)
 [WolvenKit.RED4.Types.RedReflection]::GetTypes()[$entry.Key]=$entry.Value
}
$out=Join-Path $PSScriptRoot 'shooting_decode_01'
if(Test-Path -LiteralPath $out){throw 'Preserve evidence'}
[void][IO.Directory]::CreateDirectory($out)
$handler=[WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e) return ($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])}
$rows=[Collections.Generic.List[object]]::new()
foreach($rawFile in (Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot 'shooting_sources_01') -Filter 'exterior_*.streamingsector' -Recurse)) {
 $raw=$rawFile.FullName;$row=@{raw=$raw;raw_sha256=(Get-FileHash -LiteralPath $raw).Hash;parsed=$false}
 $stream=[IO.File]::OpenRead($raw)
 try {
  $reader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($stream);$reader.add_ParsingError($handler);$file=$null
  if($reader.ReadFile([ref]$file,$true).ToString() -ne 'NoError'){throw 'Decode failed'}
  $selected=[Collections.Generic.List[object]]::new();$ni=0
  foreach($h in $file.RootChunk.Nodes){
   $node=$h.Chunk;$type=$node.GetType().Name
   if($type -match 'Entity|Device|Security|Community|Trigger|Area'){
    try{$definition=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($node,[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())|ConvertFrom-Json -Depth 100;$selected.Add(@{node=$ni;type=$type;definition=$definition})}catch{$selected.Add(@{node=$ni;type=$type;error=$_.Exception.Message})}
   };$ni++
  }
  [IO.File]::WriteAllText((Join-Path $out ($rawFile.Directory.Name+'_'+$rawFile.Name+'.nodes.json')),(@{nodes=@($selected.ToArray());refs=@($file.RootChunk.NodeRefs|ForEach-Object ToString)}|ConvertTo-Json -Depth 100)+"`n",[Text.UTF8Encoding]::new($false))
  $rawSetups=$file.RootChunk.NodeData.Buffer.GetBytes()
  if($rawSetups.Length -ne $file.RootChunk.NodeData.Data.Count*0x90){throw 'Unexpected node setup stride'}
  $placements=[Collections.Generic.List[object]]::new();$i=0
  foreach($d in $file.RootChunk.NodeData.Data){
   $idx=[int]([BitConverter]::ToUInt64($rawSetups,$i*0x90+0x70) -band 0x7FFFF);$n=if($idx -lt $file.RootChunk.Nodes.Count){$file.RootChunk.Nodes[$idx].Chunk}else{$null}
   $placements.Add(@{datum=$i;id=$d.Id.ToString();node=$idx;type=if($n){$n.GetType().Name}else{'INVALID_INDEX'};position=@([double]$d.Position.X.ToString(),[double]$d.Position.Y.ToString(),[double]$d.Position.Z.ToString());quest_ref=$d.QuestPrefabRefHash.ToString();uk_ref=$d.UkHash1.ToString()});$i++
  }
  @{placements=$placements.ToArray();nodes=$file.RootChunk.Nodes.Count;node_refs=@($file.RootChunk.NodeRefs|ForEach-Object ToString)}|ConvertTo-Json -Depth 15|Set-Content -LiteralPath (Join-Path $out ($rawFile.Directory.Name+'_'+$rawFile.Name+'.placements.json')) -Encoding utf8NoBOM
  $row.parsed=$true;$row.nodes=$file.RootChunk.Nodes.Count;$row.placements=$file.RootChunk.NodeData.Data.Count
 }catch{$row.error=$_.Exception.ToString()}finally{$stream.Dispose()}
 $rows.Add($row)
 if(($rows.Count % 10) -eq 0){Write-Output "Decoded $($rows.Count) nearby sectors"}
}
[IO.File]::WriteAllText((Join-Path $out 'report_01.json'),(@{rows=@($rows.ToArray());status='READ_ONLY_SECTOR_DECODE';game_writes=0;save_writes=0}|ConvertTo-Json -Depth 12)+"`n",[Text.UTF8Encoding]::new($false))
@{count=$rows.Count;parsed=@($rows|Where-Object parsed).Count;failed=@($rows|Where-Object {$_.parsed -eq $false}).Count}|ConvertTo-Json
