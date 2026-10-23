param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$out=Join-Path $WorkspaceRoot 'research\b0_cpz_food02'
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$rows=[Collections.Generic.List[object]]::new()
$handler=[WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e)return ($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])}
foreach($relative in @('content\basegame_3_nightcity.archive','ep1\ep1_1_nightcity.archive')){
 $arc=$null
 [void]([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive(('C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\'+$relative),$hs,[ref]$arc)
 foreach($entry in $arc.Files.Values){
  if($entry.Name -notmatch 'always_loaded_[012]\.streamingsector$'){continue}
  $ms=[IO.MemoryStream]::new()
  try{
   $entry.Extract($ms);$hash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($ms.ToArray()));$ms.Position=0
   $reader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($ms);$reader.add_ParsingError($handler);$file=$null
   if($reader.ReadFile([ref]$file,$true).ToString() -ne 'NoError'){throw 'Read failed'}
   foreach($d in $file.RootChunk.NodeData.Data){
    $i=[int]$d.NodeIndex.ToString();$n=$file.RootChunk.Nodes[$i].Chunk
    $x=[double]$d.Position.X.ToString();$y=[double]$d.Position.Y.ToString();$z=[double]$d.Position.Z.ToString()
    $name=$n.DebugName.ToString();$ref=$d.QuestPrefabRefHash.ToString()
    $near=(($x+1541.27417)*($x+1541.27417)+($y+304.61795)*($y+304.61795)+($z+4.47565)*($z+4.47565)) -lt 3600
    if($near -or $name -match 'cpz.*food.*02' -or $ref -match 'cpz.*food.*02'){
     $rows.Add([pscustomobject]@{archive=$relative;sector=$entry.Name;sha256=$hash;index=$i;type=$n.GetType().Name;name=$name;reference=$ref;x=$x;y=$y;z=$z;orientation=@{i=$d.Orientation.I.ToString();j=$d.Orientation.J.ToString();k=$d.Orientation.K.ToString();r=$d.Orientation.R.ToString()}})
    }
   }
  }finally{$ms.Dispose()}
 }
}
[IO.File]::WriteAllText((Join-Path $out 'nearby_service_nodes.json'),(ConvertTo-Json -InputObject @($rows.ToArray()) -Depth 6))
$rows.ToArray() | Select-Object type,name,reference,x,y,z | ConvertTo-Json -Depth 4
