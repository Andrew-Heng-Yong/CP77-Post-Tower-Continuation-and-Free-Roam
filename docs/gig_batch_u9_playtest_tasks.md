# U9 whitelisted-gig batch — playtest tasks

**Current deployment supersedes the old launch commands below:** the consolidated
PA1 package is installed. Start with [ManualSave-10 and the clean-run guide](pre_alpha_clean_run.md).
Gig dispatch is automatic after the ending, H10 arrival and profile transaction.
Old PTFR CET modules and old test saves have been recoverably archived. Keep the
per-gig acceptance checks below as the backlog, but do not run the retired U9
CET-interlock/old-baseline setup instructions in PA1.

Prepared 12 October 2026. Intended for the next available playtest session.

This is the gig component of the broader [integrated alpha](alpha_playtest_tasks.md).
The full alpha also requires side jobs, other activities, existing restorations,
apartment repurchase (H10 €$25,000; other previously owned homes at normal prices),
the accepted nerf profile and the pre-ending handoff
to H10's street. Development overrides below do not prove automatic deployment.

> **Baseline correction after the first U9 startup test:** Do not use
> ManualSave-20 for this batch. A fresh read-only audit found
> `PTFRB5_TierRequest=1` and `PTFRB5_H1_Started=1`; it carries earlier B5
> restoration state. The pre-U6/U7 requirement below was insufficient.
> A read-only search identified ManualSave-17 (level48, 21:02:06, 25.09.2026)
> with Tower complete and no sampled old gig-ownership facts recorded. It still
> has unequal historical phone counters, so U9 phone admission needs review.
> Hold StartAll until that is resolved; do not replay the ending or reset facts
> to work around it. No live readiness pass is claimed for this candidate.

## Build status

**INSTALLED — U9 development batch, gameplay verification pending.**
Installed 12 October 2026 at 20:24 Toronto time (13 October 00:24 UTC).
Offline checks passed; this is not a live gameplay pass. No playtest is needed
today. Cold-launch when you are ready to test using the baseline below.

Scope: approved gigs only. Side jobs, NCPD scanner activities, cyberpsycho
sightings, El Capitan vehicle contracts, airdrops and other world missions are
not being restored by this batch. Their tests belong to later work.

The target remains original quest graphs, calls, objectives, rewards, fixer
credit, earned tiers and cleanup. Johnny's supporting voice remains audible;
his visual projection does not. No cast-policy or whitelist expansion.

## What has already passed

- [x] U7 Jeopardy: native phone briefing/debrief, completion, fixer credit,
  departure cleanup and reported save/reload checks.
- [x] U8 startup: user loaded successfully and saw map gig icons.
- [x] U8 Life's Work: succeeded journal, fixer credit and their persistence
  across reported reload; later final cleanup `finished=1`, `creditDone=1`,
  `Heywood=2`, `fault=0`.
- [x] HP150 checkpoint-reload fix: user confirmed fixed.

These are predecessor-build results, not automatic passes for U9. Do not repeat
every old pilot before continuing development. Check representative U9 routes
and regressions below when convenient; a complete 72-gig playthrough is not a
prerequisite for further implementation. Unplayed gigs stay **untested**.

## Save to load — important

**Current development candidate:** ManualSave-17, level **48**, timestamp
**21:02:06, 25.09.2026**. Its recorded `sav.dat` SHA256 is:

`035EED1F702E49652C6F7308ADB5722133E8C6A48E4C6E465083D64C689A7804`

The [read-only search](../research/gig_restoration/u9_baseline_save_search_20261012.json)
does not prove runtime admission. Resolve the phone guard before StartAll; a
read-only `GigPhoneU9.Inspect()` can check the loaded state. Do **not** use
ManualSave-20, ManualSave-21 or the later Life's Work save as fresh U9 baselines.
They contain old restoration state. No development-save migration or ownership
fact clearing is approved. The full alpha needs a separately verified pre-ending
fixture, not this post-Tower candidate.

Preserve the original baseline. Make **new manual saves in separate slots**.
Record each new slot and timestamp below; do not guess save numbering.

| Role | Slot / timestamp | Notes |
|---|---|---|
| Development baseline candidate | ManualSave-17 / 21:02:06, 25.09.2026 | Keep untouched; phone admission unresolved |
| U9 activated | To record | Support and batch accepted, outside encounters |
| U9 completed representative | To record | Reward/counter values noted |
| U9 cleanup complete | To record | Native cleanup acknowledged |

