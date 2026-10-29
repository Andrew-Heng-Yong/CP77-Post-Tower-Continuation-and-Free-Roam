$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$cohort=Get-Content (Join-Path $PSScriptRoot 'identity_cohort_01.json') -Raw|ConvertFrom-Json -Depth 100
$out=Join-Path $PSScriptRoot 'spot_bindings_01';if(Test-Path $out){throw 'Preserve evidence'}
[void][IO.Directory]::CreateDirectory($out)
$hashes=@{};$spotRows=@()
foreach($g in $cohort.groups){
 foreach($hash in $g.spawner_hashes){$hashes[$hash]=$true}
 $d=Get-Content -LiteralPath $g.support_sector_json -Raw|ConvertFrom-Json -AsHashtable -Depth 100
 $spots=@();foreach($p in $d.placements){if($p.type -eq 'worldAISpotNode'){$spots+=@{ref=$p.quest_ref;hash=[WolvenKit.RED4.Types.NodeRef]::CalculateHash([string]$p.quest_ref).ToString();node=$p.node;datum=$p.datum}}}
 $spotRows+=@{id=$g.id;spots=$spots}
}
$raw=Join-Path $PSScriptRoot 'additional_extracted_03/ep1_1_nightcity.archive/always_loaded_1.streamingsector'
$stream=[IO.File]::OpenRead($raw);$areas=@()
try{
 $reader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($stream);$reader.add_ParsingError([WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e)return ($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])});$file=$null
 if($reader.ReadFile([ref]$file,$true).ToString() -cne 'NoError'){throw 'Native area read failed'}
 $index=0;foreach($h in $file.RootChunk.Nodes){
  $n=$h.Chunk
  if($n.GetType().Name -like 'worldCompiledCommunityAreaNode*'){
   $hash=$n.SourceObjectId.Hash.ToString()
   if($hashes.ContainsKey($hash)){
    $p=Join-Path $out ($hash+'.json');$json=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($n,[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())
    if(Test-Path $p){throw 'Duplicate community area hash'}
    [IO.File]::WriteAllText($p,$json,[Text.UTF8Encoding]::new($false))
    $areas+=@{hash=$hash;node=$index;json=$p;sha256=(Get-FileHash $p).Hash}
   }
  };$index++
 }
}finally{$stream.Dispose()}
$result=@{status='CURRENT_COMPILED_AREA_SPOT_BINDINGS';native_registry=$raw;native_registry_sha256=(Get-FileHash $raw).Hash;groups=$spotRows;areas=$areas;game_writes=0;save_writes=0}
[IO.File]::WriteAllText((Join-Path $out 'report_01.json'),($result|ConvertTo-Json -Depth 30)+"`n",[Text.UTF8Encoding]::new($false))
@{groups=$spotRows.Count;areas=$areas.Count;wanted=$hashes.Count}|ConvertTo-Json
