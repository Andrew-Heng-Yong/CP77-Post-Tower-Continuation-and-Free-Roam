$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
$wk=Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package'
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot $wk
$models=@'
using WolvenKit.RED4.Types;
namespace WA2EnvReadOnly02 {
 public class worldCookedBendedMeshNode : worldNode, IDynamicClass {[RED("className")] public CName ClassName {get;set;}="worldCookedBendedMeshNode";}
 public class worldCookedAcousticSectorNode : worldNode, IDynamicClass {[RED("className")] public CName ClassName {get;set;}="worldCookedAcousticSectorNode";}
 public class worldCookedGenericProxyMeshNode : worldNode, IDynamicClass {[RED("className")] public CName ClassName {get;set;}="worldCookedGenericProxyMeshNode";}
 public class worldCookedStaticDecalNode : worldNode, IDynamicClass {[RED("className")] public CName ClassName {get;set;}="worldCookedStaticDecalNode";}
 public class worldCookedStaticMeshNode : worldNode, IDynamicClass {[RED("className")] public CName ClassName {get;set;}="worldCookedStaticMeshNode";}
 public class worldCookedCableMeshNode : worldNode, IDynamicClass {[RED("className")] public CName ClassName {get;set;}="worldCookedCableMeshNode";}
 public class worldCookedFoliageDestructionNode : worldNode, IDynamicClass {[RED("className")] public CName ClassName {get;set;}="worldCookedFoliageDestructionNode";}
 public class worldCookedCollisionNode : worldNode, IDynamicClass {[RED("className")] public CName ClassName {get;set;}="worldCookedCollisionNode";}
}
'@
Add-Type -TypeDefinition $models -ReferencedAssemblies ([WolvenKit.RED4.Types.RedBaseClass].Assembly.Location)
$types=@{'worldCookedBendedMeshNode'=[WA2EnvReadOnly02.worldCookedBendedMeshNode];'worldCookedStaticMeshNode'=[WA2EnvReadOnly02.worldCookedStaticMeshNode];'worldCookedCollisionNode'=[WA2EnvReadOnly02.worldCookedCollisionNode];'worldCookedAcousticSectorNode'=[WA2EnvReadOnly02.worldCookedAcousticSectorNode];'worldCookedGenericProxyMeshNode'=[WA2EnvReadOnly02.worldCookedGenericProxyMeshNode];'worldCookedStaticDecalNode'=[WA2EnvReadOnly02.worldCookedStaticDecalNode]}
$types['worldCookedCableMeshNode']=[WA2EnvReadOnly02.worldCookedCableMeshNode]
$types['worldCookedFoliageDestructionNode']=[WA2EnvReadOnly02.worldCookedFoliageDestructionNode]
foreach($entry in $types.GetEnumerator()) {
 [void][WolvenKit.RED4.Types.RedReflection]::AddRedType($entry.Value)
 $property=[WolvenKit.RED4.Types.RedReflection]::GetNativePropertyInfo($entry.Value,'ClassName')
 $property.GetType().GetProperty('IsIgnored').SetValue($property,$true)
 [WolvenKit.RED4.Types.RedReflection]::GetTypes()[$entry.Key]=$entry.Value
}

$path=Join-Path $PSScriptRoot 'extract_01/ep1_1_nightcity_10971083935992963809.streamingsector'
$stream=[IO.File]::OpenRead($path)
$reader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($stream)
$reader.add_ParsingError([WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e) return ($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])})
$f=$null
if($reader.ReadFile([ref]$f,$true).ToString() -ne 'NoError'){throw 'Read failure'}
$stream.Dispose()
$f.RootChunk.GetType().GetProperties().Name|ConvertTo-Json
foreach($name in @('VariantIndices','VariantNodes')){
 if($f.RootChunk.PSObject.Properties.Name -contains $name){Write-Output $name;$f.RootChunk.$name|ForEach-Object ToString|ConvertTo-Json}
}
