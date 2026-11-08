# QR9 manual test cards
Prepared only. Codex has not deployed, launched or controlled the game. Wait for explicit deployment authorization. Start with S00 only.
## Before playing
- Wait for explicit deployment authorization, successful installer verification and the reviewed diagnostic-addon installation. The preparation files authorize neither deployment nor game launch by Codex.
- Keep the confirmed master and its separately preserved backup unchanged. Use the working branch identified by the reviewed save procedure; never choose a copied/renamed folder by assumption.
- All restored controllers may initialize. Avoiding quest locations alone does not certify an arbitrary save. Stop if an unexpected old quest, duplicate reward, repeated call or missing dependency appears.

Confirmed master: **ManualSave-23** (29 October,7:23 PM), user-declared genuine post-Tower lineage. It stays untouched. Future authorized Install -BackupMaster preserves the exact original3files in workspace recovery. The user then loads ManualSave-23 solely to use native Save Game/New Save, identifies the actual new slot and keeps bootstrap separate. No backup or working copy has yet been created; never assume a renamed raw folder is recognized.

Reviewed save procedure: C:\Users\Ayong\Documents\cp77 modding\tower ws\prealpha\quest_restoration_qr9\USER_PROCEDURE.md

Deployment/rollback procedure: C:\Users\Ayong\Documents\cp77 modding\tower ws\prealpha\quest_restoration_qr9\USER_PROCEDURE.md

## Capture and return
The commands below are for the user to enter manually in CET, after approved installation. The default capture auto-stops after300 seconds; explicit stop is still safe.

Status: `GetMod("PTFR_QR9_Diagnostics").status()`. Variant marker, if useful: `GetMod("PTFR_QR9_Diagnostics").mark("S02_ordinary_future")`.

Logs: `C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_QR9_Diagnostics`. After stopping and normal quit, use the exact collection command on the relevant card. This first example is **S00 only**:

```powershell
& 'C:\Users\Ayong\.local\bin\python3.14.exe' -X utf8 -B 'C:\Users\Ayong\Documents\cp77 modding\tower ws\prealpha\quest_restoration_qr9\collect_observation.py' --run-id S00_01 --card S00
```

Each listed collection command creates its first fresh Sxx_01 bundle. For a repeated card, request/use a new RunId such as Sxx_02 while keeping its --card profile unchanged; never overwrite a previous bundle.

Return the diagnostic/log bundle and one short line: card/variant, working-slot label, what happened and approximately when. Screenshots are needed only for a visual problem such as a missing/duplicate actor or blocked door; logs are preferred for calls and state changes.

No manual fact/node list is required. Screenshots only for a visual problem.
- The user operates the game and CET. Start one bounded profile, perform only that card, then stop. No fact/journal/contact/item/clock setters, forced starts, teleports, ACK injection or world-loading manipulation.
- For long native timers, capture the entry/claim, stop, play normally, then start a new bounded capture near the callback or after normal reload. Do not leave sampling running for several in-game days.
- Stop the current capture before any deliberate reload. Arm a fresh capture from the main menu with no attached player, or start a new segment after the normal load finishes. The logger does not certify continuity across saves or identify the save automatically.
- A selected fact/journal transition is a progress observation. It is not automatically an exact graph-node trace, original-owner retirement proof or acknowledgement of successful plugin startup.
- If an event happens outside capture, report the visible observation. Missing diagnostic evidence is INCONCLUSIVE, not a failed call and not retroactive capture.

Stop rule: Stop capture and stop advancing that branch if there is an unexpected quest restart, duplicated reward/actor/call, stuck cleanup or error. Preserve that working branch and logs. Do not fix its state during the test.

## Cards

### S00 — First: short startup and registration smoke

**Fixture:** Use the user-confirmed master lineage through the reviewed working-save procedure; no fresh gig is required for this limited smoke.

**Before:** Exact QR8:02 and diagnostics verified installed after explicit authorization. Reviewed working-save identity and master protection are established; any initial native-slot bootstrap is recorded separately, not called a disposable startup test.

