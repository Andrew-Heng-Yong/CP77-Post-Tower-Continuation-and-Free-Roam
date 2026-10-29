$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$inputs=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'inputs_01.json') -Raw|ConvertFrom-Json -Depth 30
foreach($p in $inputs.pins){if((Get-FileHash -LiteralPath $p.path).Hash -cne $p.sha256){throw 'Input changed'}}
$out=Join-Path $PSScriptRoot 'extract_02';if(Test-Path -LiteralPath $out){throw 'Preserve evidence'}
[void][IO.Directory]::CreateDirectory($out)
$keys=@{}
foreach($g in $inputs.groups){
 $tx=[int][math]::Floor($g.center[0]/64);$ty=[int][math]::Floor($g.center[1]/64)
 foreach($x in (($tx-1)..($tx+1))){foreach($y in (($ty-1)..($ty+1))){
  $depot='base\worlds\03_night_city\_compiled\default\exterior_'+$x+'_'+$y+'_0_0.streamingsector'
  $keys[[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot).ToString()]=$depot
 }}
}
$block='base\worlds\03_night_city\_compiled\default\blocks\all.streamingblock'
$keys[[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($block).ToString()]=$block
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$archives=@(Get-ChildItem -LiteralPath 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc' -Recurse -Filter '*.archive' -File)
$hits=@()
foreach($file in $archives){
 $a=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName,$hs,[ref]$a).ToString() -cne 'NoError'){throw ('Unreadable archive '+$file.FullName)}
 foreach($key in $keys.Keys){
  if(!$a.Files.ContainsKey([uint64]$key)){continue}
  $e=$a.Files[[uint64]$key];$depot=$keys[$key]
  $raw=Join-Path $out ($file.BaseName+'_'+$key+[IO.Path]::GetExtension($depot))
  $stream=[IO.File]::Create($raw);try{$e.Extract($stream)}finally{$stream.Dispose()}
  if($depot.EndsWith('.streamingblock')){Export-Cr2wJson (Read-Cr2wFile $raw) ($raw+'.json')}
  $hits+=@{archive=$file.FullName;depot=$depot;raw=$raw;sha256=(Get-FileHash -LiteralPath $raw).Hash}
 }
}
$r=@{status='CURRENT_NEARBY_DEFAULT_ENVIRONMENT_CENSUS';archives=$archives.Count;resources=@($keys.Values|Sort-Object);hits=$hits;game_writes=0;save_writes=0}
[IO.File]::WriteAllText((Join-Path $out 'report_01.json'),($r|ConvertTo-Json -Depth 12)+"`n",[Text.UTF8Encoding]::new($false))
@{archives=$archives.Count;queries=$keys.Count;hits=$hits.Count}|ConvertTo-Json
