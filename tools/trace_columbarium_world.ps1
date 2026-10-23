param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$out=Join-Path $WorkspaceRoot 'research\radio_memorial_validation\world'
New-Item -ItemType Directory -Force -Path $out | Out-Null
$hashService=[WolvenKit.Common.Services.HashService]::new();$hashService.Load()
$rows=[Collections.Generic.List[object]]::new()
$handler=[WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e) return ($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])}
foreach($rel in @('content\basegame_3_nightcity.archive','ep1\ep1_1_nightcity.archive')){
  $arc=$null
  $path=Join-Path 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc' $rel
  if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($path,$hashService,[ref]$arc).ToString() -ne 'NoError'){throw 'Archive read failed'}
  $scanned=0;$matched=0
  foreach($entry in $arc.Files.Values){
    if($entry.Extension -ne '.streamingsector'){continue}
    $stream=[IO.MemoryStream]::new()
    try{
      $entry.Extract($stream);$scanned++
      $bytes=$stream.ToArray();$text=[Text.Encoding]::UTF8.GetString($bytes)
      if(-not $text.Contains('loc_q204_columbarium_devices',[StringComparison]::Ordinal)){continue}
      $matched++;$stream.Position=0;$file=$null
      $reader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($stream);$reader.add_ParsingError($handler)
      if($reader.ReadFile([ref]$file,$true).ToString() -ne 'NoError'){throw 'Sector parse failed'}
      $stem=([IO.Path]::GetFileNameWithoutExtension($rel))+'_'+[IO.Path]::GetFileName($entry.Name)
      $found=[Collections.Generic.List[object]]::new()
      foreach($d in $file.RootChunk.NodeData.Data){
        if(-not $d.QuestPrefabRefHash.ToString().Contains('#loc_q204_columbarium_devices',[StringComparison]::Ordinal)){continue}
        $idx=[int]$d.NodeIndex.ToString();$node=$file.RootChunk.Nodes[$idx].Chunk
        $found.Add([pscustomobject]@{index=$idx;type=$node.GetType().Name;reference=$d.QuestPrefabRefHash.ToString();x=[double]$d.Position.X.ToString();y=[double]$d.Position.Y.ToString();z=[double]$d.Position.Z.ToString()})
      }
      $rows.Add([pscustomobject]@{archive=$rel;sector=$entry.Name;sha256=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes));nodes=$found.ToArray()})
    }finally{$stream.Dispose()}
  }
  Write-Output "$rel scanned=$scanned matched=$matched"
}
[IO.File]::WriteAllText((Join-Path $out 'matches.json'),(ConvertTo-Json -InputObject @($rows.ToArray()) -Depth 7))
