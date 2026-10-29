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
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$out=Join-Path $PSScriptRoot 'registry_all_02';if(Test-Path -LiteralPath $out){throw 'Preserve evidence'}
[void][IO.Directory]::CreateDirectory($out)
$census=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'registry_fresh_01/report_01.json') -Raw|ConvertFrom-Json -Depth 10
$contracts=Get-Content -LiteralPath (Join-Path $PSScriptRoot '../native_review/action_contracts_02.json') -Raw|ConvertFrom-Json -Depth 100
$selectedContracts=@($contracts.contracts|Where-Object {$_.kind -ne 'existing_BA1_preserve'})
$ids=@($selectedContracts|ForEach-Object {$_.spawner_hashes}|Sort-Object -Unique)
$hashes=@{}
foreach($contract in $selectedContracts){
 foreach($ref in $contract.community_refs){$hashes[$ref]=[WolvenKit.RED4.Types.NodeRef]::CalculateHash($ref).ToString()}
 foreach($ref in $contract.dependencies|Where-Object {$_.type -eq 'NodeRef'}){$hashes[$ref.value]=[WolvenKit.RED4.Types.NodeRef]::CalculateHash($ref.value).ToString()}
}
$rows=@()
foreach($hit in $census.hits){
 if((Get-FileHash -LiteralPath $hit.raw).Hash -cne $hit.sha256){throw 'Registry binary changed'}
 $stream=[IO.File]::OpenRead($hit.raw)
 try{
  $reader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($stream)
  $reader.add_ParsingError([WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e) return ($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])})
  $parsed=$null;if($reader.ReadFile([ref]$parsed,$true).ToString() -cne 'NoError'){throw 'Registry decode failed'}
  $communities=@()
  foreach($n in $parsed.RootChunk.Nodes){if($n.Chunk.GetType().Name -ne 'worldCommunityRegistryNode'){continue};foreach($c in $n.Chunk.CommunitiesData){
   if($ids -contains $c.CommunityId.EntityId.Hash.ToString()){$communities+=([WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($c,[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())|ConvertFrom-Json -Depth 100)}
  }}
  if($communities.Count -ne $ids.Count){throw ('Missing selected communities '+$communities.Count+'/'+$ids.Count)}
  $refs=@()
  foreach($r in $parsed.RootChunk.NodeRefs){$ref=$r.ToString();$hash=[WolvenKit.RED4.Types.NodeRef]::CalculateHash($ref).ToString();if($ids -contains $hash){$refs+=@{reference=$ref;hash=$hash};$hashes[$ref]=$hash}}
  $json=Join-Path $out (([IO.Path]::GetFileNameWithoutExtension($hit.archive))+'.json')
  [IO.File]::WriteAllText($json,(@{communities=$communities;registry_refs=$refs}|ConvertTo-Json -Depth 100)+"`n",[Text.UTF8Encoding]::new($false))
  $rows+=@{archive=$hit.archive;raw=$hit.raw;raw_sha256=$hit.sha256;json=$json;json_sha256=(Get-FileHash -LiteralPath $json).Hash;communities=$communities.Count;refs=$refs.Count}
 }finally{$stream.Dispose()}
}
[IO.File]::WriteAllText((Join-Path $out 'report_01.json'),(@{status='FRESH_25_ACTION_COMMUNITIES_AND_NATIVE_HASH_BINDING';rows=$rows;hashes=$hashes;contract_sha256=(Get-FileHash -LiteralPath (Join-Path $PSScriptRoot '../native_review/action_contracts_02.json')).Hash;registry_census_sha256=(Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'registry_fresh_01/report_01.json')).Hash;game_writes=0;save_writes=0}|ConvertTo-Json -Depth 10)+"`n",[Text.UTF8Encoding]::new($false))
@{registries=$rows.Count;communities=$ids.Count;references=$hashes.Count}|ConvertTo-Json
