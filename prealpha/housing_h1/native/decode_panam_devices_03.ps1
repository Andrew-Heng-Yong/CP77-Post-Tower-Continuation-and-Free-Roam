# Read-only current world lookup. No binary writer or world-sector mutation.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
$wk=Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package'
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot $wk
$models=@'
using WolvenKit.RED4.Types;
namespace H1StashReadOnly {
 public class worldCookedAcousticSectorNode : worldNode, IDynamicClass {
  [RED("className")] public CName ClassName {get;set;}="worldCookedAcousticSectorNode";
 }
 public class worldCookedCollisionNode : worldNode, IDynamicClass {
  [RED("className")] public CName ClassName {get;set;}="worldCookedCollisionNode";
 }
 public class worldCookedFoliageDestructionNode : worldNode, IDynamicClass {
  [RED("className")] public CName ClassName {get;set;}="worldCookedFoliageDestructionNode";
 }
 public class worldCookedGenericProxyMeshNode : worldNode, IDynamicClass {
  [RED("className")] public CName ClassName {get;set;}="worldCookedGenericProxyMeshNode";
 }
 public class worldCookedStaticDecalNode : worldNode, IDynamicClass {
  [RED("className")] public CName ClassName {get;set;}="worldCookedStaticDecalNode";
 }
 public class worldCookedStaticMeshNode : worldNode, IDynamicClass {
  [RED("className")] public CName ClassName {get;set;}="worldCookedStaticMeshNode";
 }
}
'@
Add-Type -TypeDefinition $models -ReferencedAssemblies ([WolvenKit.RED4.Types.RedBaseClass].Assembly.Location)
$types=@{
 'worldCookedAcousticSectorNode'=[H1StashReadOnly.worldCookedAcousticSectorNode]
 'worldCookedCollisionNode'=[H1StashReadOnly.worldCookedCollisionNode]
 'worldCookedFoliageDestructionNode'=[H1StashReadOnly.worldCookedFoliageDestructionNode]
 'worldCookedGenericProxyMeshNode'=[H1StashReadOnly.worldCookedGenericProxyMeshNode]
 'worldCookedStaticDecalNode'=[H1StashReadOnly.worldCookedStaticDecalNode]
 'worldCookedStaticMeshNode'=[H1StashReadOnly.worldCookedStaticMeshNode]
}
foreach($entry in $types.GetEnumerator()) {
 if($null -ne [WolvenKit.RED4.Types.RedReflection]::GetTypes()[$entry.Key]){throw ('Unexpected existing type '+$entry.Key)}
 [void][WolvenKit.RED4.Types.RedReflection]::AddRedType($entry.Value)
 $property=[WolvenKit.RED4.Types.RedReflection]::GetNativePropertyInfo($entry.Value,'ClassName')
 $property.GetType().GetProperty('IsIgnored').SetValue($property,$true)
 if([WolvenKit.RED4.Types.RedReflection]::GetCSTypeFromRedType($entry.Key).Item1 -ne $entry.Value){throw ('Native reader registration failed '+$entry.Key)}
}
$root=Join-Path $ws 'research/housing_h1/purchase/panam_world_01'
$out=Join-Path $ws 'research/housing_h1/native/panam_device_decode_03'
if(Test-Path -LiteralPath $out){throw 'Immutable output exists'}
New-Item -ItemType Directory $out|Out-Null
$script:ignored=[Collections.Generic.List[object]]::new()
$handler=[WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e)
 if($e -isnot [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs]){return $false}
 $item=@{type=$e.GetType().FullName}
 foreach($p in $e.GetType().GetProperties()){
  $v=$p.GetValue($e)
  $item[$p.Name]=$(if($null -eq $v){$null}else{$v.ToString()})
 }
 $script:ignored.Add($item)
 return $true
}
$rows=[Collections.Generic.List[object]]::new()
$pins=@{}
foreach($name in @('basegame_3_nightcity_exterior_27_35_2_0.streamingsector','basegame_3_nightcity_exterior_53_-6_2_0.streamingsector','ep1_1_nightcity_exterior_27_35_2_0.streamingsector','ep1_1_nightcity_exterior_53_-6_2_0.streamingsector')){
 $raw=Get-Item -LiteralPath (Join-Path $root $name)
 $rel=[IO.Path]::GetRelativePath($ws,$raw.FullName).Replace('\','/')
 $row=@{raw=$rel;raw_sha256=(Get-FileHash -LiteralPath $raw.FullName).Hash;parsed=$false}
 $pins[$rel]=$row.raw_sha256
 $script:ignored.Clear()
 $stream=[IO.File]::OpenRead($raw.FullName)
 try {
  $reader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($stream);$file=$null
  if($reader.ReadFile([ref]$file,$false).ToString() -ne 'NoError'){throw 'Read failed'}
  $json=Join-Path $out ($raw.Name+'.json');Export-Cr2wJson $file $json
  $row.parsed=$true;$row.json=[IO.Path]::GetRelativePath($ws,$json).Replace('\','/');$row.json_sha256=(Get-FileHash -LiteralPath $json).Hash
  $pins[$row.json]=$row.json_sha256
 } catch {$row.error=$_.Exception.ToString()}
 finally {$stream.Dispose()}
 $row.ignored_default_fields=$script:ignored.ToArray()
 $rows.Add($row)
}
$scriptRel=[IO.Path]::GetRelativePath($ws,$PSCommandPath).Replace('\','/')
$pins[$scriptRel]=(Get-FileHash -LiteralPath $PSCommandPath).Hash
[IO.File]::WriteAllText((Join-Path $out 'report.json'),(@{
 status='READ_ONLY_TYPED_STASH_SOURCE_DECODE';rows=$rows.ToArray();source_pins=$pins;
 adapter=$scriptRel;adapter_sha256=$pins[$scriptRel];adapted_irrelevant_types=@($types.Keys);
 typed_target='worldDeviceNode remains the original WolvenKit model; no adapter changes it or its entity reference.';
 limits='Six otherwise unknown cooked world node classes use dynamic fields and worldNode base solely to read the containing sector. Buffer parsing disabled: nodeData, positions, instance index and opaque instance buffers are not evidence; target stash nodes have null instanceData. No parsing-error bypass is registered. No reconstructed binary world output, rendering, collision or live-device claim.';
 game_writes=0;binary_writes=0
}|ConvertTo-Json -Depth 15),[Text.UTF8Encoding]::new($false))
Write-Output ($rows|ConvertTo-Json -Depth 6)
