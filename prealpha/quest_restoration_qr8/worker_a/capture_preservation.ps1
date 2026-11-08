param([Parameter(Mandatory=$true)][string]$Output)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$taskRoot=(Get-Location).Path
. (Join-Path $taskRoot 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $taskRoot 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$taskOut=[IO.Path]::GetFullPath((Join-Path $taskRoot $Output))
if(-not $taskOut.StartsWith((Join-Path $taskRoot 'prealpha/quest_restoration_qr8/worker_a')+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'Worker output scope'}
if(Test-Path -LiteralPath $taskOut){throw 'Fresh output required'}
New-Item -ItemType Directory -Path $taskOut|Out-Null
$candidate=Join-Path $taskRoot 'prealpha/quest_restoration_qr7/candidate_01/archive_source'
$depots=@('towercontinued\sidejobs_s23\base_b\mq037.questphase','towercontinued\sidejobs_s23\base_b\mq030.questphase','towercontinued\sidejobs_s23\base_a\mq007_smartgun.questphase','towercontinued\sidejobs_s23\base_a_v2\mq007_resume_boot.questphase','towercontinued\phone_merge_ph2\mark_bana_listener.questphase','towercontinued\gig_phone_u9\fixer_cleanup.questphase','towercontinued\phone_studios_ph3\studio_support.questphase','towercontinued\native_gigs_u9\sts_ep1_08_entry.questphase')
$rows=@();$ordinal=0
foreach($depot in $depots){
 $source=Join-Path $candidate $depot;$f=Get-Item -LiteralPath $source;$before=@($f.Length,$f.LastWriteTimeUtc.Ticks);$hash=(Get-FileHash -LiteralPath $source).Hash
 $raw=Join-Path $taskOut ("{0:D2}.questphase" -f $ordinal);$ordinal++;Copy-Item -LiteralPath $source -Destination $raw
 if((Get-FileHash -LiteralPath $raw).Hash -ne $hash){throw 'Copy mismatch'}
 $json=$raw+'.json';Export-Cr2wJson (Read-Cr2wFile $raw) $json
 $f.Refresh();if($f.Length -ne $before[0] -or $f.LastWriteTimeUtc.Ticks -ne $before[1]){throw 'Input changed'}
 $rows+=,@{depot=$depot;source=$source;raw_sha256=$hash;source_size=$before[0];source_mtime_utc_ticks=$before[1];raw=$raw;json=$json;json_sha256=(Get-FileHash -LiteralPath $json).Hash}
}
@{status='FRESH_READ_ONLY_TYPED_CAPTURES';resources=$rows;script_sha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash;game_writes=0;candidate_writes=0}|ConvertTo-Json -Depth 12|Set-Content -LiteralPath (Join-Path $taskOut 'manifest.json') -Encoding utf8NoBOM
'Captured8 exact resource readbacks'
