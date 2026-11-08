$ErrorActionPreference='Stop'
$W=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $W 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $W 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$C=Join-Path $PSScriptRoot 'candidate_01';$G='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
function Arc($p){$a=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($p,$hs,[ref]$a).ToString() -ne 'NoError'){throw 'Archive unreadable'};return $a}
function EH($e){$m=[IO.MemoryStream]::new();try{$e.Extract($m);return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($m.ToArray()))}finally{$m.Dispose()}}
$a=Join-Path $C 'package/archive/pc/mod/zzzz_PTFR_Combined.archive';$before=Arc (Join-Path $G 'archive/pc/mod/zzzz_PTFR_Combined.archive');$after=Arc $a
if($before.Files.Count -ne 1573 -or $after.Files.Count -ne 1574){throw 'Member count'}
foreach($e in $before.Files.Values){if(-not $after.Files.ContainsKey($e.Key) -or (EH $e) -cne (EH $after.Files[$e.Key])){throw 'Changed old resource'}}
$d='towercontinued\phone_studios_ph3\studio_support.questphase';$key=[uint64][WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($d)
if((EH $after.Files[$key]) -cne (Get-FileHash (Join-Path (Join-Path $C 'archive_source') $d)).Hash){throw 'Owner readback mismatch'}
$count=0;foreach($f in Get-ChildItem (Join-Path $G 'archive/pc') -Recurse -Filter '*.archive' -File){$p=Arc $f.FullName;$count++;if($p.Files.ContainsKey($key)){throw 'Owner depot collision'}}
@{status='PASS_FULL_ARCHIVE_READBACK_NO_COLLISION';baseline_members=1573;candidate_members=1574;unchanged_members=1573;archives_scanned=$count;external_lizzies_archive_sha256=(Get-FileHash (Join-Path $G 'archive/pc/mod/LizziesBDs.archive')).Hash}|ConvertTo-Json|Set-Content (Join-Path $C 'verification_01.json') -Encoding utf8NoBOM
'PASS_FULL_ARCHIVE_READBACK_NO_COLLISION'
