$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$out=Join-Path $PSScriptRoot 'registry_01';if(Test-Path $out){throw 'Preserve evidence'}
[void][IO.Directory]::CreateDirectory($out)
$prepared=Get-Content (Join-Path $PSScriptRoot 'registry_candidates_01.json') -Raw|ConvertFrom-Json -Depth 30
$refs=@{};$identities=@()
foreach($r in $prepared){
 $local=@();foreach($ref in $r.refs){$hash=[WolvenKit.RED4.Types.NodeRef]::CalculateHash([string]$ref).ToString();$refs[$hash]=$ref;$local+=@{ref=$ref;hash=$hash;within_prefab=$ref.StartsWith($r.prefab+'/')}}
 $identities+=@{id=$r.id;prefab=$r.prefab;candidates=$local}
}
Write-Output ("Calculated "+$refs.Count+" native candidate hashes")
$handler=[WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e) return ($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])}
$rows=@()
foreach($archive in @('basegame_3_nightcity.archive','ep1_1_nightcity.archive')){
 $raw=Join-Path $PSScriptRoot ('../extracted_01/'+$archive+'/always_loaded_1.streamingsector');$stream=[IO.File]::OpenRead($raw)
 try{
  $reader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($stream);$reader.add_ParsingError($handler);$file=$null
  if($reader.ReadFile([ref]$file,$true).ToString() -ne 'NoError'){throw 'Decode failed'}
  $found=@();$count=0;$ni=0
  foreach($h in $file.RootChunk.Nodes){
   if($h.Chunk.GetType().Name -eq 'worldCommunityRegistryNode'){
    $ci=0;foreach($community in $h.Chunk.CommunitiesData){
     $count++;$hash=$community.CommunityId.EntityId.Hash.ToString()
     if($refs.ContainsKey($hash)){
      $dest=Join-Path $out ($archive+'_'+$hash+'.json')
      $json=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($community,[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())
      [IO.File]::WriteAllText($dest,$json,[Text.UTF8Encoding]::new($false))
      $found+=@{hash=$hash;ref=$refs[$hash];json=$dest;sha256=(Get-FileHash -LiteralPath $dest).Hash;node_index=$ni;community_index=$ci}
     };$ci++
    }
   };$ni++
  }
  $rows+=@{archive=$archive;raw=$raw;raw_sha256=(Get-FileHash -LiteralPath $raw).Hash;registry_entries=$count;found=$found}
 }finally{$stream.Dispose()}
}
$result=@{status='CURRENT_NATIVE_REGISTRY_BINDINGS';identities=$identities;candidate_hashes=$refs.Count;rows=$rows;game_writes=0;save_writes=0}
[IO.File]::WriteAllText((Join-Path $out 'report_01.json'),($result|ConvertTo-Json -Depth 30)+"`n",[Text.UTF8Encoding]::new($false))
@{candidates=$refs.Count;found=@($rows|ForEach-Object {$_.found}|Select-Object -ExpandProperty hash -Unique).Count}|ConvertTo-Json
