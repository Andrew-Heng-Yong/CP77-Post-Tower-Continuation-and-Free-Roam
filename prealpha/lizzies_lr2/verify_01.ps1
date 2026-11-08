Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$c=Join-Path $PSScriptRoot 'candidate_01';$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
function Archive($p){$a=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($p,$hs,[ref]$a).ToString() -ne 'NoError'){throw "Archive unreadable $p"};return $a}
function EntryHash($e){$m=[IO.MemoryStream]::new();try{$e.Extract($m);return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($m.ToArray()))}finally{$m.Dispose()}}
$before=Archive 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\mod\zzzz_PTFR_Combined.archive'
$after=Archive (Join-Path $c 'package/archive/pc/mod/zzzz_PTFR_Combined.archive')
if($before.Files.Count -ne 1565 -or $after.Files.Count -ne 1566){throw 'Archive size unexpected'}
$unchanged=0
foreach($e in $before.Files.Values){if(-not $after.Files.ContainsKey($e.Key)){throw "Missing $($e.Name)"};if((EntryHash $e) -cne (EntryHash $after.Files[$e.Key])){throw "Changed $($e.Name)"};$unchanged++}
$depot='towercontinued\lizzies_lr2\club_support.questphase';$key=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot)
if(-not $after.Files.ContainsKey([uint64]$key)){throw 'New owner absent'}
if((EntryHash $after.Files[[uint64]$key]) -cne (Get-FileHash -LiteralPath (Join-Path $c ('archive_source/'+$depot))).Hash){throw 'New owner readback mismatch'}
$others=@(Get-ChildItem -LiteralPath 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc' -Filter '*.archive' -Recurse -File|Where-Object {$_.Name -ne 'zzzz_PTFR_Combined.archive'})
foreach($f in $others){if((Archive $f.FullName).Files.ContainsKey([uint64]$key)){throw "New resource collision $($f.FullName)"}}
$sem=Get-Content -LiteralPath (Join-Path $c 'semantic_verification_01.json') -Raw|ConvertFrom-Json
if($sem.status -cne 'PASS_NATIVE_BINDINGS_AND_SERIALIZED_OWNER'){throw 'Native/owner validation failed'}
$xl=Get-Content -LiteralPath (Join-Path $c 'package/archive/pc/mod/zzzz_PTFR_Combined.archive.xl') -Raw
if($xl.Split($depot).Count -ne 2 -or -not $xl.Contains('parent: ep1\quest\ep1.quest')){throw 'XL injection missing or duplicated'}
@{status='PASS_FULL_ARCHIVE_READBACK_NO_COLLISION';baseline_members=1565;unchanged_members=$unchanged;candidate_members=1566;archives_scanned=$others.Count+1;new_depot=$depot;external_lizzies_archive_sha256=(Get-FileHash -LiteralPath 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\mod\LizziesBDs.archive').Hash}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $c 'verification_01.json') -Encoding utf8NoBOM
Get-Content -LiteralPath (Join-Path $c 'verification_01.json')
