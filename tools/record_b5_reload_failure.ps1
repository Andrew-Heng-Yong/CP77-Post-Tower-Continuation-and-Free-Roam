param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
$ErrorActionPreference='Stop'
$audit=Join-Path $WorkspaceRoot 'research\gig_restoration\fresh_b5'
$receipt=Get-Content -LiteralPath (Join-Path $audit 'install_receipt.json') -Raw | ConvertFrom-Json
$live=Join-Path $receipt.game_root 'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_FreshGigsB5/fresh_b5_20261011T200202Z_1.jsonl'
$frozen=Join-Path $audit 'reload_failure_trace_20261011.jsonl'
$result=Join-Path $audit 'reload_failure_result_20261011.json'
if((Test-Path -LiteralPath $frozen) -or (Test-Path -LiteralPath $result)){throw 'Preserve existing evidence'}
$bytes=[IO.File]::ReadAllBytes($live)
$text=[Text.Encoding]::UTF8.GetString($bytes)
$cut=$text.LastIndexOf("`n")
if($cut -lt 0){throw 'No complete log rows'}
$prefix=$text.Substring(0,$cut+1)
$rows=@($prefix.Split("`n") | Where-Object {$_} | ForEach-Object {$_ | ConvertFrom-Json})
if(-not $rows.Count){throw 'Empty trace'}
$failed=@($rows | Where-Object {
 $_.status.sts_wbr_hil_07 -match 'stage=0 ' -and $_.status.sts_wbr_hil_07 -match 'counterAck=false' -and
 $_.status.sts_wbr_hil_01 -match 'stage=0 ' -and $_.facts.PTFRB5_H7_CounterAck -eq 1
})
if(-not $failed.Count){throw 'Reported reload failure not present'}
foreach($r in $failed){
 foreach($suffix in @('Request','Started','OwnerFinished','RewardClaim','RewardAck','AccountRequest','AccountReady','AccountClaim','AccountAck','CounterAck')){
  if($r.facts.PSObject.Properties['PTFRB5_H7_'+$suffix].Value -ne 1){throw ('H7 acknowledgement differs: '+$suffix)}
 }
 if($r.facts.PTFRB5_H7_CountBase -ne 1 -or $r.facts.PTFRB5_H7_AchBase -ne 3 -or
    $r.facts.wbr_sts_counter -ne 2 -or $r.facts.wbr_achievement -ne 4 -or
    $r.facts.PTFRB5_Tier2_Ack -ne 1 -or $r.facts.PTFRB5_H7_Fault -ne 0){throw 'H7 stored facts/counters differ'}
 if($r.facts.PTFRB5_H1_Request -ne 1 -or $r.facts.PTFRB5_H1_Started -ne 1 -or
    $r.facts.PTFRB5_H1_OwnerFinished -ne 0 -or $r.facts.PTFRB5_H1_AccountRequest -ne 0 -or
    $r.facts.PTFRB5_H1_RewardClaim -ne 0 -or $r.facts.PTFRB5_H1_Fault -ne 0){throw 'H1 stored facts differ'}
}
$hashes=@()
foreach($f in $receipt.files){
 $actual=(Get-FileHash -LiteralPath (Join-Path $receipt.game_root $f.relative)).Hash
 if($actual -ne $f.sha256){throw ('Installed file drift: '+$f.relative)}
 $hashes+=,[ordered]@{relative=$f.relative;sha256=$actual;match=$true}
}
$last=$failed[-1]
$hasher=[Security.Cryptography.SHA256]::Create()
try {$prefixHash=[BitConverter]::ToString($hasher.ComputeHash([Text.Encoding]::UTF8.GetBytes($prefix))).Replace('-','')}
finally {$hasher.Dispose()}
$summary=[ordered]@{
 status='B5_USER_RELOAD_FAILED_SCRIPT_BOOKKEEPING_NATIVE_ACKS_PRESERVED'
 source_log=$live;frozen_trace=$frozen
 frozen_prefix_sha256=$prefixHash
 rows=$rows.Count;failure_rows=$failed.Count;first_utc=$rows[0].utc;last_utc=$rows[-1].utc
 error_rows=@($rows | Where-Object {@($_.errors).Count -gt 0}).Count
 user_reported_save_reload=$true;independently_decoded_save=$false
 latest_status=$last.status;latest_facts=$last.facts;latest_journal=$last.journal
 installed_hashes=$hashes
 source_findings=@(
  'FreshSlotB5 has six public let fields without persistent markers; only its enclosing slots array is marked persistent.',
  'Restored does not explicitly clear valid slot members, but PollSlot returns immediately for stage=0.',
  'H7 native-owned baselines 1/3, counter acknowledgement, payout/account acknowledgements and completion survived; the slot reports zero baselines and counterAck=false.',
  'H1 native Request/Started survived, but its stage=0 disables the runtime completion-accounting monitor.',
  'ActivitySnapshot in R3 has the same nested non-persistent-member pattern; production pre-ending history serialization needs a separate audit, not fabricated recovery.')
 causal_assessment='Confirmed missing nested persistence modifiers match documented serializer behavior and observed reset. Exact serialized save bytes were not decoded; lifecycle/schema values are not independently exposed.'
 references=@('https://github.com/psiberx/cp2077-playground/wiki/Save-Data','https://wiki.redmodding.org/scripting-cyberpunk/redscript/language-reference/persistence')
 next_step='Repair nested persistence and narrowly reconstruct B5 tracking from existing owned acknowledgements without reissuing native requests, payouts or credits. Audit R3 history separately; never invent lost pre-ending evidence.'
 user_action='Game may close. Keep original and new test snapshots. Do not replay H7, rerun overrides, or complete H1 before repair.'
 implementation_or_install_performed=$false;game_cache_or_save_files_written=$false
 earlier_route_evidence_preserved=$true;all_gig_restoration_or_alpha_ready=$false
}
[IO.File]::WriteAllText($frozen,$prefix,[Text.UTF8Encoding]::new($false))
[IO.File]::WriteAllText($result,($summary | ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
[pscustomobject]$summary | Select-Object status,rows,failure_rows,error_rows,first_utc,last_utc | ConvertTo-Json
