param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
$ErrorActionPreference='Stop'
$audit=Join-Path $WorkspaceRoot 'research\gig_restoration\fresh_b5_1'
$receipt=Get-Content -LiteralPath (Join-Path $audit 'install_receipt.json') -Raw|ConvertFrom-Json
$live=Join-Path $receipt.game_root 'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_FreshGigsB5/fresh_b5_20261011T202635Z_1.jsonl'
$frozen=Join-Path $audit 'reload_pass_trace_20261011.jsonl'
$result=Join-Path $audit 'reload_pass_result_20261011.json'
if((Test-Path -LiteralPath $frozen) -or (Test-Path -LiteralPath $result)){throw 'Preserve existing evidence'}
$bytes=[IO.File]::ReadAllBytes($live)
$text=[Text.Encoding]::UTF8.GetString($bytes);$cut=$text.LastIndexOf("`n")
if($cut -lt 0){throw 'No complete rows'}
$prefix=$text.Substring(0,$cut+1)
$rows=@($prefix.Split("`n")|Where-Object {$_}|ForEach-Object {$_|ConvertFrom-Json})
function Persisted($r){
 return $r.status.sts_wbr_hil_07 -match 'stage=4 ' -and
  $r.status.sts_wbr_hil_07 -match 'counterAck=true baseCount/Ach=1/3 current=2/4' -and
  $r.status.sts_wbr_hil_01 -match 'stage=3 ' -and
  $r.status.sts_wbr_hil_07.Contains(' |  | certifiedFreshHistory=false') -and
  $r.status.sts_wbr_hil_01.Contains(' |  | certifiedFreshHistory=false')
}
if(-not $rows.Count -or -not (Persisted $rows[-1])){throw 'Expected persisted terminal/running tracking and cleared volatile details'}
$start=$rows.Count-1
while($start -gt 0 -and (Persisted $rows[$start-1])){$start-=1}
$stable=@($rows[$start..($rows.Count-1)])
foreach($r in $stable){
 foreach($suffix in @('Request','Started','OwnerFinished','RewardClaim','RewardAck','AccountRequest','AccountReady','AccountClaim','AccountAck','CounterAck')){
  if($r.facts.PSObject.Properties['PTFRB5_H7_'+$suffix].Value -ne 1){throw ('H7 acknowledgement drift: '+$suffix)}
 }
 if($r.facts.PTFRB5_H7_CountBase -ne 1 -or $r.facts.PTFRB5_H7_AchBase -ne 3 -or $r.facts.hil_07_finished -ne 1 -or $r.facts.PTFRB5_H7_Fault -ne 0 -or
    $r.facts.PTFRB5_H1_Request -ne 1 -or $r.facts.PTFRB5_H1_Started -ne 1 -or $r.facts.PTFRB5_H1_OwnerFinished -ne 0 -or $r.facts.hil_01_finished -ne 0 -or $r.facts.PTFRB5_H1_Fault -ne 0){throw 'Owner/native outcome drift'}
 foreach($suffix in @('RewardClaim','RewardAck','AccountRequest','AccountReady','AccountClaim','AccountAck','CountBase','AchBase','CounterAck')){
  if($r.facts.PSObject.Properties['PTFRB5_H1_'+$suffix].Value -ne 0){throw ('H1 unexpected credit/progress: '+$suffix)}
 }
 if($r.facts.wbr_sts_counter -ne 2 -or $r.facts.wbr_achievement -ne 4 -or $r.facts.PTFRB5_Tier2_Ack -ne 1){throw 'Counter/tier drift'}
}
$hashes=@()
foreach($f in $receipt.files){$h=(Get-FileHash -LiteralPath (Join-Path $receipt.game_root $f.relative)).Hash;if($h -ne $f.sha256){throw ('Installed drift: '+$f.relative)};$hashes+=,[ordered]@{relative=$f.relative;sha256=$h;match=$true}}
$hasher=[Security.Cryptography.SHA256]::Create()
try{$prefixHash=[BitConverter]::ToString($hasher.ComputeHash([Text.Encoding]::UTF8.GetBytes($prefix))).Replace('-','')}finally{$hasher.Dispose()}
$summary=[ordered]@{
 status='B5_1_LEGACY_ADOPTION_AND_NEW_SAVE_RELOAD_USER_GETTER_PASS'
 source_log=$live;frozen_trace=$frozen;frozen_prefix_sha256=$prefixHash
 rows=$rows.Count;first_utc=$rows[0].utc;last_utc=$rows[-1].utc
 legacy_adoption_rows=@($rows|Where-Object {$_.status.sts_wbr_hil_07 -like '*adopted saved owned acknowledgements*'}).Count
 final_persisted_rows=$stable.Count;first_final_persisted_utc=$stable[0].utc
 error_rows=@($rows|Where-Object {@($_.errors).Count -gt 0}).Count
 latest_status=$rows[-1].status;latest_facts=$rows[-1].facts;latest_journal=$rows[-1].journal
 installed_hashes=$hashes
 user_report=[ordered]@{legacy_snapshot_recovered=$true;original_snapshot_reload_adopts_again_expected=$true;separate_new_save_created_and_reloaded=$true;volatile_adoption_details_cleared=$true}
 interpretation=@('Legacy snapshots require adoption each time because they do not contain the later recovered script values.',
  'USER explicitly confirms separate NEW save/reload. Final stable getter suffix retains H7 stage4/counterAcktrue/baselines1/3, H1 stage3, unchanged ledger/tier/counters2/4, and cleared volatile recovery details.',
  'This closes the tested legacy-adoption/new-save-reload milestone, not independently decoded save serialization, all interrupted states or full cold-process restart.',
  'H7 freshJournal/freshFacts false after completion and H1 inactive root1 before encounter approach are expected. Unknown certifiedFreshHistory=false remains unknown.',
  'No code/install/runtime native writes/cache/direct-save writes or pinned main reruns by this evidence audit.')
 pending=@('B5 batch live dispatch confirmation','Distant marker/discovery presentation','H1 encounter/completion/payout/cleanup gameplay','R3 pre-ending history serialization and ending transition','Other67 gig adapters/all completed replay/fullalpha')
 immediate_gameplay_or_restart_required=$false;user_may_close_game=$true
 independently_decoded_save=$false;all_gig_restoration_or_alpha_ready=$false
}
[IO.File]::WriteAllText($frozen,$prefix,[Text.UTF8Encoding]::new($false))
[IO.File]::WriteAllText($result,($summary|ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
[pscustomobject]$summary|Select-Object status,rows,legacy_adoption_rows,final_persisted_rows,first_final_persisted_utc,last_utc,error_rows|ConvertTo-Json