**Start:** `GetMod("PTFR_QR9_Diagnostics").start("S00")`

1. At the main menu, start capture; then load only the reviewed working branch through the normal Load Game menu.
2. For 1–2 minutes, move normally and open/close the map. Do not accept a gig, buy an item, visit a restored quest location or overwrite the master.
3. Stop capture. Quit normally before collecting the log bundle; record any automatic save/new-slot bootstrap separately.

**Visible:** The save loads, ordinary movement/map work, and no ending replay, unexpected old quest or duplicate call appears. Cured/post-Tower presentation remains. Do not repeat the already successful generic Ana fixture.

**Logs:** A valid capture session linked to the separate verified installation identity, plus matching current ArchiveXL/RED4ext/redscript log window. Declared addon build fields are not runtime hash measurements. ArchiveXL parent patch/merge/refusal records where emitted. A plugin receipt is startup-attempt bookkeeping, not proof the private phase activated; early startup and numeric19913 stay unobserved unless independently measured.

**Stop:** `GetMod("PTFR_QR9_Diagnostics").stop()`. Stop after the short smoke, or immediately on an unexpected replay/error. Do not continue to a full playthrough yet.

**Collect after quit:**
```powershell
& 'C:\Users\Ayong\.local\bin\python3.14.exe' -X utf8 -B 'C:\Users\Ayong\Documents\cp77 modding\tower ws\prealpha\quest_restoration_qr9\collect_observation.py' --run-id S00_01 --card S00
```

**Return:** Bundle plus: loaded/not loaded, movement/map okay or not, unexpected quest/call/error. Screenshot only a visual anomaly.

**Branch:** This is the first small test. Registration-attempt and actual-owner-activation results are recorded separately; a visible smoke PASS cannot certify private graph activation.

### S01 — Alternate Hands calls: Two Wrongs Makes Us Right

**Fixture:** NOT_TESTABLE as a fresh-entry test on ManualSave-23/AutoSave-19: the gig is already completed. Skip unless another genuine supported post-Tower fixture exists; never replay it by reset.

**Before:** Another genuine fresh, not-yet-admitted CVI02 history with no old custom call/request or conflicting owner; read-only precheck must support it. S00 has passed within its limited smoke scope.

**Start:** `GetMod("PTFR_QR9_Diagnostics").start("S01")`

1. On that independent working fixture, start capture before approaching/accepting the gig normally; answer the actual Hands prebrief.
2. Follow the normal van route and listen to the resulting debrief. Stop after the call/cleanup settles; mark a missing or stalled call rather than forcing the door/objective.
3. Native failure or muted/no-scene alternatives use separate untouched fixtures only if naturally available.

**Visible:** Expected Hands prebrief/debrief occur on the appropriate native route; the normal objective advances and the van outcome/reward is preserved. No repeated call, stuck phone mode or forced door/objective is needed.

**Logs:** Selected real request/ACK/clear and private-flight transitions, with profile availability/errors recorded. Visible/audio call plus progress evidence is separate from exact unobserved engine-node ownership. A missing toast alone is not a defect.

**Stop:** `GetMod("PTFR_QR9_Diagnostics").stop()`. Stop after debrief/cleanup or on a stalled request. Do not clear a request, reset completion or start another conflicting call.

**Collect after quit:**
```powershell
& 'C:\Users\Ayong\.local\bin\python3.14.exe' -X utf8 -B 'C:\Users\Ayong\Documents\cp77 modding\tower ws\prealpha\quest_restoration_qr9\collect_observation.py' --run-id S01_01 --card S01
```

**Return:** Bundle plus whether prebrief, native objective and debrief occurred, and the chosen native outcome.

**Branch:** Success/failure/muted alternatives are separate branches. The current master is not a fresh fixture for this card.

### S02 — Ronald: one genuine future gig and its native news

**Fixture:** First candidates on the confirmed master are The Man Who Killed Jason Foreman or Treating Symptoms, only if read-only precheck and genuine history support admission. Saints/Spy are already completed and must not be replayed.

