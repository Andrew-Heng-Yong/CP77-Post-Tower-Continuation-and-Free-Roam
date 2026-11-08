param([Parameter(Mandatory=$true)][string]$OutputRoot)
$ErrorActionPreference='Stop';$w=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $w 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $w 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$o=[IO.Path]::GetFullPath($OutputRoot);if(-not $o.StartsWith((Join-Path $w 'diagnostics')+'\')){throw 'Unsafe output'}
if(Test-Path (Join-Path $o 'parents.json')){throw 'Preserve capture'}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$d='ep1\quest\ep1.quest';$key=[uint64][WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($d);$rows=@()
foreach($f in Get-ChildItem 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc' -Recurse -Filter '*.archive' -File){$a=$null;[void]([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($f.FullName,$hs,[ref]$a);if($a.Files.ContainsKey($key)){$p=Join-Path $o ('parents/'+$f.BaseName+'/ep1.quest');New-Item -ItemType Directory -Force (Split-Path $p -Parent)|Out-Null;$m=[IO.MemoryStream]::new();$a.Files[$key].Extract($m);[IO.File]::WriteAllBytes($p,$m.ToArray());$m.Dispose();Export-Cr2wJson (Read-Cr2wFile $p) ($p+'.json');$rows+=,@{depot=$d;archive=$f.FullName;raw=$p;json=$p+'.json';sha256=(Get-FileHash $p).Hash;json_sha256=(Get-FileHash ($p+'.json')).Hash;stock=$f.DirectoryName -notlike '*\mod*';status='DECODED_PARENT_METADATA_ONLY'}}}
$rows|ConvertTo-Json -Depth 5|Set-Content (Join-Path $o 'parents.json') -Encoding utf8NoBOM
