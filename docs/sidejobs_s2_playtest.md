# S2 — first native side-job batch

**Superseded current instructions:** see [S22 progress-preserving restoration](sidejobs_s22_playtest.md).
The latest user rule is Failed **or Inactive** after Tower, preserving halfway
progress. Future selection uses actual Inactive pre-Tower history. The sections
below describe the historical S2/S21 diagnostic rollout, not the current policy.

**15 October follow-up:** live inspection found Sacrum fresh but unauthorized:
`ready/permit/issued/finished=1/0/0/0`, `currentFresh=true`, `certified=false`,
`development=false`. The earlier post-Tower save recommendation did not establish
development authorization. Approach alone cannot fix that condition. PA1's
development getter can be false either without its late-ending flag or when PA1
is certified; the supplied S2 output does not distinguish those cases.

The user has since set a broader current rule: restore whitelisted **Failed**
post-Tower side jobs, retaining progress when possible and restarting otherwise.
Future production selection will use actually unstarted pre-ending history.
This old two-job fresh-only test is not that broader implementation. Sacrum's
reported currentFresh state is Inactive, not a Failed-root example. No generic
failed reset or replay is performed by the diagnostic commands below.

## Current step — S2.1 read-only failed/progress capture

**Installed 15 October at 19:17 UTC.** This is a diagnostic and optional
fresh-fixture authorization repair, **not all-failed-side-job restoration**.
No native quest, journal, reward, history or saved progress was reset. All other
mods, saves, caches and settings were preserved; compilation and rollback passed.

Cold-launch and load **the same working post-Tower save used for the S2 status
report** above. Do not replay the ending or choose the newest slot blindly.
Wait about ten seconds with menus closed, then open CET and run once:

```lua
print(Game.GetScriptableSystemsContainer():Get("PTFR.SideJobsS2.SideJobsS2"):FailedDetails())
```

This prints the summary and remaining catalogue-bound journal/fact values for
actual Failed whitelist roots. It is read-only; no new save or forced facts are
needed. Tell the agent when it is done so the CET log can be inspected. If it
reports missing/unsettled systems, close menus briefly and retry once. Missing
entries remain unknown, not assumed eligible. Three jobs have explicit
`noDetailCoverage`; even covered jobs lack complete scene/item/actor history.
`postTowerReady` is context, not proof that a restart/resume is safe.

The optional `EnableFreshFixture("DISPOSABLE_SAVE")` API repairs the old two-job
fresh test's separate authorization. **Do not run it for this Failed-job task**;
it does not restore Failed jobs and is not the current rollout policy.

S2.1 recovery comes **before** S2: run `prealpha/sidejobs_s21/deploy.ps1`
`ValidateRollback`, then `Rollback`, with `recovery/sidejobs_s21_01`. This returns
the original S2 script. Its installed source/build/tools/tests are now pinned.

## Historical S2 installation and original fresh test

Status: **installed on 15 October; live playtest pending**. Three files added,
no existing files replaced. All installed hashes and rollback validation pass;
existing mods, saves, settings and caches were preserved. The game was not
launched. See `research/sidejobs_s2/install_result_20261015.json`; the earlier
blocked-install assessment remains historical.

This batch restores **Sacrum Profanum / Losing My Religion** (`mq032_sacrum`)
and **Stadium Love** (`mq008_party`) when eligible. It does not restore the
entire 58-candidate whitelist, restart Only Pain, or replay completed jobs.
Original quest phases, conversations, rewards, failure branches and cleanup
are referenced directly. No synthetic markers or custom rewards are added.

Johnny's voice is retained using the existing JV1 policy: his scene actor may
exist internally, but its visible body is hidden. The user explicitly approved
that approach on 15 October. Sacrum's three original scenes have Johnny and no
independent scene props; Stadium's scenes do not cast Johnny. Actual Sacrum
voice/body delivery still needs the live check below.

## Short test — no ending replay

1. Cold-launch after installation. Load **AutoSave-10, level 48,
   13:32:21 on 15 October 2026**. It tracks `sts_wbr_hil_07/get_in` and has
   Tower/handoff/support completion facts. Do **not** choose AutoSave-11 at
   Viktor: that is a different ending-stage save.
2. Make a **new manual test save**; do not overwrite the source. A byte-exact
   three-file backup of AutoSave-10 is in
   `research/sidejobs_s2/fixture_auto10_20261015`.
3. Close CET/menus, leave combat/vehicle/workspot and wait about ten seconds.
   Keep the Jobs map filter enabled. Inspect both jobs if useful:

   ```lua
   print(Game.GetScriptableSystemsContainer():Get("PTFR.SideJobsS2.SideJobsS2"):Status())
   print(Game.GetScriptableSystemsContainer():Get("PTFR.SideJobsS2.SideJobsS2"):Inspect("mq032_sacrum"))
   print(Game.GetScriptableSystemsContainer():Get("PTFR.SideJobsS2.SideJobsS2"):Inspect("mq008_party"))
   ```

4. Look for the monk encounter for **Sacrum Profanum / Losing My Religion**
   in Northside, Watson. Approach on foot and check the normal conversation,
   objective and enemy encounter. Before approaching, a map marker need not
   mean an active named journal job. If admission is refused, send the three
   lines above; **do not force facts or clear completion state**.
5. During Johnny's dialogue, confirm voice/subtitles continue but no body or
   detached props appear, and the conversation advances normally.

The inspected AutoSave-10 already contains `mq008_done=1` and
`mq008_agreed_to_competition=1`. **Stadium Love must remain completed on this
branch**; absence of a new Stadium Love marker is correct. Its gameplay test
needs a different genuinely unstarted branch, not a forced reset. Sacrum's
sampled facts were absent from serialized tables, which is not proof of live
zero or eligibility; the runtime journal/fact checks decide.

## Deferred full coverage

- Sacrum: accept, rescue, native reward, epilogue, departure cleanup; optional
  lethal/nonlethal or refusal outcomes on separate untouched test branches.
- Stadium: native approach and dialogue, drinking/shooting contest, score,
  win/loss, prize collection, combat/refusal routes and departure cleanup.
- Stadium: ambient crowd coexistence and prevention/police behaviour. Native
  passive `mq008_active` may increment from 1 to 2 on re-entry; audited readers
  use zero/positive tests and native cleanup sets it back to exact zero. The
  separate ambient respawn/retrofix roots are not restarted.
- New save/reload before approach, during gameplay and after completion. No
  second owner, replayed reward, or lost completion. Include a queued-permission
  save/reload check; offline tests do not prove native loader ordering.
- Production: install before Tower, observe fresh state, cross the genuine
  native cutoff, finish the ending and verify only captured-unstarted jobs are
  restored. Missing pre-Tower history is never certified; the current explicit
  late-ending development route remains labelled uncertified.
- Regression: Only Pain, gigs, races, fixer offices, scanners, courier,
  airdrops, cyberpsychos, H10, nerfs and ending handoff stay unchanged.

`Issued=1` only confirms admission; it is not proof of a visible NPC, prompt,
reward or finished gameplay. `Finished` observes the original child's output;
the wrapper has no termination node that can cancel remaining native cleanup.

## Recovery

After rolling back S2.1 first, use `prealpha/sidejobs_s2/deploy.ps1` with recovery directory
`recovery/sidejobs_s2_01`: first `ValidateRollback`, then `Rollback`. Remove this
newest layer before R1/P1/D1/N22/N21/C1/N2/N1/FO1/PA6. File rollback does not undo
quest progress already saved; keep the untouched test source.
