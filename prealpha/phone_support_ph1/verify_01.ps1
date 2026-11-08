Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$W=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $W 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $W 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$C=Join-Path $PSScriptRoot 'candidate_03';$B=Join-Path $W 'prealpha/lizzies_lr2/candidate_01'
$build=Get-Content (Join-Path $C 'build_01.json') -Raw|ConvertFrom-Json -Depth 100
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
function Archive($p){$a=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($p,$hs,[ref]$a).ToString() -ne 'NoError'){throw "Read failure $p"};return $a}
function Key($d){return [uint64][WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($d)}
function EH($e){$m=[IO.MemoryStream]::new();try{$e.Extract($m);return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($m.ToArray()))}finally{$m.Dispose()}}
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077';$before=Archive (Join-Path $game 'archive/pc/mod/zzzz_PTFR_Combined.archive');$after=Archive (Join-Path $C 'package/archive/pc/mod/zzzz_PTFR_Combined.archive')
if($before.Files.Count -ne 1566 -or $after.Files.Count -ne 1572){throw 'Archive counts'}
$changed=@{};foreach($p in $build.resources.PSObject.Properties){$changed[(Key $p.Name)]=$p.Name}
$same=0;$diff=0
foreach($e in $before.Files.Values){if(-not $after.Files.ContainsKey($e.Key)){throw 'Deleted member'};if((EH $e) -cne (EH $after.Files[$e.Key])){if(-not $changed.ContainsKey($e.Key)){throw 'Unplanned resource change'};$diff++;$d=$changed[$e.Key];Export-Cr2wJson (Read-Cr2wFile (Join-Path (Join-Path $B 'archive_source') $d)) (Join-Path $C ('before_'+$d.Replace('\','_')+'.json'))}else{$same++}}
if($diff -ne 4){throw 'Expected four changed old resources'}
foreach($p in $build.resources.PSObject.Properties){if((EH $after.Files[(Key $p.Name)]) -cne $p.Value){throw 'Packed source mismatch'}}
$pins=@{};foreach($p in $build.native_pins.PSObject.Properties){$pins[$p.Name]=$p.Value}
foreach($case in $build.contracts.source){foreach($n in @('controller','cleanup','holocall_scene')){$pins[$case.$n.depot]=$case.$n.sha256}}
foreach($d in @('base\quest\cyberpunk2077.questphase','ep1\quest\ep1.questphase','ep1\quest\main_quests\q307\q307.quest')){$p=Join-Path (Join-Path $W 'research/q307_extracted/raw') $d;$pins[$d]=(Get-FileHash $p).Hash;Export-Cr2wJson (Read-Cr2wFile $p) (Join-Path $C ($d.Replace('\','_')+'.json'))}
$hits=@{};foreach($d in $pins.Keys){$hits[$d]=@()};$count=0
foreach($f in Get-ChildItem (Join-Path $game 'archive/pc') -Recurse -Filter '*.archive' -File){$a=Archive $f.FullName;$count++;foreach($d in $build.boots){if($a.Files.ContainsKey((Key $d))){throw "New depot collision $d"}};foreach($d in $pins.Keys){if($a.Files.ContainsKey((Key $d))){$hash=EH $a.Files[(Key $d)];if($hash -cne $pins[$d]){throw "Native source changed $d"};$hits[$d]+=,$f.FullName}}}
foreach($d in $hits.Keys){if($hits[$d].Count -ne 1){throw "Ambiguous provider $d"}}
@{status='PASS_FULL_ARCHIVE_READBACK_NO_COLLISION';baseline_members=1566;candidate_members=1572;unchanged_members=$same;changed_old_members=$diff;archives_scanned=$count;native_providers=$hits;external_lizzies_archive_sha256=(Get-FileHash (Join-Path $game 'archive/pc/mod/LizziesBDs.archive')).Hash}|ConvertTo-Json -Depth 10|Set-Content (Join-Path $C 'verification_01.json') -Encoding utf8NoBOM
Get-Content (Join-Path $C 'verification_01.json') -TotalCount 7
