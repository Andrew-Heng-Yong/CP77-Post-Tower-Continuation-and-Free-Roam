$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$out=Join-Path $PSScriptRoot 'candidate306_01'
if(Test-Path -LiteralPath $out){throw 'Preserve evidence'}
[void][IO.Directory]::CreateDirectory($out)
$refs=@{
 '306'='$/03_night_city/#c_santo_domingo/rancho_coronado/rcr_ce_prefabUUVLBPI/ce_std_rcr_133_a/ce_std_rcr_133/cs_goons_shooting_com'
 '289'='$/03_night_city/#c_santo_domingo/rancho_coronado/rcr_ce_prefabUUVLBPI/cs_goons_shooting_openworld_prefab75FOTQA/cs_goons_shooting_com'
}
$hashes=@{};foreach($key in $refs.Keys){$hashes[$key]=[WolvenKit.RED4.Types.NodeRef]::CalculateHash($refs[$key]).ToString()}
$handler=[WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e) return ($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])}
$rows=@()
foreach($archive in @('basegame_3_nightcity.archive','ep1_1_nightcity.archive')){
 $raw=Join-Path $PSScriptRoot ('shooting_sources_01/'+$archive+'/always_loaded_1.streamingsector')
 $stream=[IO.File]::OpenRead($raw)
 try{
  $reader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($stream);$reader.add_ParsingError($handler);$file=$null
  if($reader.ReadFile([ref]$file,$true).ToString() -ne 'NoError'){throw 'Decode failed'}
  $ni=0;$found=@();$registryCount=0
  foreach($h in $file.RootChunk.Nodes){
   $node=$h.Chunk
   if($node.GetType().Name -eq 'worldCommunityRegistryNode'){
    $ci=0
    foreach($c in $node.CommunitiesData){
     $registryCount++;$id=$c.CommunityId.EntityId.Hash.ToString()
     if($id -in @($hashes.Values)){
      $json=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($c,[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())
      $dest=Join-Path $out ($archive+'_'+$id+'.json');[IO.File]::WriteAllText($dest,$json,[Text.UTF8Encoding]::new($false))
      $found+=@{community_id=$id;registry_node=$ni;community_index=$ci;json=$dest}
     };$ci++
    }
   };$ni++
  }
  $rows+=@{archive=$archive;raw=$raw;raw_sha256=(Get-FileHash -LiteralPath $raw).Hash;registry_entries=$registryCount;found=$found}
 }finally{$stream.Dispose()}
}
$resources=[Collections.Generic.List[string]]::new()
$resources.Add('base\open_world\combat_events\santo_domingo\rancho_coronado\ce_std_rcr_phase.questphase')
$variants=@()
foreach($district in @('#c_santo_domingo','c_santo_domingo')){foreach($sub in @('rancho_coronado','#rancho_coronado')){
 $ref='$/03_night_city/'+$district+'/'+$sub+'/rcr_ce_prefabUUVLBPI/ce_std_rcr_133_a/ce_std_rcr_133'
 $hash=[WolvenKit.RED4.Types.NodeRef]::CalculateHash($ref)
 $resource='base\worlds\03_night_city\_compiled\default\quest_'+$hash.ToString('x16')+'.streamingsector'
 $resources.Add($resource);$variants+=@{ref=$ref;hash=$hash.ToString();resource=$resource}
}}
$keys=@{};foreach($r in $resources){$keys[[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($r).ToString()]=$r}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$archives=@(Get-ChildItem -LiteralPath 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc' -Recurse -Filter '*.archive' -File)
$hits=[Collections.Generic.List[object]]::new()
foreach($entryFile in $archives){
 $a=$null
 if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($entryFile.FullName,$hs,[ref]$a).ToString() -cne 'NoError'){throw ('Unreadable '+$entryFile.FullName)}
 foreach($entry in $a.Files.Values){
  $key=$entry.Key.ToString();if(!$keys.ContainsKey($key)){continue}
  $depot=$keys[$key];$dest=Join-Path $out ($entryFile.Name+'/'+[IO.Path]::GetFileName($depot))
  [void][IO.Directory]::CreateDirectory((Split-Path $dest -Parent))
  $stream=[IO.File]::Create($dest)
  try{$entry.Extract($stream)}finally{$stream.Dispose()}
  $row=@{archive=$entryFile.FullName;depot=$depot;raw=$dest;sha256=(Get-FileHash -LiteralPath $dest).Hash}
  if($depot.EndsWith('.questphase')){Export-Cr2wJson (Read-Cr2wFile $dest) ($dest+'.json');$row.json=$dest+'.json'}
  $hits.Add($row)
 }
}
$result=@{status='READ_ONLY_CANDIDATE306_EXACT_REGISTRY_AND_ARCHIVE_CHECK';refs=$refs;hashes=$hashes;registry_rows=$rows;archives=$archives.Count;resources=@($resources.ToArray());variants=$variants;hits=@($hits.ToArray());game_writes=0;save_writes=0}
[IO.File]::WriteAllText((Join-Path $out 'report_01.json'),($result|ConvertTo-Json -Depth 15)+"`n",[Text.UTF8Encoding]::new($false))
@{hashes=$hashes;registry=$rows;hits=@($hits.ToArray())}|ConvertTo-Json -Depth 8
