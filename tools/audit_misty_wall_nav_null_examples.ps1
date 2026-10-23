param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
Add-Type -TypeDefinition 'using System; public static class PTFRNullNeedle { public static bool Has(byte[] a, byte[] b) { return System.MemoryExtensions.IndexOf<byte>(a.AsSpan(), b.AsSpan()) >= 0; } }'
$hash=[WolvenKit.Common.Services.HashService]::new();$hash.Load()
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc'
$needle=[Text.Encoding]::UTF8.GetBytes('worldCrowdNullAreaNode')
$out=Join-Path $WorkspaceRoot 'research\misty_viktor_world\r6_wall_nav_null_examples'
New-Item -ItemType Directory -Force $out|Out-Null
$rows=[Collections.Generic.List[object]]::new();$scanned=0;$hits=0
foreach($relative in @('ep1\ep1_1_nightcity.archive','content\basegame_3_nightcity.archive')){
 $arc=$null;$archivePath=Join-Path $game $relative
 [void]([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archivePath,$hash,[ref]$arc)
 foreach($e in $arc.Files.Values){
  if($e.Name -notmatch 'exterior_-?\d+_-?\d+_-?\d+_2\.streamingsector$'){continue}
  $scanned++;$m=[IO.MemoryStream]::new()
  try{
   $e.Extract($m);$bytes=$m.ToArray()
   if(-not [PTFRNullNeedle]::Has($bytes,$needle)){continue}
   $hits++;$m.Position=0;$reader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($m)
   $handler=[WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($x)return ($x -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])}
   $reader.add_ParsingError($handler);$f=$null
   if($reader.ReadFile([ref]$f,$true).ToString() -ne 'NoError'){continue}
   for($i=0;$i -lt $f.RootChunk.Nodes.Count;$i++){
    $n=$f.RootChunk.Nodes[$i].Chunk
    if($n.GetType().Name -ne 'worldCrowdNullAreaNode' -or $n.PermanentlyEnabledByDefault.ToString() -ne 'True'){continue}
    $archiveKey=[IO.Path]::GetFileNameWithoutExtension($relative)
    $raw=Join-Path $out ($archiveKey+'\raw\'+$e.Name)
    New-Item -ItemType Directory -Force (Split-Path $raw)|Out-Null
    [IO.File]::WriteAllBytes($raw,$bytes)
    $json=Join-Path $out ($archiveKey+'\json\'+$e.Name+'.json')
    Export-Cr2wJson $f $json
    $rows.Add([pscustomobject]@{archive=$archivePath;sector=$e.Name;node_index=$i;name=$n.DebugName.ToString();IsForBlockade=$n.IsForBlockade.ToString();permanentlyEnabledByDefault=$n.PermanentlyEnabledByDefault.ToString();raw=$raw;json=$json;sha256=(Get-FileHash $raw).Hash})
   }
  }finally{$m.Dispose()}
  if($rows.Count -ge 3){break}
 }
 if($rows.Count -ge 3){break}
}
$result=@{scanned=$scanned;type_hits=$hits;examples=@($rows)}
[IO.File]::WriteAllText((Join-Path $out 'manifest.json'),($result|ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false))
$result|ConvertTo-Json -Depth 6
