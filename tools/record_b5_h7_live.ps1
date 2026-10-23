param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
$ErrorActionPreference='Stop'
$audit=Join-Path $WorkspaceRoot 'research\gig_restoration\fresh_b5'
$live='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_FreshGigsB5\fresh_b5_20261011T193336Z_1.jsonl'
$frozen=Join-Path $audit 'live_trace_h7_20261011.jsonl'
$result=Join-Path $audit 'live_result_h7_20261011.json'
if((Test-Path $frozen) -or (Test-Path $result)){throw 'Preserve existing evidence'}
$bytes=[IO.File]::ReadAllBytes($live)
$text=[Text.Encoding]::UTF8.GetString($bytes);$cut=$text.LastIndexOf("`n")
if($cut -lt 0){throw 'No complete log rows'}
$prefix=$text.Substring(0,$cut+1)
$rows=@($prefix.Split("`n") | Where-Object {$_} | ForEach-Object {$_ | ConvertFrom-Json})
if(-not $rows.Count){throw 'Empty trace'}
$done=@($rows | Where-Object {$_.status.sts_wbr_hil_07 -match 'stage=4 '})
if(-not $done.Count){throw 'No completed H7 sample'}
foreach($r in $done){
 foreach($f in @('PTFRB5_H7_Started','PTFRB5_H7_OwnerFinished','PTFRB5_H7_RewardClaim','PTFRB5_H7_RewardAck','PTFRB5_H7_AccountClaim','PTFRB5_H7_AccountAck','PTFRB5_H7_CounterAck','PTFRB5_Tier2_Ack')){
  if($r.facts.$f -ne 1){throw "Terminal acknowledgement changed: $f"}
 }
 if($r.facts.PTFRB5_H7_Fault -ne 0 -or $r.facts.wbr_sts_counter -ne 2 -or $r.facts.wbr_achievement -ne 4){throw 'Terminal fault/counter drift'}
}
$receipt=Get-Content (Join-Path $audit 'install_receipt.json') -Raw | ConvertFrom-Json
$hashes=@();foreach($f in $receipt.files){
 $actual=(Get-FileHash -LiteralPath (Join-Path $receipt.game_root $f.relative)).Hash
 if($actual -ne $f.sha256){throw ('Installed file drift: '+$f.relative)}
 $hashes+=,[ordered]@{relative=$f.relative;sha256=$actual;match=$true}
}
$firstPoi=@($rows | Where-Object {$_.journal.'points_of_interest/street_stories/sts_wbr_hil_07' -eq 2}) | Select-Object -First 1
$firstQuest=@($rows | Where-Object {$_.journal.'quests/street_stories/wesbrook/charter_hill/sts_wbr_hil_07' -eq 2}) | Select-Object -First 1
$last=$rows[-1]
[IO.File]::WriteAllText($frozen,$prefix,[Text.UTF8Encoding]::new($false))
$summary=[ordered]@{
 status='H7_TESTED_SUCCESS_ROUTE_USER_AND_GETTER_PASS_RELOAD_PENDING'
 source_log=$live;frozen_trace=$frozen;frozen_prefix_sha256=(Get-FileHash $frozen).Hash
 rows=$rows.Count;first_utc=$rows[0].utc;last_utc=$last.utc;first_terminal_utc=$done[0].utc;terminal_rows=$done.Count
 error_rows=@($rows | Where-Object {$_.errors -and @($_.errors.PSObject.Properties).Count -gt 0}).Count
 fixer_values=@($rows.facts.wbr_sts_counter | Select-Object -Unique);achievement_values=@($rows.facts.wbr_achievement | Select-Object -Unique)
 first_poi_active=[ordered]@{utc=$firstPoi.utc;position=$firstPoi.position;status=$firstPoi.status.sts_wbr_hil_07}
 first_quest_active=[ordered]@{utc=$firstQuest.utc;position=$firstQuest.position;status=$firstQuest.status.sts_wbr_hil_07}
 terminal_h7=$last.status.sts_wbr_hil_07;latest_h1=$last.status.sts_wbr_hil_01;installed_hashes=$hashes
 user_report=[ordered]@{completed_h7=$true;marker_appeared_only_after_teleport=$true;new_save_reload_reported=$false}
 interpretation=@('H7 native completion/output, reward/account acknowledgements, independent fixer 1->2 and achievement 3->4, and tier-2 acknowledgement observed once on this trace.',
  'Native POI Active is a journal state, not renderer/map-icon visibility proof. USER reports no marker until teleport/approach; distant discovery remains unresolved.',
  'H1 queue gained earned eligibility and subsequently reached stage 3; H1 encounter activation/completion/payout are not proven.',
  'freshJournal/freshFacts false after H7 completion is expected. Unknown pre-ending certification remains false under explicit override.',
  'No native writes, save/cache/deployment changes or predecessor main reruns by this audit. Frozen hash covers captured complete prefix, not the mutable whole live log.')
 pending=@('H7 separate NEW save/reload persistence','H1 gameplay/completion/cleanup/reload','B5 batch EntityID-string guard fix; direct per-ID commands are the current workaround',
  'Far-distance marker/discovery presentation','Exact cash/XP attribution and alternate routes/baselines','Automatic ending-history production integration','Other 67 approved gig adapters and all completed replay')
 all_gig_restoration_or_alpha_ready=$false
}
[IO.File]::WriteAllText($result,($summary | ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
[pscustomobject]$summary | Select-Object status,rows,first_utc,last_utc,first_terminal_utc,terminal_rows,error_rows,fixer_values,achievement_values | ConvertTo-Json -Depth 5
