Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$depot='base\workspots\quest\side_quests\sq006\sq006_02b_investigation\sq006__johnny__stand_cigarette__stand_around__01.workspot'
$key=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot)
$game='C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077/archive/pc/content'
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$hits=@()
foreach($path in (Get-ChildItem -LiteralPath $game -Filter '*.archive' -File)){
 $a=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($path.FullName,$hs,[ref]$a).ToString() -cne 'NoError'){throw ('Archive read failed '+$path.FullName)}
 if(!$a.Files.ContainsKey($key)){continue}
 $out=Join-Path $PSScriptRoot 'candidate_02/kold_workspot_source_01';New-Item -ItemType Directory -Path $out -Force|Out-Null
 $raw=Join-Path $out ([IO.Path]::GetFileNameWithoutExtension($path.Name)+'.workspot');$m=[IO.MemoryStream]::new();try{$a.Files[$key].Extract($m);[IO.File]::WriteAllBytes($raw,$m.ToArray())}finally{$m.Dispose()}
 Export-Cr2wJson (Read-Cr2wFile $raw) ($raw+'.json')
 $hits+=@{archive=$path.FullName;raw=$raw;sha256=(Get-FileHash -LiteralPath $raw).Hash}
}
$hits|ConvertTo-Json -Depth 10