## A. Startup and admission — first session

- [ ] Resolve the phone-admission hold described above before running StartAll.
- [ ] Confirm the U9 installation receipt below is present before starting.
- [ ] Cold-launch after installation and load the baseline specified above.
- [ ] Wait until normal gameplay is loaded. The U9 CET safety guard must be
  active; a guard-not-ready refusal is a stop/report condition, not a reason to
  force facts or invoke older entry commands.
- [ ] Run U9 StartAll **once**, using the command below after installation.
- [ ] Close CET and all menus, holster, leave combat/vehicle/workspot and allow
  the service/entry guards to settle.
- [ ] Capture support status, all gig states and tier status.
- [ ] Ensure the **Gigs** map filter is enabled. Service Points alone hides gigs.
- [ ] Check markers in each region with eligible unfinished gigs. Native tier
  locks and completed gigs mean that not all whitelist markers appear at once.
- [ ] Approach one eligible marker. A named journal entry may appear only after
  approach/briefing; an empty journal beforehand is not itself a failure.
- [ ] Completed baseline gigs remain completed. Excluded gigs are not activated.
- [ ] No side-job/world-mission restoration requests are issued by U9.

Start (this also requests the shared fixer phone support):

```lua
print(Game.GetScriptableSystemsContainer():Get("PTFR.ActivityStateR3.NativeGigsU9"):StartAll("DISPOSABLE_SAVE"))
```

Close CET/menus for about 15 seconds, then capture these read-only statuses:

```lua
print(Game.GetScriptableSystemsContainer():Get("PTFR.ActivityStateR3.GigPhoneU9"):Inspect())
print(GetMod("PTFR_GigBatchU9").Status())
print(Game.GetScriptableSystemsContainer():Get("PTFR.ActivityStateR3.NativeGigsU9"):InspectAll())
print(Game.GetScriptableSystemsContainer():Get("PTFR.ActivityStateR3.NativeGigsU9"):TierStatus())
print(Game.GetScriptableSystemsContainer():Get("PTFR.ActivityStateR3.NativeGigsU9"):DependencyStatus())
```

For one gig, replace the ID in this example with a row from the coverage table:

```lua
print(Game.GetScriptableSystemsContainer():Get("PTFR.ActivityStateR3.NativeGigsU9"):Inspect("sts_hey_rey_06"))
```

`request=1` means accepted; `parentEntered=1` means its original parent was entered,
not necessarily that native tiers/approach/briefing have fired. `mainEntered=1`
means the original main input fired. Neither proves a successful call or payout.
Entry flags remain set after completion; they are not live-running-owner queries.
Do not run U1/U4/U6/U7/U8/B5/B6/B7 or old pilot Start/Restore commands alongside U9.
The safe readiness probe tests REDscript-to-CET delivery without invoking an old
mutating entry method. Individual old-method override delivery remains a separate
engine integration check; do not probe it by restarting old gigs on a valued save.

## B. Representative end-to-end routes

Choose **one available unfinished gig per fixer**, not an already completed
one. If a suggested region has no eligible gig, record the refusal/tier state;
do not force counts or replay completion to manufacture a test.

| Fixer / region | Selected gig + ID | Briefing | Objectives | Reward / debrief | Credit | Cleanup | Reload |
|---|---|---|---|---|---|---|---|
| Regina / Watson | To choose from accepted rows | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| Wakako / Westbrook | To choose from accepted rows | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| Padre / Heywood | Jeopardy or Life's Work if still unfinished on baseline | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| Muamar / Santo Domingo | To choose from accepted rows | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| Dino / City Center | To choose from accepted rows | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| Dakota / Badlands | To choose from accepted rows | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| Mr. Hands / Pacifica | To choose from accepted rows | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| Mr. Hands / Dogtown | Choose an accepted Dogtown row | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| Rogue's gigs | Only if source-admitted/available | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |

For each chosen route:

1. Record the gig ID, journal state, relevant fixer counter and money before it.
2. Answer the normal fixer call; note incoming popup, audible dialogue and text.
3. Complete objectives normally, including pickups/downloads/escorts/delivery.
4. Confirm normal debrief and payout. A `creditDone` flag is **not** direct proof
   of a money payout or audible call.
5. Leave the encounter and allow its original cleanup conditions to complete.
   `cleanupFinished=0` immediately after success can be normal. Life's Work waits one
   in-game day after debrief plus departure; other gigs have their own rules.
