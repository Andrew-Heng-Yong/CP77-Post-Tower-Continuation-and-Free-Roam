. ./tools/build_phase2a.ps1 -HelpersOnly -WolvenKitRoot (Join-Path (Get-Location).Path 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$ErrorActionPreference='Stop';$c=Join-Path $PSScriptRoot 'candidate_03';$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$deps=@('base\quest\additional_game_elements.questphase','ep1\quest\ep1_additional_game_elements.questphase');$rows=@()
foreach($f in Get-ChildItem 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc' -Recurse -Filter '*.archive' -File){
 $a=$null;[void]([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($f.FullName,$hs,[ref]$a)
 foreach($d in $deps){$k=[uint64][WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($d);if($a.Files.ContainsKey($k)){$p=Join-Path $c ('native_'+$d.Replace('\','_'));$m=[IO.MemoryStream]::new();$a.Files[$k].Extract($m);[IO.File]::WriteAllBytes($p,$m.ToArray());$m.Dispose();Export-Cr2wJson (Read-Cr2wFile $p) ($p+'.json');$rows+=,@{depot=$d;archive=$f.FullName;raw=$p;sha256=(Get-FileHash $p).Hash}}}
}
if($rows.Count -ne 2){throw 'Unexpected ancestry providers'}
$rows|ConvertTo-Json|Set-Content (Join-Path $c 'ancestry_sources_01.json') -Encoding utf8NoBOM
