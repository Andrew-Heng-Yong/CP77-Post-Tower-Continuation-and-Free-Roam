param([Parameter(Mandatory=$true)][string]$ResourceFile,[Parameter(Mandatory=$true)][string]$OutputName)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$out=Join-Path $PSScriptRoot $OutputName
if(Test-Path -LiteralPath $out){throw 'Preserve existing evidence'}
[void][IO.Directory]::CreateDirectory($out)
$resources=@(Get-Content -LiteralPath $ResourceFile)
$keys=@{};foreach($r in $resources){$keys[[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($r).ToString()]=$r}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$archives=@(Get-ChildItem -LiteralPath 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc' -Recurse -Filter '*.archive' -File)
$hits=@()
foreach($file in $archives){
 $a=$null
 if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName,$hs,[ref]$a).ToString() -cne 'NoError'){throw ('Unreadable '+$file.FullName)}
 foreach($entry in $a.Files.Values){
  $key=$entry.Key.ToString();if(!$keys.ContainsKey($key)){continue}
  $depot=$keys[$key];$dest=Join-Path $out ($file.Name+'/'+$depot)
  [void][IO.Directory]::CreateDirectory((Split-Path $dest -Parent))
  $stream=[IO.File]::Create($dest)
  try{$entry.Extract($stream)}finally{$stream.Dispose()}
  Export-Cr2wJson (Read-Cr2wFile $dest) ($dest+'.json')
  $hits+=@{archive=$file.FullName;depot=$depot;copy=$dest;sha256=(Get-FileHash -LiteralPath $dest).Hash}
 }
}
$result=@{status='CURRENT_DEPENDENCY_CENSUS';archives=$archives.Count;hits=$hits;game_writes=0;save_writes=0}
[IO.File]::WriteAllText((Join-Path $out 'report_01.json'),($result|ConvertTo-Json -Depth 10)+"`n",[Text.UTF8Encoding]::new($false))
$result|ConvertTo-Json -Depth 10