6. Note counter and money, save to a **new slot**, reload and inspect again.
   No repeated payout, counter increment, respawned encounter or restarted call.
7. Mark only the observed columns above. Report anything that stalled.

## C. Cross-cutting regression checks

- [ ] Native call rejection follows the original fallback route and does not
  leave later calls blocked. Test on a separate disposable branch.
- [ ] One interrupted call can recover through native handling; no permanently
  active phone/setup flags or duplicate incoming popups.
- [ ] Save/reload while one gig is active: objectives and encounter continue,
  without duplicate actors/owners or restarted rewards.
- [ ] Death -> Load Last Checkpoint: HP remains150 and gig progression matches
  the checkpoint. No need to deliberately repeat this for every gig.
- [ ] A gig with supporting Johnny: voice/timing remain, no visible projection,
  no Relic reactivation or bodily takeover.
- [ ] Earn a native tier threshold legitimately: original delay/message/new
  eligible markers occur once; survive a new save/reload without duplicate credit.
- [ ] Ordinary fast travel, map, vendors and saving still work during/after gigs.
- [ ] Longer play session / repeated reload: no new loading crash. Preserve logs
  for any crash; a prior memory-allocation error does not identify every new cause.
- [ ] Separate native prestate/tier handoff coverage: Shark in the Water, Backs
  Against the Wall, Woman of La Mancha, Welcome to America Comrade, Troublesome
  Neighbors, Catch a Tyger's Toe, Flight of the Cheetah, Dirty Biz, Until Death
  Do Us Part, Olive Branch and Old Friends. These 11 use restored original
  prestate companions; no need to complete all in the first session. Shark may
  legitimately remain locked until its stock tier is earned.

Stock thresholds remain intact. The whitelist may leave too few available gigs
to reach a later threshold on a particular save. Do not add synthetic credit.
Some original completion watchers have no connected counter edge; do not assume
every successful gig must add a fixer count. Their absence is recorded in the
coverage table, not compensated with invented credit.

Spy in the Jungle's original cleanup has no completion output. `cleanupFinished=0`
alone is not a failure for that gig; check journal completion, native credit,
departure behavior and reload instead. U9 does not fabricate an acknowledgement.
For My Son also requires its original prestate input before the gameplay input;
include it in follow-up coverage after the basic representative routes.

Independent final-fixer reward side jobs and other follow-up side-job owners are
not restored by this gigs-only batch. Native gig-local conclusions remain intact.

### Native gang retaliation

Retaliation caused by selected gigs is part of their stock consequences, not a
separate world-activity rollout. Test one qualifying route when convenient:

- [ ] Record `DependencyStatus()` before and after a qualifying gig.
- [ ] If the original outcome triggers retaliation, verify the native message,
  chase/ambush and normal cancellation/cleanup. Do not force an outcome or flag.
- [ ] Save/reload does not duplicate the chase or consume unrelated old flags.

ManualSave-20's read-only audit contains pending Maelstrom and Tyger Claws
retaliation. U9 does **not** clear those historical flags. Gigs that can write
the same gang's retaliation are refused before a request is queued. They do not
automatically retry, and U9 does not clear the old flags later. On this baseline,
The Heisenberg Principle, Catch a Tyger's Toe and Bloodsport may therefore defer.
Hippocratic Oath, Rite of Passage, Monster Hunt and Tyger and Vulture share the
guard but are already recorded finished; they remain excluded from replay.
Other gangs are admitted independently. Treat this as a documented baseline
limitation, not evidence that all 72 gigs are simultaneously playable.
Testing a refused route needs a suitable baseline without that pending gang
state, or separately implemented historical-state handling. Do not force flags
or repeatedly run Start to bypass it.

Monster Hunt and The Heisenberg Principle have a stock generic Tyger retaliation
signal without a matching local selector in the inspected service. U9 preserves
that wiring; it does not invent an additional ambush route.

## D. Production ending-transition tests — deferred

This U9 development batch does not fabricate pre-Tower history. Production must
restore only genuinely **unstarted-before-Tower** whitelisted gigs. Record these
as later tasks only when production capture/automatic admission is integrated:

- [ ] Capture fresh, started, completed and genuinely failed gig examples before
  Tower; preserve their distinct states through the ending.
