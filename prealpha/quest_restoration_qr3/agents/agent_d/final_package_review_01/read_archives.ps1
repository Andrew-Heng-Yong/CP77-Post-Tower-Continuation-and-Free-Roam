Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$W=Split-Path (Split-Path (Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent) -Parent) -Parent
$Q=Join-Path $W 'prealpha/quest_restoration_qr3'
$O=Join-Path $PSScriptRoot 'evidence'
if(Test-Path -LiteralPath $O){throw 'Fresh independent review output required'}
$old=Join-Path $W 'prealpha/phone_studios_ph3/candidate_01/package/archive/pc/mod/zzzz_PTFR_Combined.archive'
$new=Join-Path $Q 'candidate_01/package/archive/pc/mod/zzzz_PTFR_Combined.archive'
if((Get-FileHash -LiteralPath $old).Hash -cne '18B855B55A62771F146B9BA518F8DB782832606AA7666755303EEBA91D9F66C7'){throw 'Unpinned PH3 archive'}
$plan=Get-Content -LiteralPath (Join-Path $Q 'approved_changes_02.json') -Raw|ConvertFrom-Json -Depth 30
if(@($plan.resources).Count -ne 2){throw 'Expected exactly two reviewed repairs'}
. (Join-Path $W 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $W 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
function Open-ReviewArchive($path){$a=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($path,$hs,[ref]$a).ToString() -ne 'NoError'){throw 'Archive unreadable'};return $a}
function Hash-ReviewEntry($entry){$m=[IO.MemoryStream]::new();try{$entry.Extract($m);return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($m.ToArray()))}finally{$m.Dispose()}}
$a=Open-ReviewArchive $old;$b=Open-ReviewArchive $new
if($a.Files.Count -ne 1574 -or $b.Files.Count -ne 1574){throw 'Member inventory changed'}
$expected=@{}
foreach($r in $plan.resources){$k=([uint64][WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($r.depot)).ToString();$expected[$k]=$r}
$rows=@();$changes=@()
foreach($key in $a.Files.Keys){
 if(-not $b.Files.ContainsKey($key)){throw 'Missing or replaced depot key'}
 $before=Hash-ReviewEntry $a.Files[$key];$after=Hash-ReviewEntry $b.Files[$key]
 $row=@{key=$key.ToString();before=$before;after=$after;changed=($before -cne $after)};$rows+=,$row
 if($row.changed){
  $r=$expected[$key.ToString()]
  if($null -eq $r -or $r.before -cne $before -or $r.after -cne $after){throw 'Unapproved packaged payload delta'}
  $raw=Join-Path (Join-Path $Q 'candidate_01/archive_source') $r.depot
  if((Get-FileHash -LiteralPath $raw).Hash -cne $after){throw 'Packaged bytes differ from independently reviewed serialized resource'}
  $changes+=,@{depot=$r.depot;key=$key.ToString();before=$before;after=$after}
 }
}
if($changes.Count -ne 2){throw 'Expected two actual byte changes'}
[IO.Directory]::CreateDirectory($O)|Out-Null
@{status='PASS_INDEPENDENT_ACTUAL_ARCHIVE_COMPARISON';member_count=$a.Files.Count;keyset_identical=$true;changed_count=$changes.Count;unchanged_payload_count=1572;changed_resources=$changes;resources=$rows;baseline_archive=$old;baseline_sha256=(Get-FileHash -LiteralPath $old).Hash;candidate_archive=$new;candidate_sha256=(Get-FileHash -LiteralPath $new).Hash;method='Independent ArchiveReader extraction of actual pinned PH3 versus staged archive, not packer expected-source table';game_writes=0;save_writes=0}|ConvertTo-Json -Depth 40|Set-Content -LiteralPath (Join-Path $O 'archive_review.json') -Encoding utf8NoBOM
@{status='PASS';members=1574;changed=2;unchanged=1572}|ConvertTo-Json
