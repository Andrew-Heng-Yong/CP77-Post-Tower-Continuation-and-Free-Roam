$out=Join-Path $PSScriptRoot 'registry_fresh_01';if(Test-Path -LiteralPath $out){throw 'Preserve evidence'}
[void][IO.Directory]::CreateDirectory($out)
$resource='base\worlds\03_night_city\_compiled\default\always_loaded_1.streamingsector'
$key=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($resource)
$ids=@('8683340974758377731','8801107406373372937')
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$archives=@(Get-ChildItem -LiteralPath 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc' -Recurse -Filter '*.archive' -File)
$hits=@()
foreach($file in $archives){
 $a=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName,$hs,[ref]$a).ToString() -cne 'NoError'){throw ('Unreadable archive '+$file.FullName)}
 if(!$a.Files.ContainsKey([uint64]$key)){continue}
 $entry=$a.Files[[uint64]$key];$raw=Join-Path $out ($file.BaseName+'.streamingsector')
 $stream=[IO.File]::Create($raw);try{$entry.Extract($stream)}finally{$stream.Dispose()}
 $stream=[IO.File]::OpenRead($raw)
 try{
  $reader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($stream)
  $reader.add_ParsingError([WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e) return ($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])})
  $parsed=$null;if($reader.ReadFile([ref]$parsed,$true).ToString() -cne 'NoError'){throw 'Registry decode failed'}
  $selected=@()
  foreach($n in $parsed.RootChunk.Nodes){if($n.Chunk.GetType().Name -ne 'worldCommunityRegistryNode'){continue};foreach($c in $n.Chunk.CommunitiesData){
   if($ids -contains $c.CommunityId.EntityId.Hash.ToString()){$selected+=([WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($c,[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())|ConvertFrom-Json -Depth 100)}
  }}
  if($selected.Count -ne 2){throw 'Expected two exact community registry entries'}
  $json=$raw+'.json';[IO.File]::WriteAllText($json,(@{communities=$selected}|ConvertTo-Json -Depth 100)+"`n",[Text.UTF8Encoding]::new($false))
 }finally{$stream.Dispose()}
 $hits+=@{archive=$file.FullName;depot=$resource;raw=$raw;sha256=(Get-FileHash -LiteralPath $raw).Hash;json=$json;json_sha256=(Get-FileHash -LiteralPath $json).Hash}
}
[IO.File]::WriteAllText((Join-Path $out 'report_01.json'),(@{status='CURRENT_EXACT_COMMUNITY_REGISTRY';archives=$archives.Count;hits=$hits;game_writes=0;save_writes=0}|ConvertTo-Json -Depth 10)+"`n",[Text.UTF8Encoding]::new($false))
@{archives=$archives.Count;hits=$hits.Count}|ConvertTo-Json