**Before:** Existing genuine Ronald subscription and Active contact; this card does not create a first subscription. Ordinary variant: one selected gig genuinely not yet entered, no old message/timer, and an idle supported queue. Lack of finished metadata is insufficient. Late-future variant: genuine positive QR7 Armed, native done1/sent0 and a real helper still before its first200–203 gate (possibly awaiting220). Issued1 is allowed without root reentry. If that stage cannot be observed, the variant is NOT_TESTABLE/INCONCLUSIVE, not manufactured.

**Start:** `GetMod("PTFR_QR9_Diagnostics").start("S02")`

1. Ordinary: start capture, enter one eligible selected gig normally, and complete its native outcome. Stop after the initial claim/queue transition.
2. Let the native two-game-day timer pass through normal play. Start another bounded capture near the expected message/callback; inspect Ronald's conversation even if there is no toast.
3. Late-future: do not re-enter/reaccept/rearm anything. Only observe the existing genuine owner proceed from its first gate through the unchanged native timer.
4. Timer/reload variant: use a separate working branch after this same new supported timer has started; save/load only through normal permitted menus, then resume normal play.

**Visible:** The appropriate native Ronald message eventually appears; outcome and reward remain original, without repeated news or stuck phone/queue. Spy's greeting has native notification0; no toast alone is not failure. Ordinary delivery does not count as testing the late-future repair.

**Logs:** Real positive Armed then ParentEntered/native completion and native sent-before-delay, followed by available message/queue observations. Record exact variant and capture segments. Sent1 is not delivery. Pre-gate220, actual phase execution and saved predicate refresh remain unobserved unless a separately approved observer can establish them.

**Stop:** `GetMod("PTFR_QR9_Diagnostics").stop()`. Stop each bounded capture after its event window. Stop advancing on duplicated news, old-clock adoption or stuck cleanup; never reset sent/done/pause or change the clock with commands.

**Collect after quit:**
```powershell
& 'C:\Users\Ayong\.local\bin\python3.14.exe' -X utf8 -B 'C:\Users\Ayong\Documents\cp77 modding\tower ws\prealpha\quest_restoration_qr9\collect_observation.py' --run-id S02_01 --card S02
```

**Return:** Bundles for entry/claim and callback/reload, gig title, outcome, variant and approximate in-game elapsed time. No manual fact list is required.

**Branch:** Ordinary, late-future and reload are alternatives/stages with different prerequisites. First enrollment, old sent1 clocks and already-processed branches remain held.

### S03 — Nitro: existing vehicle eligibility or already-issued preservation

**Fixture:** Nitro is absent from the known finished list; this does not prove its eligibility or original-owner state.

**Before:** Prospective: genuine not-yet-Issued history with an already-earned native allowed Kusanagi variant and at least three native vehicle purchases. Use bounded observations where the actual API supports them; otherwise eligibility stays unconfirmed. Alternative: a genuine existing already-Issued predecessor owner at the original selector. Do not impose fresh prerequisites on this branch. Do not buy/spawn vehicles or change purchase/quest counters to manufacture a test.

**Start:** `GetMod("PTFR_QR9_Diagnostics").start("S03")`

1. Prospective: start capture, approach/wait for normal Nitro activation, then observe the normal next objective. A genuinely available ineligible fixture is an independent negative branch.
2. Already-issued: start capture before normal load/progression on that separate branch; observe the retained selector, without restarting admission.
3. Stop after the admission/deferral or retained-progress result is clear.

**Visible:** An eligible future owner starts normally; a genuinely ineligible owner remains unavailable. An existing issued owner keeps its progress without new setup/rewards or forced migration.

**Logs:** Bounded native vehicle/purchase and Issued/progress observations; missing API or uncertain historical eligibility remains explicit. A car visible in the garage alone does not prove the native earned acquisition/purchase contract.

