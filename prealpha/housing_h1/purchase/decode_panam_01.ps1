# Read-only adapter for irrelevant, otherwise unknown cooked render/collision nodes.
# Stash/device node and entity templates retain stock WolvenKit native models.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
$wk=Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package'
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot $wk
$models=@'
using WolvenKit.RED4.Types;
namespace H1ReadOnly {
 public class CookedMesh : worldNode, IDynamicClass {
  [RED("className")] public CName ClassName {get;set;}="worldCookedStaticMeshNode";
 }
 public class CookedCollision : worldNode, IDynamicClass {
  [RED("className")] public CName ClassName {get;set;}="worldCookedCollisionNode";
 }
}
'@
Add-Type -TypeDefinition $models -ReferencedAssemblies ([WolvenKit.RED4.Types.RedBaseClass].Assembly.Location)
$types=@{'worldCookedStaticMeshNode'=[H1ReadOnly.CookedMesh];'worldCookedCollisionNode'=[H1ReadOnly.CookedCollision]}
foreach($entry in $types.GetEnumerator()) {
 [void][WolvenKit.RED4.Types.RedReflection]::AddRedType($entry.Value)
 $property=[WolvenKit.RED4.Types.RedReflection]::GetNativePropertyInfo($entry.Value,'ClassName')
 $property.GetType().GetProperty('IsIgnored').SetValue($property,$true)
 [WolvenKit.RED4.Types.RedReflection]::GetTypes()[$entry.Key]=$entry.Value
}
$root=Join-Path $ws 'research/housing_h1/purchase/panam_world_01'
$out=Join-Path $ws 'research/housing_h1/purchase/panam_decode_01'
if(Test-Path -LiteralPath $out){throw 'Immutable output exists'}
New-Item -ItemType Directory $out|Out-Null
$handler=[WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e) return ($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])}
$rows=[Collections.Generic.List[object]]::new()
foreach($raw in Get-ChildItem -LiteralPath $root -Filter '*.streamingsector' -File) {
 $row=@{raw=[IO.Path]::GetRelativePath($ws,$raw.FullName).Replace('\','/');raw_sha256=(Get-FileHash -LiteralPath $raw.FullName).Hash;parsed=$false}
 $stream=[IO.File]::OpenRead($raw.FullName)
 try {
  $reader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($stream);$reader.add_ParsingError($handler);$file=$null
  if($reader.ReadFile([ref]$file,$true).ToString() -ne 'NoError'){throw 'Read failed'}
  $json=Join-Path $out ($raw.Name+'.json');Export-Cr2wJson $file $json
  $row.parsed=$true;$row.json=[IO.Path]::GetRelativePath($ws,$json).Replace('\','/');$row.json_sha256=(Get-FileHash -LiteralPath $json).Hash
 } catch {$row.error=$_.Exception.ToString()}
 finally {$stream.Dispose()}
 $rows.Add($row)
}
[IO.File]::WriteAllText((Join-Path $out 'report.json'),(@{status='READ_ONLY_TYPED_STASH_SOURCE_DECODE';rows=$rows.ToArray();adapter_sha256=(Get-FileHash $PSCommandPath).Hash;adapted_irrelevant_types=@($types.Keys);limits='Cooked mesh/collision fields are preserved dynamically for lookup only; no rebuilt world output or rendering claim.'}|ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
Write-Output ($rows|ConvertTo-Json -Depth 5)
