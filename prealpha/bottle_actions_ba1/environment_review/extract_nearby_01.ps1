$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
$wk=Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package'
foreach($n in @('WolvenKit.Core.dll','WolvenKit.Common.dll','WolvenKit.RED4.dll')){[void][Reflection.Assembly]::LoadFrom((Join-Path $wk $n))}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$out=Join-Path $PSScriptRoot 'nearby_01'
if(Test-Path -LiteralPath $out){throw 'Preserve evidence'}
[void][IO.Directory]::CreateDirectory($out)
$keys=@{}
foreach($lod in 0..5){
 $size=64*[math]::Pow(2,$lod);$tx=[int][math]::Floor(-2107.72/$size);$ty=[int][math]::Floor(-1901.91/$size)
 foreach($x in (($tx-1)..($tx+1))){foreach($y in (($ty-1)..($ty+1))){
  $depot='base\worlds\03_night_city\_compiled\default\exterior_'+$x+'_'+$y+'_0_'+$lod+'.streamingsector'
  $keys[[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot).ToString()]=$depot
 }}
}
$matches=[Collections.Generic.List[object]]::new()
foreach($rel in @('content/basegame_3_nightcity.archive','ep1/ep1_1_nightcity.archive')){
 $ap=Join-Path 'C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077/archive/pc' $rel;$a=$null
 if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($ap,$hs,[ref]$a).ToString() -ne 'NoError'){throw 'Archive read failed'}
 foreach($e in $a.Files.Values){
  if(!$keys.ContainsKey($e.Key.ToString())){continue}
  $raw=Join-Path $out (([IO.Path]::GetFileNameWithoutExtension($ap))+'_'+$e.Key+'.streamingsector')
  $s=[IO.File]::Create($raw);try{$e.Extract($s)}finally{$s.Dispose()}
  $matches.Add(@{archive=$ap;resource=$e.Name;raw=$raw;sha256=(Get-FileHash -LiteralPath $raw).Hash})
 }
}
[IO.File]::WriteAllText((Join-Path $out 'report_01.json'),(@{status='READ_ONLY_NEARBY_DEFAULT_SECTORS';queries=$keys.Count;matches=@($matches.ToArray())}|ConvertTo-Json -Depth 8)+"`n",[Text.UTF8Encoding]::new($false))
Write-Output "Extracted $($matches.Count) nearby sectors"
