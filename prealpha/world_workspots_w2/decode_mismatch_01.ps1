# Read-only archive extraction of 31 exact authored Rancho Coronado prefabs.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$models=@'
using WolvenKit.RED4.Types;
namespace W2ReadOnly01 {
 public class worldCookedBendedMeshNode : worldNode, IDynamicClass {[RED("className")] public CName ClassName {get;set;}="worldCookedBendedMeshNode";}
 public class worldCookedAcousticSectorNode : worldNode, IDynamicClass {[RED("className")] public CName ClassName {get;set;}="worldCookedAcousticSectorNode";}
 public class worldCookedGenericProxyMeshNode : worldNode, IDynamicClass {[RED("className")] public CName ClassName {get;set;}="worldCookedGenericProxyMeshNode";}
 public class worldCookedStaticDecalNode : worldNode, IDynamicClass {[RED("className")] public CName ClassName {get;set;}="worldCookedStaticDecalNode";}
 public class worldCookedStaticMeshNode : worldNode, IDynamicClass {[RED("className")] public CName ClassName {get;set;}="worldCookedStaticMeshNode";}
 public class worldCookedCollisionNode : worldNode, IDynamicClass {[RED("className")] public CName ClassName {get;set;}="worldCookedCollisionNode";}
}
'@
Add-Type -TypeDefinition $models -ReferencedAssemblies ([WolvenKit.RED4.Types.RedBaseClass].Assembly.Location)
$types=@{'worldCookedBendedMeshNode'=[W2ReadOnly01.worldCookedBendedMeshNode];'worldCookedStaticMeshNode'=[W2ReadOnly01.worldCookedStaticMeshNode];'worldCookedCollisionNode'=[W2ReadOnly01.worldCookedCollisionNode];'worldCookedAcousticSectorNode'=[W2ReadOnly01.worldCookedAcousticSectorNode];'worldCookedGenericProxyMeshNode'=[W2ReadOnly01.worldCookedGenericProxyMeshNode];'worldCookedStaticDecalNode'=[W2ReadOnly01.worldCookedStaticDecalNode]}
foreach($e in $types.GetEnumerator()){
 [void][WolvenKit.RED4.Types.RedReflection]::AddRedType($e.Value)
 $p=[WolvenKit.RED4.Types.RedReflection]::GetNativePropertyInfo($e.Value,'ClassName');$p.GetType().GetProperty('IsIgnored').SetValue($p,$true)
 [WolvenKit.RED4.Types.RedReflection]::GetTypes()[$e.Key]=$e.Value
}
$inputPath=Join-Path $PSScriptRoot 'mismatch_resolution_01.json'
$out=Join-Path $PSScriptRoot 'decoded_mismatch_02'
if(Test-Path -LiteralPath $out){throw 'Preserve evidence; use successor'}
[void][IO.Directory]::CreateDirectory($out)
$data=Get-Content -LiteralPath $inputPath -Raw|ConvertFrom-Json -Depth 80
if($data.count -ne 31 -or $data.found -ne 31){throw 'Exact lookup incomplete'}
$wanted=@{};foreach($row in $data.rows){$wanted[$row.native_resource]=$row}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$archives=@((Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc/content') -Filter 'basegame_*.archive' -File|Sort-Object Name);(Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc/ep1') -Filter 'ep1_*.archive' -File|Sort-Object Name))
$extracted=[Collections.Generic.List[object]]::new()
foreach($af in $archives){
 $a=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($af.FullName,$hs,[ref]$a).ToString() -ne 'NoError'){throw "Archive read failed $($af.Name)"}
 foreach($e in $a.Files.Values){if($wanted.ContainsKey($e.Name)){
  $row=$wanted[$e.Name];$dir=Join-Path $out ([string]$row.id);[void][IO.Directory]::CreateDirectory($dir)
  $raw=Join-Path $dir ($af.BaseName+'.streamingsector')
  $ms=[IO.MemoryStream]::new();try{$e.Extract($ms);[IO.File]::WriteAllBytes($raw,$ms.ToArray())}finally{$ms.Dispose()}
  $extracted.Add([pscustomobject][ordered]@{id=$row.id;ref=$row.native_ref;archive=$af.Name;domain=if($af.Name.StartsWith('ep1_')){'ep1'}else{'base'};raw=$raw;sha256=(Get-FileHash -LiteralPath $raw -Algorithm SHA256).Hash})
 }}
}
$options=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new()
$handler=[WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e) return ($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])}
$results=[Collections.Generic.List[object]]::new()
foreach($row in $data.rows){
 $matches=@($extracted|Where-Object id -eq $row.id);$selected=@($matches|Where-Object domain -eq 'ep1');if(!$selected.Count){$selected=$matches}
 if(!$selected.Count -or @($selected|Select-Object -ExpandProperty sha256 -Unique).Count -ne 1){throw "Missing/ambiguous native winner $($row.id)"}
 $winner=$selected[-1];$stream=[IO.File]::OpenRead($winner.raw)
 try{
  $reader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($stream);$reader.add_ParsingError($handler);$file=$null
  if($reader.ReadFile([ref]$file,$true).ToString() -ne 'NoError'){throw "Decode failed $($row.id)"}
  $defs=[Collections.Generic.List[object]]::new();$ni=0
  foreach($h in $file.RootChunk.Nodes){$n=$h.Chunk;$v=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($n,$options)|ConvertFrom-Json -Depth 100;$defs.Add(@{index=$ni;definition=$v});$ni++}
  $setups=$file.RootChunk.NodeData.Buffer.GetBytes();if($setups.Length -ne $file.RootChunk.NodeData.Data.Count*0x90){throw 'Placement stride mismatch'}
  $places=[Collections.Generic.List[object]]::new();$i=0
  foreach($d in $file.RootChunk.NodeData.Data){
   $idx=[int]([BitConverter]::ToUInt64($setups,$i*0x90+0x70) -band 0x7FFFF);$n=if($idx -lt $file.RootChunk.Nodes.Count){$file.RootChunk.Nodes[$idx].Chunk}else{$null}
   $places.Add(@{datum=$i;id=$d.Id.ToString();node=$idx;type=if($n){$n.GetType().Name}else{'INVALID_INDEX'};position=@([double]$d.Position.X.ToString(),[double]$d.Position.Y.ToString(),[double]$d.Position.Z.ToString());quest_ref=$d.QuestPrefabRefHash.ToString();uk_ref=$d.UkHash1.ToString()});$i++
  }
  $dest=Join-Path (Join-Path $out ([string]$row.id)) 'nodes.json'
  @{nodes=$defs.ToArray();placements=$places.ToArray();node_refs=@($file.RootChunk.NodeRefs|ForEach-Object ToString);raw=$winner.raw;raw_sha256=$winner.sha256;full_ref=$row.native_ref}|ConvertTo-Json -Depth 100|Set-Content -LiteralPath $dest -Encoding utf8NoBOM
  $results.Add([ordered]@{id=$row.id;ref=$row.native_ref;winner=$winner;json=$dest;json_sha256=(Get-FileHash -LiteralPath $dest -Algorithm SHA256).Hash;nodes=$defs.Count;placements=$places.Count})
 }finally{$stream.Dispose()}
}
$result=[ordered]@{status='READ_ONLY_EXACT_AUTHORED_RANCHO_DECODE';source_sha256=(Get-FileHash -LiteralPath $inputPath -Algorithm SHA256).Hash;count=$results.Count;rows=@($results);game_writes=0;save_writes=0}
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'decoded_mismatch_02.json'),($result|ConvertTo-Json -Depth 40)+"`n",[Text.UTF8Encoding]::new($false))
@{status=$result.status;count=$result.count}|ConvertTo-Json