**Stop:** `GetMod("PTFR_QR9_Diagnostics").stop()`. Stop after the short eligibility/progress window. Do not change eligibility or retry by resetting the owner.

**Collect after quit:**
```powershell
& 'C:\Users\Ayong\.local\bin\python3.14.exe' -X utf8 -B 'C:\Users\Ayong\Documents\cp77 modding\tower ws\prealpha\quest_restoration_qr9\collect_observation.py' --run-id S03_01 --card S03
```

**Return:** Bundle plus prospective/negative/already-issued variant and the visible activation or preserved objective.

**Branch:** Positive, negative and already-issued histories use independent genuine branches. Do not call normal deferral a defect before precheck.

### S04 — Machine Gun: supported future return and Regina follow-up

**Fixture:** Conditional on a genuine monitored stage before future1101. An already-returned old owner or an unknown11/51/95 admission seam is not a supported fixture.

**Before:** Exact genuine supported pre1101 stage, earned Regina/quest history and no old done/reacquired state; precheck/observation must establish the stage without setters. No general fresh full-chain admission or opaque loot placement certification is implied.

**Start:** `GetMod("PTFR_QR9_Diagnostics").start("S04")`

1. Start capture before the normal supported return/handoff; follow the native choices and stop after the new continuation enrolls.
2. Let the original five-game-day/context/variant conditions run through normal play; capture the actual Regina follow-up and one-time reacquisition window.
3. For persistence, use a separate branch during that same new pending delay; save/load only when native menus permit it.

**Visible:** The appropriate native delayed follow-up and one-time reacquisition occur, without an invented world container or duplicate item/reward. Normal earned outcomes remain. Unsupported fresh admission is not forced.

**Logs:** Supported future enrollment, done/reacquired and selected message transitions; before/after item/reward observations where available. Exact original helper lease/opaque placement may remain unobserved; a completion journal alone does not prove them.

**Stop:** `GetMod("PTFR_QR9_Diagnostics").stop()`. Stop on repeated rewards, missing cleanup or a wrong-stage fixture. Do not reset done/reacquired or grant/restore Skippy to create eligibility.

**Collect after quit:**
```powershell
& 'C:\Users\Ayong\.local\bin\python3.14.exe' -X utf8 -B 'C:\Users\Ayong\Documents\cp77 modding\tower ws\prealpha\quest_restoration_qr9\collect_observation.py' --run-id S04_01 --card S04
```

**Return:** Segmented bundles, original stage/choice, whether Regina follow-up occurred, and item/reward change. No multi-day continuous capture.

**Branch:** Keep this long pending timer separate from other queue tests. If no genuine supported future1101 history exists, mark NOT_TESTABLE.

### S05 — Bullets: helper retirement and shared vendor

**Fixture:** Needs a genuine supported pending Melissa/helper handoff. A killed fact or completed journal alone is not retirement evidence.

**Before:** Known native actor/vendor history and an actual pending supported handoff, without a conflicting old owner. Independent working branch; no actor reset/despawn or vendor entitlement changes.

**Start:** `GetMod("PTFR_QR9_Diagnostics").start("S05")`

1. Start capture before advancing the normal handoff; complete only the supported native interaction.
2. Wait for cleanup, then inspect the ordinary vendor/actor interaction and leave/return normally.
3. Optional reload uses a separate branch only at a naturally saveable pending-cleanup stage.

**Visible:** One intended actor/vendor remains usable, with no overlap, duplicate interaction, repeated reward or premature disappearance.

**Logs:** Available native retirement/lease-state progress signals and errors, correlated with the interaction window. If actual retirement acknowledgement/lease release is not exposed, internal ownership remains INCONCLUSIVE even when the shop appears normal.

**Stop:** `GetMod("PTFR_QR9_Diagnostics").stop()`. Stop on a stuck retirement/cleanup or duplicate actor. Do not force-disable/despawn/reactivate anything or set a retirement fact.

