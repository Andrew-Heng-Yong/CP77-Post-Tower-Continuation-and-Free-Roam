$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$out=Join-Path $PSScriptRoot 'external_01'
if(Test-Path -LiteralPath $out){throw 'Preserve evidence'}
[void][IO.Directory]::CreateDirectory($out)
$resources=@(Get-Content -LiteralPath (Join-Path $PSScriptRoot 'external_resources_01.txt'))
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
  $row=@{archive=$file.FullName;depot=$depot;raw=$dest;sha256=(Get-FileHash -LiteralPath $dest).Hash;parsed=$false}
  try{Export-Cr2wJson (Read-Cr2wFile $dest) ($dest+'.json');$row.parsed=$true;$row.json=$dest+'.json'}catch{$row.error=$_.Exception.ToString()}
  $hits.Add($row)
 }
}
$result=@{status='CURRENT_EXACT_EXTERNAL_PHASE_CENSUS';archives=$archives.Count;resources=$resources;hits=@($hits.ToArray());game_writes=0;save_writes=0}
[IO.File]::WriteAllText((Join-Path $out 'report_01.json'),($result|ConvertTo-Json -Depth 10)+"`n",[Text.UTF8Encoding]::new($false))
@{resources=$resources.Count;hits=$hits.Count;parsed=@($hits|Where-Object parsed).Count}|ConvertTo-Json
