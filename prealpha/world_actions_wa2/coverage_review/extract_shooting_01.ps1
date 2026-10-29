$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$out=Join-Path $PSScriptRoot 'shooting_sources_01'
if(Test-Path -LiteralPath $out){throw 'Preserve evidence'}
[void][IO.Directory]::CreateDirectory($out)
$resources=[Collections.Generic.List[string]]::new()
foreach($r in @('base\worlds\03_night_city\_compiled\default\always_loaded_0.streamingsector','base\worlds\03_night_city\_compiled\default\always_loaded_1.streamingsector','base\worlds\03_night_city\_compiled\default\blocks\all.streamingblock','base\worlds\03_night_city\_compiled\default\quest_b6fab76541bd1bdb.streamingsector','base\open_world\combat_events\santo_domingo\arroyo\ce_std_arr_phase.questphase','base\open_world\combat_events\heywood\vista_del_rey\ce_hey_rey_phase.questphase')){$resources.Add($r)}
$variants=@()
foreach($district in @('#c_heywood','c_heywood')){foreach($sub in @('vista_del_rey','#vista_del_rey')){
 $ref='$/03_night_city/'+$district+'/'+$sub+'/rey_ce_prefabWLQAZXI/cs_goons_shooting_openworld_prefabWPDHRIQ'
 $hash=[WolvenKit.RED4.Types.NodeRef]::CalculateHash($ref)
 $resource='base\worlds\03_night_city\_compiled\default\quest_'+$hash.ToString('x16')+'.streamingsector'
 $resources.Add($resource);$variants+=@{ref=$ref;hash=$hash.ToString();resource=$resource}
}}
foreach($x in -1..1){foreach($y in -18..-16){$resources.Add(('base\worlds\03_night_city\_compiled\default\exterior_{0}_{1}_0_0.streamingsector' -f $x,$y))}}
$keys=@{};foreach($r in $resources){$keys[[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($r).ToString()]=$r}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$archives=@(Get-ChildItem -LiteralPath 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc' -Recurse -Filter '*.archive' -File)
$hits=[Collections.Generic.List[object]]::new()
foreach($file in $archives){
 $a=$null
 if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName,$hs,[ref]$a).ToString() -cne 'NoError'){throw ('Unreadable '+$file.FullName)}
 foreach($entry in $a.Files.Values){
  $key=$entry.Key.ToString();if(!$keys.ContainsKey($key)){continue}
  $depot=$keys[$key];$dest=Join-Path $out ($file.Name+'/'+[IO.Path]::GetFileName($depot))
  [void][IO.Directory]::CreateDirectory((Split-Path $dest -Parent))
  $stream=[IO.File]::Create($dest)
  try{$entry.Extract($stream)}finally{$stream.Dispose()}
  $row=@{archive=$file.FullName;depot=$depot;raw=$dest;sha256=(Get-FileHash -LiteralPath $dest).Hash}
  if($depot.EndsWith('.questphase') -or $depot.EndsWith('.streamingblock') -or $depot.Contains('always_loaded_')){
   try{Export-Cr2wJson (Read-Cr2wFile $dest) ($dest+'.json');$row.parsed=$true;$row.json=$dest+'.json'}catch{$row.parsed=$false;$row.error=$_.Exception.ToString()}
  }
  $hits.Add($row)
 }
}
$result=@{status='CURRENT_SHOOTING_DEPENDENCY_CENSUS';archives=$archives.Count;resources=@($resources.ToArray());candidate130_variants=$variants;hits=@($hits.ToArray());game_writes=0;save_writes=0}
[IO.File]::WriteAllText((Join-Path $out 'report_01.json'),($result|ConvertTo-Json -Depth 10)+"`n",[Text.UTF8Encoding]::new($false))
@{resources=$resources.Count;hits=$hits.Count}|ConvertTo-Json