**Collect after quit:**
```powershell
& 'C:\Users\Ayong\.local\bin\python3.14.exe' -X utf8 -B 'C:\Users\Ayong\Documents\cp77 modding\tower ws\prealpha\quest_restoration_qr9\collect_observation.py' --run-id S05_01 --card S05
```

**Return:** Bundle plus handoff stage, whether the vendor worked after cleanup/return, and only a screenshot if actor duplication/placement is the problem.

**Branch:** Do not mix a pending shared vendor cleanup with an unrelated actor/phone interruption test.

### S06 — Brendan: containment and existing descendant preservation

**Fixture:** Unearned all-Inactive Dumpster history and genuinely progressed descendant are different fixtures. No general sequel adapter is approved.

**Before:** One known unearned history for containment, or a separate genuine earned/progressed Spray Paint/Coin Operated Boy descendant. Never fabricate earned Dumpster history, push the excluded fresh chain through a check, or reset existing progression.

**Start:** `GetMod("PTFR_QR9_Diagnostics").start("S06")`

1. Containment: start capture and visit/observe the ordinary location briefly without forcing a quest interaction.
2. Progressed alternative: use its separate working branch; observe the existing native objective/progress and normal save/reload only where permitted.
3. Stop after observation; do not request a fresh full-chain activation.

**Visible:** Excluded unearned fresh Dumpster activation stays contained. Existing earned descendant/progress and rewards remain intact. Nonactivation of an unsupported sequel is not a restoration failure.

**Logs:** Selected journal/receipt/progress observations identify which fixture was actually tested; unknown owner history remains explicit.

**Stop:** `GetMod("PTFR_QR9_Diagnostics").stop()`. Stop on unexpected fresh setup, reset progress or duplicate reward. Do not repair the negative fixture with facts.

**Collect after quit:**
```powershell
& 'C:\Users\Ayong\.local\bin\python3.14.exe' -X utf8 -B 'C:\Users\Ayong\Documents\cp77 modding\tower ws\prealpha\quest_restoration_qr9\collect_observation.py' --run-id S06_01 --card S06
```

**Return:** Bundle plus unearned-containment or progressed-preservation variant and the visible journal/objective state.

**Branch:** This is safety containment/preservation, never evidence that the full MQ037 continuation was restored.

### S07 — Old/completed histories: no replay or invented consent

**Fixture:** The confirmed master supplies completed CVI02/Saints/Spy history. Other old entered/no-Armed, pending-clock or missing-contact histories require their own genuine fixtures.

**Before:** Known completed history or another genuine unsupported entered/pending/missing-contact state. Record which one; do not infer an old clock from sent1 alone. Use S00's reviewed working-save procedure and preserve the original history. First Ronald enrollment remains held.

**Start:** `GetMod("PTFR_QR9_Diagnostics").start("S07")`

1. Start capture and load/idle normally on the selected separate history; observe the existing completed/objective/message state without accepting/resetting the old job.
2. For a specific old pending/reload subcase, use only its genuine independent fixture. Do not create a contact or resume a clock through commands.
3. Stop after the bounded idle observation. This does not replace the positive fresh-entry tests.

**Visible:** Completed jobs remain completed, without fresh setup/reward/call replay; unsupported histories defer rather than receive invented consent. Hidden first-subscription choices and omitted native bar support remain an explicit held extension, not repaired by the QR8 late-future guard.

**Logs:** Before/after selected native history, requests and receipts, with actual observed owner limits recorded. Completed-history containment is separate from old timer ownership; lack of a toast alone does not prove a malfunction.

**Stop:** `GetMod("PTFR_QR9_Diagnostics").stop()`. Stop if an old job restarts, a reward repeats or a historical call is unexpectedly adopted. Preserve logs and that branch; no setter workaround.

**Collect after quit:**
```powershell
& 'C:\Users\Ayong\.local\bin\python3.14.exe' -X utf8 -B 'C:\Users\Ayong\Documents\cp77 modding\tower ws\prealpha\quest_restoration_qr9\collect_observation.py' --run-id S07_01 --card S07
```

**Return:** Bundle plus the exact completed/old-entered/pending/missing-contact variant and any unexpected change.

