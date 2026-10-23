# N1 — NCPD scanner pilot playtest

**Update 14 October:** the user reports the activities work. Exact subtype,
completion,call and reload coverage was not specified. The unchanged pilot is
now included beneath the [N2 citywide expansion](ncpd_n2_playtest.md); use that
document's current save and recovery order (**N2 before N1**). The original test
instructions below are retained for pilot-specific follow-up, not a request to
repeat the basic working-activity check.

Original installation record,14 October 2026: initially live pending. Three Little
China encounters, not all Night City scanners. Working fixer-office, gig,
H10 and ending repairs remain installed.

## Load this save

Cold launch and load **AutoSave-6, level 48, 11:14:31 on 14.10.2026**. Identify it
by timestamp, not just slot name. This is the current post-Tower save, not an old
development snapshot. No ending replay, `StartAll`, override or forced facts.

The original three save files were backed up byte-for-byte in
`recovery/ncpd_n1_fixture_20261014/AutoSave-6`; the active save was not edited.
If the autosave slot has since changed, do not assume its contents are the same.

Close CET/menus and let normal play run for roughly 10 seconds. In the map's
Custom filter, enable **NCPD Scanner**, then inspect **Watson → Little China**.
Existing native tier/story gates still apply. These candidates had no serialized
start/finished facts in the checked save; absence alone is not runtime proof.

| Native ID | Type | What the test must establish |
|---|---|---|
| `ma_wat_lch_01` | Suspected Organized Crime | Gang encounter, dispatcher briefing, evidence and native completion |
| `ma_wat_lch_02` | Assault in Progress | Actual enemies/evidence, native completion and payout |
| `ma_wat_lch_03` | Reported Crime | Initial evidence and original follow-up trail/stash objectives |

For a short first check, visit one new scanner marker and confirm the encounter
is populated and evidence is interactable. A visible icon alone is not a pass.
These are native scanner markers, not three forced entries in the main Journal.
The Reported Crime's follow-up objectives activate through its original clues.

## Read-only status if needed

Paste commands, not their printed output, into CET. No new periodic logging is
installed.

```lua
local q=Game.GetQuestsSystem(); for _,id in ipairs({"ma_wat_lch_01","ma_wat_lch_02","ma_wat_lch_03"}) do local p="PTFRN1_"..id; print(id.." ready/issued/output/refused="..q:GetFactStr(p.."_Ready").."/"..q:GetFactStr(p.."_Issued").."/"..q:GetFactStr(p.."_NativeOutput").."/"..q:GetFactStr(p.."_Refused").." native start/finished="..q:GetFactStr(id.."_start").."/"..q:GetFactStr(id.."_finished")) end
```

```lua
local q=Game.GetQuestsSystem(); for _,f in ipairs({"PTFRN1_Support_Ready","PTFRN1_Support_Issued","PTFRU9_Support_Issued","PTFRU9_Support_Fault","ma_token","sts_wat_lch_tier_1","q101_enable_side_content","wat_achievement","holo_setup_active","holo_setup_started","holo_ncpd_dispatcher_calls_v_start_activate","holo_ncpd_dispatcher_calls_v_start_count","holo_ncpd_dispatcher_calls_v_end_count"}) do print(f.."="..q:GetFactStr(f)) end
```

Expected before approaching an admitted, unstarted encounter:
`ready/issued/output/refused=1/1/0/0`, native `start/finished=0/0`.
Being near a trigger can already change `start`. After original completion,
`NativeOutput=1` and `finished=1` are expected; the native departure/time cleanup
can still be running. **Issued is permission/entry bookkeeping, not proof that
spawning, the phone scene or icons worked.**

If issued stays zero, send the read-only output. Do not clear facts to make it
start. Already-started or completed encounters are intentionally excluded.

## Completion and regression checklist

- [ ] Each of the three types has actual encounter content, not an empty marker.
- [ ] Organized Crime: native dispatcher call/text behavior works; phone exits
  cleanly. Existing gig calls still work after this call.
- [ ] Assault: enemies and evidence can be resolved normally; marker completes.
- [ ] Reported Crime: initial clue starts the correct follow-up, destination
  evidence resolves it, and there is no orphaned objective.
- [ ] Record money/XP and `wat_achievement` before and after each isolated
  completion. Let native rewards run; no repeated payout or achievement credit.
  Do not finish another Watson activity while measuring the counter.
- [ ] Leave the encounter, allow its native time/departure cleanup, then return.
  A completed site must not restart or reward again. LCH02 uses a 24-game-hour
  cleanup wait; LCH03 uses three game hours plus leaving both relevant areas.
  Do not treat waiting cleanup as a request to reset the quest.
- [ ] Make a **new** save while an encounter is active; reload and verify it
  continues without a duplicate owner or reset. Keep the baseline fixture.
- [ ] Make another new save after completion; reload, revisit and verify no
  replay/reward/counter duplication. Read-only issued flag should remain one.
- [ ] Completed scanner controls and all previously completed cyberpsychos stay
  completed. No renewed Regina reports or duplicate cyberpsycho reward.
- [ ] Wakako conversation, existing gigs, H10 and camera behavior remain intact;
  no added CET chatter.
- [ ] Later fresh-ending integration: nothing starts during Tower/credits;
  post-handoff admission works. **Not needed for this first short test.**

Current guards use native start/finish facts and saved N1 ownership. They are not
a certified pre-Tower history snapshot. Partially completed encounters,
citywide scanners, races, side jobs, airdrops and car contracts are not added by
N1. Expand the scanner batch after the representative native flows are verified.

## Recovery

After recovering N2 if installed, with the game closed recover N1 using
`prealpha/ncpd_scanner_n1/deploy.ps1` ValidateRollback then Rollback with
`recovery/ncpd_scanner_n1_01`. It recoverably removes only the two N1 additions,
returning to FO1+PA6+GD2. Then use older recovery transactions if necessary.
Removing mod files does not undo gameplay already saved after installation;
retain the pre-test save for a clean rollback test.

Evidence: `research/ncpd_scanner_n1/assessment.json` and
`prealpha/ncpd_scanner_n1/build/n1_01/`. The later user-reported functional pass is
recorded separately in `research/ncpd_scanner_n1/live_result_20261014.json`.
