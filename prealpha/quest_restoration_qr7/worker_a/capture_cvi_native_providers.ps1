param([Parameter(Mandatory=$true)][string]$Output)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$w=(Get-Location).Path
. (Join-Path $w 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $w 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$o=[IO.Path]::GetFullPath((Join-Path $w $Output))
if(Test-Path -LiteralPath $o){throw 'Fresh output required'}
New-Item -ItemType Directory -Path $o|Out-Null
$planPath=Join-Path $PSScriptRoot 'proposal_04/plan.json'
$plan=Get-Content -LiteralPath $planPath -Raw|ConvertFrom-Json
$depots=@('base\open_world\fixers\mr_hands\scenes\mr_hands_new_scenes_activators.questphase','ep1\openworld\fixers\mr_hands\scenes\mr_hands_combat_zone_default.scene','ep1\openworld\fixers\mr_hands\phases\mr_hands_combat_zone_default.questphase','ep1\openworld\ep1_open_world.questphase','ep1\quest\ep1.questphase','base\open_world\street_stories\pacifica\coastview\sts_pac_cvi_02\phases\sts_pac_cvi_02.questphase')
$keys=@{};$expected=@{}
foreach($d in $depots){
 $pin=@($plan.source_pins|Where-Object depot -eq $d)
 if($pin.Count -ne 1){throw ('Missing exact approved donor pin '+$d)}
 if((Get-FileHash -LiteralPath $pin[0].raw).Hash -ne $pin[0].raw_sha256){throw ('Pinned donor changed '+$d)}
 $expected[$d]=$pin[0]
 $keys[[string][WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($d)]=$d
}
$game='C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077'
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$archives=@();$records=@();$i=0
foreach($f in Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc') -Recurse -File -Filter '*.archive'|Sort-Object FullName){
 $before=@($f.Length,$f.LastWriteTimeUtc.Ticks)
 $a=$null;$status=([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($f.FullName,$hs,[ref]$a).ToString()
 if($status -ne 'NoError'){throw ('Unreadable provider archive '+$f.FullName)}
 $hits=@()
 foreach($key in $keys.Keys){
  if(-not $a.Files.ContainsKey([uint64]$key)){continue}
  $d=$keys[$key];$hits+=,$d
  $raw=Join-Path $o ('provider_'+$i+[IO.Path]::GetExtension($d));$i++
  $memory=[IO.MemoryStream]::new()
  try{$a.Files[[uint64]$key].Extract($memory);[IO.File]::WriteAllBytes($raw,$memory.ToArray())}finally{$memory.Dispose()}
  $hash=(Get-FileHash -LiteralPath $raw).Hash
  $row=@{depot=$d;fnv64=$key;provider=$f.FullName;provider_metadata=$before;raw=$raw;raw_sha256=$hash;approved_raw=$expected[$d].raw;approved_raw_sha256=$expected[$d].raw_sha256;matches_approved_donor=($hash -ceq $expected[$d].raw_sha256)}
  if(-not $row.matches_approved_donor){
   try{$json=$raw+'.json';Export-Cr2wJson (Read-Cr2wFile $raw) $json;$row.fresh_json=$json;$row.fresh_json_sha256=(Get-FileHash -LiteralPath $json).Hash;$row.fresh_decode_status='EXPORTED_FOR_EXACT_SEMANTIC_COMPARISON'}catch{$row.fresh_decode_status='BLOCKED';$row.fresh_decode_error=$_.Exception.ToString()}
  }
  $records+=,$row
 }
 $f.Refresh();if($f.Length -ne $before[0] -or $f.LastWriteTimeUtc.Ticks -ne $before[1]){throw 'Provider changed during bounded extraction'}
 $archives+=@{path=$f.FullName;bytes=$before[0];mtime_utc_ticks=$before[1];index_entries=$a.Files.Count;read_status=$status;matches=$hits}
}
foreach($d in $depots){if(@($records|Where-Object depot -eq $d).Count -lt 1){throw ('No current provider for '+$d)}}
$report=@{status='BOUNDED_CURRENT_PROVIDER_EXTRACTION_COMPLETE';scope='Six exact native CVI donor depots only; every current archive index checked and all matching payloads retained. No current-provider winner is guessed from filenames.';approved_plan=$planPath;approved_plan_sha256=(Get-FileHash -LiteralPath $planPath).Hash;depots=$depots;providers=$records;archive_index_inventory=$archives;all_current_matches_approved_donors=(@($records|Where-Object {-not $_.matches_approved_donor}).Count -eq 0);script_sha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash;game_writes=0;candidate_writes=0;save_writes=0}
$report|ConvertTo-Json -Depth 13|Set-Content -LiteralPath (Join-Path $o 'manifest.json') -Encoding utf8NoBOM
Write-Output ('Extracted '+$records.Count+' current provider payloads for6targetdepots across'+$archives.Count+' archives; all exact donor matches='+$report.all_current_matches_approved_donors)
