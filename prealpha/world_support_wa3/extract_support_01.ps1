$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$census=Get-Content (Join-Path $PSScriptRoot 'census_01.json') -Raw|ConvertFrom-Json -Depth 100
$out=Join-Path $PSScriptRoot 'extracted_01';if(Test-Path $out){throw 'Preserve evidence'}
[void][IO.Directory]::CreateDirectory($out)
$wanted=@{};$identities=@()
foreach($r in $census.rows){
 if($r.already_supported){continue}
 if($r.resolved_prefab){
  $hash=[WolvenKit.RED4.Types.NodeRef]::CalculateHash([string]$r.resolved_prefab)
  $depot='base\worlds\03_night_city\_compiled\default\quest_'+$hash.ToString('x16')+'.streamingsector'
  $wanted[$depot]=$true
  $identities+=@{id=$r.id;ref=$r.resolved_prefab;resource=$depot;hash=$hash.ToString();communities=@($r.community_refs|ForEach-Object {@{ref=$_;hash=[WolvenKit.RED4.Types.NodeRef]::CalculateHash([string]$_).ToString()}})}
 }
}
$wanted['base\worlds\03_night_city\_compiled\default\always_loaded_1.streamingsector']=$true
$keys=@{};foreach($r in $wanted.Keys){$keys[[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($r).ToString()]=$r}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$archives=@(Get-ChildItem -LiteralPath 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc' -Recurse -Filter '*.archive' -File)
$hits=[Collections.Generic.List[object]]::new()
foreach($af in $archives){
 $a=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($af.FullName,$hs,[ref]$a).ToString() -cne 'NoError'){throw ('Unreadable '+$af.FullName)}
 foreach($e in $a.Files.Values){
  $key=$e.Key.ToString();if(!$keys.ContainsKey($key)){continue}
  $depot=$keys[$key];$dest=Join-Path $out ($af.Name+'/'+[IO.Path]::GetFileName($depot));[void][IO.Directory]::CreateDirectory((Split-Path $dest -Parent))
  $ms=[IO.MemoryStream]::new();try{$e.Extract($ms);[IO.File]::WriteAllBytes($dest,$ms.ToArray())}finally{$ms.Dispose()}
  $hits.Add(@{archive=$af.FullName;resource=$depot;raw=$dest;sha256=(Get-FileHash -LiteralPath $dest).Hash;is_mod=$af.FullName.Contains('\mod\')})
 }
}
$result=@{status='CURRENT_ALL_REMAINING_SUPPORT_ARCHIVE_CENSUS';archives=$archives.Count;identities=$identities;resources=@($wanted.Keys);hits=@($hits.ToArray());game_writes=0;save_writes=0}
[IO.File]::WriteAllText((Join-Path $out 'report_01.json'),($result|ConvertTo-Json -Depth 20)+"`n",[Text.UTF8Encoding]::new($false))
@{archives=$archives.Count;identities=$identities.Count;resources=$wanted.Count;hits=$hits.Count}|ConvertTo-Json
