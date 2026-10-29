# Read-only archive extraction of 31 exact authored Rancho Coronado prefabs.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$models=@'
using WolvenKit.RED4.Types;
namespace WA3ReadOnly01 {
 public class worldCookedBendedMeshNode : worldNode, IDynamicClass {[RED("className")] public CName ClassName {get;set;}="worldCookedBendedMeshNode";}
 public class worldCookedAcousticSectorNode : worldNode, IDynamicClass {[RED("className")] public CName ClassName {get;set;}="worldCookedAcousticSectorNode";}
 public class worldCookedGenericProxyMeshNode : worldNode, IDynamicClass {[RED("className")] public CName ClassName {get;set;}="worldCookedGenericProxyMeshNode";}
 public class worldCookedStaticDecalNode : worldNode, IDynamicClass {[RED("className")] public CName ClassName {get;set;}="worldCookedStaticDecalNode";}
 public class worldCookedStaticMeshNode : worldNode, IDynamicClass {[RED("className")] public CName ClassName {get;set;}="worldCookedStaticMeshNode";}
 public class worldCookedCollisionNode : worldNode, IDynamicClass {[RED("className")] public CName ClassName {get;set;}="worldCookedCollisionNode";}
}
'@
Add-Type -TypeDefinition $models -ReferencedAssemblies ([WolvenKit.RED4.Types.RedBaseClass].Assembly.Location)
$types=@{'worldCookedBendedMeshNode'=[WA3ReadOnly01.worldCookedBendedMeshNode];'worldCookedStaticMeshNode'=[WA3ReadOnly01.worldCookedStaticMeshNode];'worldCookedCollisionNode'=[WA3ReadOnly01.worldCookedCollisionNode];'worldCookedAcousticSectorNode'=[WA3ReadOnly01.worldCookedAcousticSectorNode];'worldCookedGenericProxyMeshNode'=[WA3ReadOnly01.worldCookedGenericProxyMeshNode];'worldCookedStaticDecalNode'=[WA3ReadOnly01.worldCookedStaticDecalNode]}
foreach($e in $types.GetEnumerator()){
 [void][WolvenKit.RED4.Types.RedReflection]::AddRedType($e.Value)
 $p=[WolvenKit.RED4.Types.RedReflection]::GetNativePropertyInfo($e.Value,'ClassName');$p.GetType().GetProperty('IsIgnored').SetValue($p,$true)
 [WolvenKit.RED4.Types.RedReflection]::GetTypes()[$e.Key]=$e.Value
}

$data=Get-Content (Join-Path $PSScriptRoot '../native_review/combat_prefab_native_01/report_01.json') -Raw|ConvertFrom-Json -Depth 100
$out=Join-Path $PSScriptRoot 'decoded_01';if(Test-Path $out){throw 'Preserve evidence'}
[void][IO.Directory]::CreateDirectory($out)
$options=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new()
$handler=[WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e) return ($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])}
$results=[Collections.Generic.List[object]]::new()
foreach($resource in @($data.resources|Where-Object {$_ -notlike '*always_loaded*'}|Sort-Object)){
 $matches=@($data.hits|Where-Object resource -eq $resource)
 $row=@{resource=$resource;found=$matches.Count;parsed=$false;matches=$matches}
 if(!$matches.Count){$row.error='NO_CURRENT_RESOURCE';$results.Add($row);continue}
 if(@($matches|Where-Object is_mod).Count){$row.error='MOD_OVERRIDE_REQUIRES_REVIEW';$results.Add($row);continue}
 $selected=@($matches|Where-Object {$_.archive -like '*ep1*'})
 if(!$selected.Count){$selected=$matches}
 if(@($selected|Select-Object -ExpandProperty sha256 -Unique).Count -ne 1){$row.error='AMBIGUOUS_NATIVE_WINNER';$results.Add($row);continue}
 $winner=$selected[-1];$row.winner=$winner;$raw=$winner.raw;$stream=[IO.File]::OpenRead($raw)
 try{
  $reader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($stream);$reader.add_ParsingError($handler);$file=$null
  if($reader.ReadFile([ref]$file,$true).ToString() -ne 'NoError'){throw 'Decode failed'}
  $defs=[Collections.Generic.List[string]]::new();$ni=0
  foreach($h in $file.RootChunk.Nodes){$n=$h.Chunk;$v=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($n,$options);$defs.Add('{"index":'+$ni+',"definition":'+$v+'}');$ni++}
  $setups=$file.RootChunk.NodeData.Buffer.GetBytes();if($setups.Length -ne $file.RootChunk.NodeData.Data.Count*0x90){throw 'Placement stride mismatch'}
  $places=[Collections.Generic.List[object]]::new();$i=0
  foreach($d in $file.RootChunk.NodeData.Data){
   $idx=[int]([BitConverter]::ToUInt64($setups,$i*0x90+0x70) -band 0x7FFFF);$n=if($idx -lt $file.RootChunk.Nodes.Count){$file.RootChunk.Nodes[$idx].Chunk}else{$null}
   $places.Add(@{datum=$i;id=$d.Id.ToString();node=$idx;type=if($n){$n.GetType().Name}else{'INVALID_INDEX'};position=@([double]$d.Position.X.ToString(),[double]$d.Position.Y.ToString(),[double]$d.Position.Z.ToString());quest_ref=$d.QuestPrefabRefHash.ToString();uk_ref=$d.UkHash1.ToString()});$i++
  }
  $dest=Join-Path $out ([IO.Path]::GetFileNameWithoutExtension($resource)+'.json')
  $other=@{placements=@($places.ToArray());node_refs=@($file.RootChunk.NodeRefs|ForEach-Object ToString);raw=$raw;raw_sha256=$winner.sha256;resource=$resource}|ConvertTo-Json -Depth 20
  $serialized=$other.TrimEnd().Substring(0,$other.TrimEnd().Length-1)+',"nodes":['+($defs.ToArray()-join ',')+']}'
  [IO.File]::WriteAllText($dest,$serialized,[Text.UTF8Encoding]::new($false))
  $row.parsed=$true;$row.json=$dest;$row.json_sha256=(Get-FileHash -LiteralPath $dest).Hash;$row.nodes=$defs.Count;$row.placements=$places.Count
 }catch{$row.error=$_.Exception.ToString()}finally{$stream.Dispose()}
 $results.Add($row)
 if($results.Count%25 -eq 0){Write-Output "Decoded $($results.Count) support sectors"}
}
$result=@{status='CURRENT_ALL_REMAINING_NATIVE_SUPPORT_READBACK';rows=@($results.ToArray());game_writes=0;save_writes=0}
[IO.File]::WriteAllText((Join-Path $out 'report_01.json'),($result|ConvertTo-Json -Depth 30)+"`n",[Text.UTF8Encoding]::new($false))
@{count=$results.Count;parsed=@($results|Where-Object parsed).Count;missing=@($results|Where-Object found -eq 0).Count;failed=@($results|Where-Object {$_.found -gt 0 -and !$_.parsed}).Count}|ConvertTo-Json
