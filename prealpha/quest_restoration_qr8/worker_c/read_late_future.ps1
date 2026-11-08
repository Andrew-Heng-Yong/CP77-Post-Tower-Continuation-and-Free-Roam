param([string]$Output='reviews/late_future_01/readback')
$ErrorActionPreference='Stop'
$ws=(Get-Location).Path;$own=Join-Path $ws 'prealpha/quest_restoration_qr8/worker_c';$dest=[IO.Path]::GetFullPath((Join-Path $own $Output))
if(-not $dest.StartsWith($own+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'Output containment'}
if(Test-Path -LiteralPath $dest){throw 'Fresh output required'}
New-Item -ItemType Directory -Path $dest | Out-Null
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$source=Join-Path $ws 'prealpha/quest_restoration_qr8/worker_b';$e=Get-Content -Raw -LiteralPath (Join-Path $source 'late_future_verification_02/evidence.json')|ConvertFrom-Json
$manifest=Get-Content -Raw -LiteralPath (Join-Path $source 'proposal_late_future_03/NOT_FOR_INTEGRATION.json')|ConvertFrom-Json
$targets=@($e.source_pins|Where-Object {$_.depot -ceq 'towercontinued\quest_restoration_qr7\ronald_news_future.questphase' -or $_.depot -ceq 'ep1\quest\main_quests\q302\phases\q302_ronald_tree.questphase' -or $_.depot -cmatch '^towercontinued\\native_gigs_u9\\sts_ep1_(01|03|08|12)_entry\.questphase$' -or $_.depot -cmatch '^ep1\\openworld\\street_stories\\sts_ep1_(01|03|08|12)\\phases\\'})
$targets+=@{depot='PRIVATE_PROPOSAL';raw=$manifest.raw;raw_sha256=$manifest.raw_sha256}
$results=@();$index=0
foreach($t in $targets){
 if((Get-FileHash -LiteralPath $t.raw).Hash -cne $t.raw_sha256){throw 'Raw input drift'}
 $file=Read-Cr2wFile $t.raw;$json=Join-Path $dest ('resource_'+$index+'.json');$index++
 Export-Cr2wJson $file $json
 $results+=@{depot=$t.depot;raw=$t.raw;raw_sha256=$t.raw_sha256;json=$json;json_sha256=(Get-FileHash -LiteralPath $json).Hash}
}
@{resources=$results;status='INDEPENDENT_READBACK_NO_RAW_SERIALIZATION';runtime_writes=0;source_manifest_sha256=(Get-FileHash -LiteralPath (Join-Path $source 'proposal_late_future_03/NOT_FOR_INTEGRATION.json')).Hash}|ConvertTo-Json -Depth 6|Set-Content -LiteralPath (Join-Path $dest 'manifest.json') -Encoding utf8
@{readbacks=$results.Count;output=$dest}|ConvertTo-Json -Compress
