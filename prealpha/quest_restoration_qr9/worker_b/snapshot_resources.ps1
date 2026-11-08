param([string]$OutputName='resource_readbacks_01')
$ErrorActionPreference='Stop'
$ws=(Get-Location).Path;$taskDir=Join-Path $ws 'prealpha/quest_restoration_qr9/worker_b';$out=Join-Path $taskDir $OutputName
if(Test-Path -LiteralPath $out){throw 'Fresh output required'}
New-Item -ItemType Directory -Path $out|Out-Null
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$ep=Get-Content -Raw -LiteralPath (Join-Path $ws 'prealpha/quest_restoration_qr8/source_epoch_02.json')|ConvertFrom-Json
$depots=@('towercontinued\native_gigs_u9\sts_pac_cvi_02_entry.questphase','towercontinued\quest_restoration_qr7\ronald_news_future.questphase','towercontinued\sidejobs_s29\entries\mq060_nitro.questphase','towercontinued\sidejobs_s23\base_a\mq007_smartgun.questphase','towercontinued\sidejobs_s23\base_a_v2\mq007_resume_boot.questphase','towercontinued\sidejobs_s23\base_b\mq030.questphase','towercontinued\sidejobs_s23\base_b\mq037.questphase')
foreach($s in @('01','03','08','12')){$depots+=('towercontinued\native_gigs_u9\sts_ep1_'+$s+'_entry.questphase')}
$rows=@();$i=0
foreach($d in $depots){
 $hash=$ep.source_resources.$d;if(-not $hash){throw ('Unknown actual source '+$d)}
 $raw=Join-Path (Join-Path $ep.candidate 'archive_source') $d
 if((Get-FileHash -LiteralPath $raw).Hash -cne $hash){throw 'Current source drift'}
 $json=Join-Path $out ('resource_'+$i+'.json');Export-Cr2wJson (Read-Cr2wFile $raw) $json
 $rows+=@{depot=$d;raw=$raw;raw_sha256=$hash;json=$json;json_sha256=(Get-FileHash -LiteralPath $json).Hash};$i++
}
ConvertTo-Json -InputObject @($rows) -Depth 8|Set-Content -LiteralPath (Join-Path $out 'manifest.json') -Encoding utf8
Write-Output ('Read-only targeted signal source exports '+$rows.Count)