- [ ] Natural Tower ending, watched and skipped credits, retained-session return.
- [ ] Only the captured unstarted whitelist subset restored automatically.
- [ ] Missing pre-Tower history remains unknown; development override is explicit.

Do not replay the ending solely for U9 until its production integration is ready.

## When to stop / what to send

Stop the affected route for a crash, missing required actor/interaction, repeated
payout, wrong gig activation, blocked call service or unintended story change.
Send gig ID, save slot/time, exact command/status, what you expected and observed,
and whether a reload occurred. Do not fix it by forcing facts or repeating Start.

You can pause after recording results and making a separate new save. There is
no requirement to finish every gig in one session or wait in-game for hours.

## Installation and coverage receipt

Receipt: `research/gig_restoration/gig_batch_u9/install_receipt.json`.
Combined manifest SHA256:
`60FDB58AD3778DF50E3E18714C02543CB5F150887DF787E36E5862ED3F558778`.

- 12 additions, zero replacements: three archive/XL pairs (native gigs, phone
  support, special dependencies), four native/phone REDscripts, one default-false
  readiness helper and one CET entry guard.
- 72 original gig entries; 66 native connected credit branches; 25 earned-tier
  branches; 94 map branches; 11 original prestate companions; eight fixer phones.
- Source/graph checks, packed-resource readbacks, cross-package collision checks,
  CLI and full game script compilation including EquipmentEx, and all new U9
  compiled bodies passed. The code decompiler has one documented limitation in
  the unchanged older `ActivityDefinition.FactNames` body; bytecode readback passed.
- 174 LuaJIT interlock cases and 13 negative deployment/recovery cases passed.
- 2,575 existing files, including 152 save-folder files, were hash-verified
  unchanged during installation. No direct save or game-cache writes.
- Existing HP150, Body3, closed Relic and Johnny voice/projection rules unchanged.

All 72 IDs have implementation coverage below, **not** a promise of admission on
every save. Completed/terminal gigs stay preserved; unsupported progressed state,
legacy owners, historical pending retaliation and native tiers can refuse or
defer a candidate. Production pre-Tower integration remains a later task.

Recovery is only through the pinned `tools/deploy_gig_batch_u9.ps1`
`ValidateRollback` / `Rollback` modes with the game closed, then loading the
original pre-U9 baseline. It moves the 12 additions recoverably; it cannot undo
quest progress or rewards in a later save. Do not rerun installed builders/tests.

## E. Per-gig coverage / result log

All rows below are U9 build coverage, not live passes. Mark a row only after
observing its outcome; leave completed baseline or tier-locked gigs as not tested.
`No branch` means no connected credit branch in the inspected native completion
loop; no replacement credit is added. It does not mean no money payout.

