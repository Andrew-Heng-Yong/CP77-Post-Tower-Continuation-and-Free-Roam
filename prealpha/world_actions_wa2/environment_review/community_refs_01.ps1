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
$out=Join-Path $PSScriptRoot 'community_ref_proof_01.json';if(Test-Path -LiteralPath $out){throw 'Preserve evidence'}
$census=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'registry_fresh_01/report_01.json') -Raw|ConvertFrom-Json -Depth 10
$manifest=Get-Content -LiteralPath (Join-Path $ws 'prealpha/world_workspots_w2/manifest_03.json') -Raw|ConvertFrom-Json -Depth 30
$native=Get-Content -LiteralPath (Join-Path $PSScriptRoot '../native_review/census_raw_02.json') -Raw|ConvertFrom-Json -Depth 100
$refs=@{}
foreach($g in $manifest.groups|Where-Object {$_.id -in @(256,319)}){foreach($ref in $g.community_refs){$refs[$ref]=[WolvenKit.RED4.Types.NodeRef]::CalculateHash($ref).ToString();if($g.id -eq 319){$authored=$ref.Replace('/rancho_coronado/','/#rancho_coronado/');$refs[$authored]=[WolvenKit.RED4.Types.NodeRef]::CalculateHash($authored).ToString()}}}
foreach($g in $native.owners|Where-Object {$_.id -in @(256,319)}){foreach($phase in $g.phases){foreach($r in $phase.references|Where-Object {$_.type -eq 'NodeRef' -and $_.value -ne '#player'}){$refs[$r.value]=[WolvenKit.RED4.Types.NodeRef]::CalculateHash($r.value).ToString()}}}
$rows=@()
foreach($hit in $census.hits){
 if((Get-FileHash -LiteralPath $hit.raw).Hash -cne $hit.sha256){throw 'Registry binary changed'}
 $stream=[IO.File]::OpenRead($hit.raw)
 try{
  $reader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($stream);$reader.add_ParsingError([WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e) return ($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])})
  $parsed=$null;if($reader.ReadFile([ref]$parsed,$true).ToString() -cne 'NoError'){throw 'Registry decode failed'}
  $selected=@($parsed.RootChunk.NodeRefs|ForEach-Object ToString|Where-Object {$_ -match 'cs_std_arr_124|ce_std_rcr_146|ce_arr_std_113'})
  foreach($ref in $selected){$refs[$ref]=[WolvenKit.RED4.Types.NodeRef]::CalculateHash($ref).ToString()}
  $rows+=@{archive=$hit.archive;raw_sha256=$hit.sha256;registry_refs=$selected}
 }finally{$stream.Dispose()}
}
[IO.File]::WriteAllText($out,(@{status='FRESH_REGISTRY_COMMUNITY_AND_NATIVE_HASH_BINDING';rows=$rows;hashes=$refs;game_writes=0;save_writes=0}|ConvertTo-Json -Depth 10)+"`n",[Text.UTF8Encoding]::new($false))
@{registries=$rows.Count;refs=$refs.Count}|ConvertTo-Json
