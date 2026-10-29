$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$out=Join-Path $PSScriptRoot 'registry_01'
if(Test-Path -LiteralPath $out){throw 'Preserve evidence'}
[void][IO.Directory]::CreateDirectory($out)
$refs=@{
 '250'='$/03_night_city/#c_santo_domingo/arroyo/arr_cs_prefab4OUIGHQ/cs_goons_shooting_openworld_001_prefabNTGSYYA/#cs_std_arr_goons_shooting_com'
 '130'='$/03_night_city/#c_heywood/vista_del_rey/rey_ce_prefabWLQAZXI/cs_goons_shooting_openworld_prefabWPDHRIQ/cs_goons_shooting_com'
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
@{status='READ_ONLY_EXACT_REGISTRY_BINDING';refs=$refs;hashes=$hashes;rows=$rows;game_writes=0;save_writes=0}|ConvertTo-Json -Depth 15|Set-Content -LiteralPath (Join-Path $out 'report_01.json') -Encoding utf8NoBOM
@{hashes=$hashes;rows=$rows}|ConvertTo-Json -Depth 10