| Gig | ID | Native credit branch | Played / result / save |
|---|---|---|---|
| Dancing on a Minefield | `sts_bls_ina_07` | Yes | [ ] |
| A Lack of Empathy | `sts_cct_dtn_03` | Yes | [ ] |
| Sparring Partner | `sts_bls_ina_11` | Yes | [ ] |
| An Inconvenient Killer | `sts_cct_dtn_02` | Yes | [ ] |
| Guinea Pigs | `sts_cct_dtn_04` | Yes | [ ] |
| Hot Merchandise | `sts_hey_spr_06` | No branch | [ ] |
| Life's Work | `sts_hey_gle_06` | Yes | [ ] |
| On a Tight Leash | `sts_hey_spr_01` | Yes | [ ] |
| Prototype in the Scraper | `sts_ep1_04` | Yes | [ ] |
| The Man Who Killed Jason Foreman | `sts_ep1_03` | Yes | [ ] |
| Hacking the Hacker | `sts_std_arr_11` | Yes | [ ] |
| Severance Package | `sts_std_arr_10` | Yes | [ ] |
| For My Son | `sts_pac_wwd_05` | Yes | [ ] |
| Dirty Biz | `sts_wat_nid_04` | Yes | [ ] |
| Monster Hunt | `sts_wat_kab_07` | Yes | [ ] |
| Rite of Passage | `sts_wat_nid_05` | Yes | [ ] |
| Small Man, Big Evil | `sts_wat_kab_101` | Yes | [ ] |
| Shark in the Water | `sts_wat_kab_06` | Yes | [ ] |
| The Heisenberg Principle | `sts_wat_lch_06` | Yes | [ ] |
| Tyger and Vulture | `sts_wbr_hil_07` | Yes | [ ] |
| Until Death Do Us Part | `sts_wbr_hil_01` | Yes | [ ] |
| A Shrine Defiled | `sts_wbr_jpn_03` | Yes | [ ] |
| Catch a Tyger's Toe | `sts_wat_lch_01` | Yes | [ ] |
| Troublesome Neighbors | `sts_wat_kab_107` | Yes | [ ] |
| Eye for an Eye | `sts_hey_gle_01` | Yes | [ ] |
| Old Friends | `sts_hey_rey_08` | Yes | [ ] |
| The Union Strikes Back | `sts_std_rcr_01` | No branch | [ ] |
| Talent Academy | `sts_ep1_13` | Yes | [ ] |
| Serial Suicide | `sts_cct_cpz_01` | Yes | [ ] |
| Big Pete's Got Big Problems | `sts_bls_ina_02` | Yes | [ ] |
| Flying Drugs | `sts_bls_ina_03` | Yes | [ ] |
| No Fixers | `sts_bls_ina_06` | Yes | [ ] |
| MIA | `sts_bls_ina_09` | Yes | [ ] |
| Goodbye, Night City | `sts_bls_ina_05` | Yes | [ ] |
| Trevor's Last Ride | `sts_bls_ina_08` | Yes | [ ] |
| Radar Love | `sts_bls_ina_04` | Yes | [ ] |
| The Frolics of Councilwoman Cole | `sts_cct_dtn_05` | Yes | [ ] |
| Fifth Column | `sts_hey_gle_04` | Yes | [ ] |
| Jeopardy | `sts_hey_rey_06` | Yes | [ ] |
| The Lord Giveth and Taketh Away | `sts_hey_spr_03` | Yes | [ ] |
| Two Wrongs Makes Us Right | `sts_pac_cvi_02` | No branch | [ ] |
| Dogtown Saints | `sts_ep1_01` | Yes | [ ] |
| Treating Symptoms | `sts_ep1_12` | Yes | [ ] |
| Waiting for Dodger | `sts_ep1_10` | Yes | [ ] |
| Spy in the Jungle | `sts_ep1_08` | Yes | [ ] |
| Roads to Redemption | `sts_ep1_07` | Yes | [ ] |
| Family Matters | `sts_std_rcr_05` | Yes | [ ] |
| Going-away Party | `sts_std_rcr_03` | Yes | [ ] |
| Nasty Hangover | `sts_std_arr_06` | No branch | [ ] |
| Serious Side Effects | `sts_std_arr_01` | Yes | [ ] |
| Many Ways to Skin a Cat | `sts_wat_nid_02` | Yes | [ ] |
| Hippocratic Oath | `sts_wat_kab_02` | Yes | [ ] |
| Concrete Cage Trap | `sts_wat_kab_01` | No branch | [ ] |
| Freedom of the Press | `sts_wat_nid_12` | Yes | [ ] |
| We Have Your Wife | `sts_wbr_jpn_02` | Yes | [ ] |
| Getting Warmer... | `sts_hey_rey_09` | Yes | [ ] |
| Wakako's Favorite | `sts_wbr_jpn_05` | Yes | [ ] |
| Welcome to America, Comrade | `sts_wat_kab_102` | Yes | [ ] |
| Woman of La Mancha | `sts_wat_kab_08` | Yes | [ ] |
| Backs Against the Wall | `sts_wat_kab_03` | Yes | [ ] |
| Last Login | `sts_wat_kab_05` | Yes | [ ] |
| Lousy Kleppers | `sts_wat_nid_06` | Yes | [ ] |
| Bloodsport | `sts_wat_lch_03` | Yes | [ ] |
| Desperate Measures | `sts_std_arr_12` | No branch | [ ] |
| Breaking News | `sts_std_arr_05` | Yes | [ ] |
| Heaviest of Hearts | `sts_ep1_06` | Yes | [ ] |
| Occupational Hazard | `sts_wat_nid_01` | Yes | [ ] |
| Flight of the Cheetah | `sts_wat_nid_03` | Yes | [ ] |
| Cuckoo's Nest | `sts_std_rcr_02` | Yes | [ ] |
| Olive Branch | `sts_wbr_jpn_01` | Yes | [ ] |
| Fixer, Merc, Soldier, Spy | `sts_wat_kab_04` | Yes | [ ] |
| Playing for Keeps | `sts_wat_lch_05` | Yes | [ ] |

