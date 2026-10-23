# S22 — progress-preserving side-job restoration

Update: the user reports Epistrophy "seems to be working" after S22.1. Record an
initial functional pass, not all remaining cars/final reward/reload. Evidence:
`research/sidejobs_s221/live_result_20261015.json`. The requested full-whitelist
expansion is being prepared separately; see [S23](sidejobs_s23_rollout.md).

Status: **S22.1 Epistrophy phone-gate repair installed on 15 October at 23:43 UTC**
(19:43 Toronto), on top of hardened S22. One backed-up archive replacement;
scripts, XL injection IDs and graph connections are unchanged. Hash and rollback
validation passed; all 215 save files, settings and caches were preserved.
Evidence: `research/sidejobs_s221/assessment_01.json` and
`recovery/sidejobs_s221_01/install_receipt.json`. The game was not launched.

User confirmed journal entries for The Gig, Beat on the Brat and Moving Heat;
this is not their full gameplay/completion pass. Epistrophy was blocked despite
matching progress because our additional startup check required equal historical
call counts. Captured main counts were 7/2 and sad counts 0/1; all 57 busy/reset
flags were zero. Stock's sad incoming call writes `active_count`, not
`start_count`. S22.1 removes only history equality from the two preflight checks
in each Delamain support/owner graph. Busy flags, progress protection and native
phone cleanup remain unchanged; no counters are rewritten. Initial functionality
is user-reported; complete end-to-end coverage remains pending.

## Current rules

Restore R4-whitelisted side jobs whose post-Tower journal root is **Failed or
Inactive**. Preserve halfway progress, completed objectives, choices and earned
rewards. Active and Succeeded jobs are protected. Unsupported progress states are
left unchanged, not silently restarted. Johnny keeps his voice with his visible
body hidden under the existing approved policy.

The future selection rule is whitelisted jobs observed **Inactive before Tower**;
the present post-Tower route does not fabricate that history or certify it.
Eligibility and an implemented native owner are separate: this is not all 58 jobs.

## What this batch can resume

| Job | Supported saved stage | What must remain intact |
| --- | --- | --- |
| Beat on the Brat | Introduction completed, no bout started/won | Introduction choices; native four-bout discovery and later authored gates |
| Epistrophy | Briefing completed; sad, mean and suicidal cars recovered, counter 3 | All three completed car jobs; remaining four cars and final scanner-return reward run natively |
| Moving Heat | Invitation accepted; reach the first door | Accepted SMS and started/active state; no invitation resend |
| The Gig | Wakako reward already earned; tattoo objective outstanding | Both completed objectives; no cash/XP/message replay |

The existing S2 fresh Inactive routes for **Sacrum Profanum / Losing My Religion**
and **Stadium Love** now receive automatic current-policy admission, still subject
to their native freshness and one-shot checks. Completed Stadium Love is not replayed.

**No Easy Way Out is not resumed by this batch.** Its Failed root was captured,
but its current stage was absent from the old detail catalogue. Native stage,
choice, item and reward state must be established before selecting its route.
Other unfinished or differently progressed whitelist jobs are not all supported.

## Short test

1. Cold-launch the game after installation. Load **the same working post-Tower
   save used for the latest screenshots and Epistrophy phone-counter check**
   (the branch where The Gig, Beat on the Brat and Moving Heat appeared).
   Do not replay Tower or load an ending-scene checkpoint. Keep the original save.
2. Stand on foot outside the relevant encounter, out of combat, weapon holstered.
   Close CET and menus for about ten seconds.
3. Check the journal. Epistrophy should retain **3/7** cars, Moving Heat should
   point to the first door, and The Gig must not pay Wakako's reward again.
   Boxing should resume discovery, not replay the introduction.
   S22.1 should activate Epistrophy even with the recorded main 7/2 and sad 0/1
   historical counts. Do not manually balance them. Visit one of the four
   unfinished cars after journal activation; check actual car/call/objective
   interaction, then save to a new slot and reload. The three completed cars
   must remain completed, with no repeated reward.
4. If any job does not resume, run this read-only status capture once:

```lua
local s=Game.GetScriptableSystemsContainer():Get("PTFR.SideJobsS22.SideJobsS22"); print(s:Status()); for _,id in ipairs({"mq025_psycho_brawl","sq025_delamain","q304_car_retrieval","sq_q001_wakako"}) do print(s:Inspect(id)) end
```

For the monk's existing owner:

```lua
print(Game.GetScriptableSystemsContainer():Get("PTFR.SideJobsS2.SideJobsS2"):Inspect("mq032_sacrum"))
```

If Epistrophy remains absent, this single-line read-only command also captures
its support and entry state. The printed version remains S22 because no script
replacement was necessary for S22.1:

```lua
print(Game.GetScriptableSystemsContainer():Get("PTFR.SideJobsS22.SideJobsS22"):Inspect("sq025_delamain")); local q=Game.GetQuestsSystem(); for _,n in ipairs({"SupportReady","SupportIssued","Entered"}) do local f="PTFRS22_SQ025_"..n; print(f.."="..q:GetFactStr(f)); end
```

`currentMatch=false` after `Issued=1` can be expected: the native quest has moved
beyond its admission stage. Do not reset Issued/Permit/native facts or rerun a
fixture. A mismatch before issue reports the first protected state instead of
resetting progress. `Finished` follows the adapter's native output, not every
individual child objective or live-render proof.

## Deferred full playtests

- Each resumed job's actual interaction, progression, native failure/retry and
  one-time payout. Epistrophy must skip its three completed cars and finish only
  after the other four; final scanner reward must occur once.
- Epistrophy's post-completion failure/show-hide watchers must be stopped;
  normal failure handling must still work before successful completion.
- Boxing: bets/results, later Ozob/finale gates, no reward replay and no Johnny
  body or scene props. Existing nerfs remain enabled.
- The Gig: native reward-vendor availability and tattoo ownership condition;
  no item is granted by the adapter itself.
- New manual save and cold reload mid-progress and after completion; no owner
  restart, old call resend, duplicate payout or progress regression.
- Completed/out-of-whitelist controls, other fixer/courier/NCPD calls, and the
  full pre-ending-to-post-ending integration run later.

## Recovery

**First undo S22.1**, using `prealpha/sidejobs_s221/deploy.ps1` with
`recovery/sidejobs_s221_01`: ValidateRollback, then Rollback. This restores the
previous S22 archive without changing saves. Only then use older recovery below.

The first S22 installation was recoverably rolled back before any game launch
for additional Epistrophy lifecycle hardening. Its files and receipts remain at
`recovery/sidejobs_s22_01`; **do not run that completed rollback again**.
The hardened installation uses the successor installer
`prealpha/sidejobs_s22b/deploy.ps1` and `recovery/sidejobs_s22_02`.
Use ValidateRollback before Rollback. File rollback does not undo gameplay saved
after a test. Then the prior recovery order starts S21, S2, R1, P1, D1, N22, N21,
C1, N2, N1, FO1, PA6 and older layers.