**Branch:** Current completed-history containment can share the untouched working branch after S00 if no quest actions occurred; the other history variants stay isolated.

### S08 — Separate branches: interrupt, reload and exactly-once completion

**Fixture:** Only after a clean supported route from S01/S02/S04/S05 has been observed; choose one naturally reachable interruption/save stage.

**Before:** A separate working branch for each native interruption, reload or completion-revisit alternative. The game permits normal saving at the chosen stage; if it does not, skip that subcase rather than force a save.

**Start:** `GetMod("PTFR_QR9_Diagnostics").start("S08")`

1. Start capture before a genuine native reject/interrupt choice and use that choice normally. Observe the original return/cancel/cleanup behavior.
2. On another branch, save/load normally at an available request, callback or cleanup stage, then resume through ordinary actions.
3. On a completion branch, record one reward, reload its completed state and revisit normally; never restart the completed job.

**Visible:** Native interruption/return behavior works without a stuck phone, missing required actor or overlapping controller. Completion, objectives and rewards persist once; inventory/currency changes are observed rather than assumed from a graph latch.

**Logs:** Capture segments around actual interruption/load/completion, selected request/receipt changes and native errors. Exact phase/lease ownership remains INCONCLUSIVE unless the available diagnostic actually exposes it.

**Stop:** `GetMod("PTFR_QR9_Diagnostics").stop()`. Stop on a replay, duplicate reward/listener/actor or stalled cleanup. Keep the failing branch and its logs.

**Collect after quit:**
```powershell
& 'C:\Users\Ayong\.local\bin\python3.14.exe' -X utf8 -B 'C:\Users\Ayong\Documents\cp77 modding\tower ws\prealpha\quest_restoration_qr9\collect_observation.py' --run-id S08_01 --card S08
```

**Return:** Bundles, source clean-route card, chosen interruption/reload stage and observed reward change; screenshot only a visual actor/door issue.

**Branch:** Never combine mutually exclusive outcomes or reuse a progressed branch as its own fresh baseline. File rollback cannot undo persisted owners/rewards.

## Reuse or isolate a branch
- G0: First short smoke only. No quest progression, no master overwrite and no broad playthrough.
- G1: The completed-history idle subcase may follow a successful smoke on the same reviewed working branch, using a separate bounded capture. It is not the full old-controller/clock test.
- G2: Ordinary supported routes may share normal play only after the preceding queue/call/cleanup settles and no action invalidates the next genuine prerequisite. Do not overlap timers just to reduce commands. Late-future/negative/already-issued alternatives stay on separate genuine branches.
- G3: Keep each pending native helper/vendor/timer owner on its own branch. Segment captures around events; no multi-day continuous sampling.
- G4: Mutually exclusive outcomes, unearned versus progressed histories, interruption and reload cases use independent branches. Save only through native permitted menus; never force an unavailable fixture.

## Limits carried forward
- Career early original-owner retirement, Cuckoo null-source provenance and Voodoo exact door/container/consumer history remain five UNKNOWN contracts. These shared-system cards do not certify them.
- First Ronald enrollment/contact/native bar support remains a FAIL/held extension. No new subscription is created for a fixture.
- MQ00711/51/95 admission/opaque loot is not certified by its future1101 helper test. MQ037 has containment/preservation only, not a general sequel adapter.
- Old custom CVI requests, old Ronald sent1/native clocks, already-skipped branches, internal graph activation and specific saved-handler refresh remain explicitly outside proven support.

## Recording a result
PASS is limited to observed behavior. Use NOT_TESTABLE for an unavailable genuine history on the named selected fixture; use INCONCLUSIVE when a required internal observation is missing. No gameplay has been executed. S01 is NOT_TESTABLE on the selected completed-CVI02 master; other unperformed scenarios remain NOT_TESTED.
Use the JSON/CSV template or just send the brief observation and bundle; Codex can fill the technical fields. Unavailable prerequisites are not evidence of a gameplay defect.
