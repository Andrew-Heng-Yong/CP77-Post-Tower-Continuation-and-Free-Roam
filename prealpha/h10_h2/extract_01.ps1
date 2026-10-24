$ErrorActionPreference='Stop'
$W=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent;$O=Join-Path $PSScriptRoot 'candidate_01/native_inspect_01'
if(Test-Path $O){throw 'Use successor'}
. (Join-Path $W 'tools/build_phase2a.ps1') -WorkspaceRoot $W -HelpersOnly -WolvenKitRoot (Join-Path $W 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$depots=@('towercontinued\b0_wilson_vendor\owner.questphase','towercontinued\b0_wilson_vendor\body.questphase','towercontinued\sidejobs_s23\base_b\mq011.questphase')
$wanted=@{};foreach($d in $depots){$wanted[[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($d)]=$d}
$rows=@()
foreach($p in Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc/mod') -Filter '*Tower*.archive'){
 $a=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($p.FullName,$hs,[ref]$a).ToString() -ne 'NoError'){throw 'Read failed'}
 foreach($key in $wanted.Keys){
  if(!$a.Files.ContainsKey($key)){continue}
  $d=$wanted[$key];$dest=Join-Path (Join-Path $O $p.BaseName) $d
  New-Item -ItemType Directory -Force -Path (Split-Path $dest -Parent)|Out-Null
  $s=[IO.File]::Create($dest);try{$a.Files[$key].Extract($s)}finally{$s.Dispose()}
  Export-Cr2wJson (Read-Cr2wFile $dest) ($dest+'.json')
  $rows+=@{archive=$p.FullName;archive_sha256=(Get-FileHash $p.FullName).Hash;depot=$d;raw=$dest;sha256=(Get-FileHash $dest).Hash}
 }
}
$rows|ConvertTo-Json -Depth 10|Set-Content (Join-Path $O 'resources.json') -Encoding utf8
$rows|Select-Object archive,depot,sha256|ConvertTo-Json
