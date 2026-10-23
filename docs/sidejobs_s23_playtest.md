# S23 side-job playtest

Implementation and installation status: see [S23 rollout](sidejobs_s23_rollout.md).
Offline validation is not a gameplay pass. Use the same working post-Tower branch
as the S23 capture; do not replay the ending or reset quest/phone facts.

**Final selection update, 21 October:** [R6](whitelist_final_r6.md) supersedes
older selection counts below. Heroes is excluded as a whole; the installed
S27 package still needs safe new-admission denial. Do not test a new Heroes
activation as an acceptance target. Preserve already-issued/completed owners,
Claire and shared support. The fresh Brendan dumpster job is also excluded;
later Brendan jobs require genuinely earned prior completion.

## S27 new native beginnings — installed 21 October, live pending

This batch targets Claire's five-root story-race family and Heroes' original
package outcome. It does not implement general replay of already-progressed
jobs, does not undo completed quests, and does not change the restart policy
requested below. Existing restorations and the DT1 Dogtown repair stay in place.

Latest AutoSave-4 / ManualSave-23 are regression controls: their metadata records
Heroes and Claire completed. Do not clear completion facts to make test fixtures.
Use a genuinely unstarted branch for the new-entry checks; no ending replay is
needed merely to check that the current working branch remains stable.

- [ ] Existing-branch regression: no duplicate Heroes bike/keys/reward, no new
  Claire story races, repeatable races and current side jobs retain their state.
- [ ] Claire fresh family: original invitation/contact and garage conversation;
  City Center, Badlands, Santo Domingo, Big Race; native choices, cars, rewards,
  failure paths and return to normal Claire bar interaction.
- [ ] After the separate R6 enforcement patch: no new Heroes package or funeral
  admission; existing completed/issued history and bike/keys/rewards are
  preserved. Verify normal Mama/Pepe service without restoring excluded scenes.
- [ ] Johnny's supporting voice remains audible with no visible body/props.
- [ ] Save/reload before and after a call, a race or package pickup; no replayed
  initialization, duplicated NPCs/rewards or stuck phone state.
- [ ] Later fresh-ending deployment: no S27 entry before Tower/credits/handoff
  finish; restoration only after the normal post-Tower state is ready.

General unfinished-job restart remains pending exact old-owner retirement and
local persistence/reward handling. Sacrum's enemies start alongside the hook:
early conversation facts alone do not establish a safe combat/loot reset.

Manual read-only inspection after a cold launch and 20 seconds with menus closed:

```lua
local s = Game.GetScriptableSystemsContainer():Get("PTFR.SideJobsS27.SideJobsS27"); print(s:Status()); print(s:Inspect("07_nc_underground")); print(s:Inspect("sq018_jackie"))
```

Completed/currently progressed roots should report a protected state with no new
Issued owner. A genuinely fresh eligible route may issue and then wait on its
original prerequisites or timers. Issued is not proof of a working conversation,
package, race or reward. Do not force Permit/Issued/native progress facts.

## S26 restart/NPC policy — 17 October, implementation pending

The new requested policy supersedes the Inactive-only rule below: completed
whitelisted jobs remain completed; started-but-unfinished and never-started jobs
begin at the original beginning. Migration must happen once, not after every
reload/death. No automatic restart has been installed for this policy yet.

### Immediate Cassius diagnostic (installed)

Load the same working post-Tower save; no ending replay or fact commands.
Before entering Cassius's shop, run:

```lua
print(GetMod("PTFR_SideJobsCaptureS26").ArmCassius())
```

Close CET, open his shop normally, select Hands and attempt the free tattoo if
visible. Close the shop, reopen CET and run:

```lua
print(GetMod("PTFR_SideJobsCaptureS26").Capture())
```

Capture automatically stops observation and writes `capture_s26_*.json` in the
helper's installed CET folder. It also reads all 58 roots. No stock generation,
item grants, cyberware installation, quest/fact changes or automatic saving.
If abandoning the test, `print(GetMod("PTFR_SideJobsCaptureS26").StopCassius())`
disarms only this helper. The capture is diagnostic, not a repair/gameplay pass.

### Restart implementation acceptance (pending)

- [ ] Before any migration, preserve a separate manual save and verify exact
  current completion/owner/item/reward state. Never reset a completed job or
  complete sibling just to simplify a shared-family restart.
- [ ] Retire an old owner before launching its replacement. No duplicated actor,
  phone call, reward, vehicle or unique item; ordinary reload resumes the new run.
- [ ] For every restored job, verify required NPC dialogue, contact/SMS, shop,
  reward availability, original payment and cleanup—not merely a marker/spawn.
- [ ] Cassius regression: shop already opens; check the native free reward for
  The Gig, successful collection and completion, no second reward, and unchanged
  post-Tower cyberware restrictions. Ozob is separately reported completed.

## Unstarted-first priority — 16 October

### S25 clarification and next batch

Latest rule: **new activations require an Inactive job root**. Already-issued
restorations continue with their saved progress. This also narrows the old S22 /
S23 admission checks; a saved Permit must not bypass the native Inactive gate.
Failed, Active, completed and unknown roots are not newly admitted. An Inactive
root with previous progress still needs an explicitly supported native route;
it is not permission to reset facts, items, choices or rewards.

S25 build `prealpha/sidejobs_s25/build/s25_04` was installed on 16 October at
15:41 UTC. Five new bounded fresh-entry owners cover 19
whitelist roots, including family children. This is not 19 immediate markers.

| Fresh entry | Live acceptance test |
|---|---|
| The Gun | Wilson message/objective, normal shop access, stock “Ask about order” flow, Dying Night acquisition and exactly one reward; existing weapon/completed job must block. The original first-meeting prop/attention staging is intentionally not replayed. |
| Paid in Full | Viktor's original debt option, native price/affordability and debit, one journal completion, normal clinic service afterward; previously paid debt stays paid. |
| Beat on the Brat family (6 roots) | Fresh Fred introduction/tutorial invitation, native intro/tutorial handoff, gym/default service recovery, each unlocked fight and final branch, original bets/rewards; no second S22 owner. |
| Human Nature / Tune Up / Epistrophy family (10 roots) | Original vehicle incident, repair delay and return, Delamain contact/briefing/scanner, each of seven cars and final return reward; no replay of the existing 3/7 resumed branch. Excluded sequel is not started. |
| The Prophet's Song | Original local sermons, donation/choice branches, encounter and cargo progression, completion; already-heard sermons or donations are not reset. |

- [ ] Cold-launch and load the same working post-Tower branch, then make a
  separate manual save. Close CET/menus for 20 seconds, safely on foot.
- [ ] Existing restored jobs and their progress remain intact, with no repeated
  opening calls/rewards. Already completed debt/The Gun stay completed.
- [ ] The frozen capture has progressed/completed states for all five owners;
  this branch is a regression control, **not** a fresh-gameplay fixture. Use a
  separately preserved genuinely unstarted branch for the table above. Do not
  force journals, counters or Issued flags to manufacture a pass.
- [ ] Failed/Active/Succeeded roots and a saved stale Permit remain blocked from
  new admission. Existing Issued=1 owners are not restarted or disabled.
- [ ] Check death/reload and new-save/cold-reload, no duplicate rewards, normal
  vendor/phone cleanup, and Johnny voice with no visible body where applicable.
- [ ] CET stays quiet unless manual diagnostics are requested.

```lua
local s = Game.GetScriptableSystemsContainer():Get("PTFR.SideJobsS25.SideJobsS25"); print(s:Status())
```

```lua
local s = Game.GetScriptableSystemsContainer():Get("PTFR.SideJobsS25.SideJobsS25"); print(s:Inspect("mq026_conspiracy"))
```

The overall inventory has a bounded route for 52/58 whitelist roots, not support
for every progress state or a 52-job gameplay pass. Heroes and Claire's five
story-race roots remain pending. Claire's connected vehicle-hacking phase was
not found in installed official archives; it has not been replaced or silently
cut. The working repeatable races remain installed. Aaron's missing partial SMS
is still parked. Full fresh-ending deployment remains an alpha test.

The user has redirected **new development** to whitelisted, unstarted side jobs.
All existing restorations remain installed, including progress-preserving ones.
The earlier checklist below remains as a historical/full acceptance list, but
Aaron's missing-message repair and other partial-progress expansion are deferred.
Do not require those deferred tests before working on unstarted jobs.

- [ ] Inventory each whitelist family's fresh entry separately from resume
  coverage. An adapter for one captured stage is not every-stage support.
- [ ] Reuse already-installed fresh paths; do not add a second quest owner or
  reset Ready/Issued to rerun them. Candidate smoke tests include Only Pain,
  Sacrum Profanum, Big in Japan, Brendan's initial encounter and Over the Edge,
  provided that the chosen save still meets their native entry conditions.
- [ ] Audit missing fresh versions of jobs completed on the captured branch,
  including The Gun, Paid in Full, Happy Together, Shot by Both Sides, Heroes,
  Violence and Spellbound. Their completed state must remain untouched here;
  use a separately preserved, genuinely unstarted branch for later live tests.
- [ ] Audit fresh family beginnings separately for The Gig, Beat on the Brat,
  Epistrophy/Human Nature/Tune Up, Claire's story races, Moving Heat, No Easy Way
  Out and The Prophet's Song. Existing bounded resume or repeatable-race owners
  do not establish fresh-story support. Do not change their existing routes.
- [ ] For each new fresh route, preserve the original graph, local prerequisites,
  calls/messages, waits, rewards and Johnny voice/hidden-body behavior. Verify
  actual interaction, completion and save/reload; a marker alone is not a pass.
- [ ] Reject completed, progressed, unknown and already-owned states for the new
  route. Include negative tests that preserve all existing recovery routes.

The frozen pre-rollout capture has 33 Inactive roots, but some have significant
progress (Skippy, The Prophet's Song), and seven Inactive boxing/Delamain children
belong to active families. Inactive alone is not a freshness certificate. Facts
absent from a saved file are not proven live zero. Stock passive initialization
also need not mean that the player started a quest; interpret it per job.

The priority change itself installed no files. The S24 batch below adds bounded
fresh-entry coverage; the remaining queue is not a completion claim.

## S24 fresh-entry batch — live tests pending

Installed build: `prealpha/sidejobs_s24/build/s24_02`, 16 October at 14:33 UTC.
Compilation/static/deployment checks passed; no gameplay pass is claimed.

Seven new fresh routes preserve all existing S23/S22/S2/S1 restorations. Admission
requires actual Inactive journal entries **and** job-specific unstarted progress,
message and existing-owner checks. It does not reset Failed, Active, completed or
partially progressed jobs. Unknown state defers; no pre-ending certificate is
invented. Native prerequisites and waits remain in place.

**Fixture warning:** all seven candidates were already started or completed in
the frozen S23 capture. That branch is a protection/regression test, not a way to
see seven new entries. Do not zero facts or change completed journals for this
batch. Fresh gameplay tests need a separately preserved branch where the tested
job was genuinely unstarted. A full fresh-ending deployment remains deferred.

| Fresh route | Required live checks |
|---|---|
| Happy Together | Native Barry/police hook, actual dialogue, branching objectives, one native completion; no replay on the completed branch |
| Violence | Original eligibility/wait, Lizzy call and text/contact visibility, motel interaction, native objectives/rewards, phone cleanup |
| Spellbound | Nix's original prerequisites and distance/wait; contact/call/SMS, quest conversation and normal Afterlife Nix service handoff, native completion/reward |
| The Gig | Wakako's original cash dialogue, contact visibility, Cassius's additional-reward objective and native item-possession check; no prior cash/reward replay |
| Shot by Both Sides | Original Mr. Hands hook/call/contact, native stages and choices, completion/reward and cleanup |
| No Easy Way Out | **Fresh opening only:** Fred contact, original invitation delay/SMS, first encounter and clinic stages; no second S23 partial-progress owner. This does not fix the parked missing Aaron follow-up message |
| Moving Heat | Ashley contact/invitation and native delay, garage entry and later objectives, unique vehicle protection, completion; preserve the existing S22 accepted-message branch |

- [ ] Cold-launch, load a preserved working post-Tower branch, make a separate
  manual test save and close CET/menus for 20 seconds in a safe on-foot location.
- [ ] Existing Epistrophy/boxing/The Gig/Moving Heat/Skippy progress is unchanged;
  completed candidates stay completed. No new seven-entry expectation here.
- [ ] On a genuine fresh fixture, test the appropriate row above. Marker/Issued
  alone is not proof of a working interaction. Follow original delays rather than
  forcing timers, phone flags or Permit/Issued facts.
- [ ] Verify exactly one quest owner, one appropriate reward, normal service and
  phone behavior afterward, death/reload and a new-save/cold-reload.
- [ ] Where Johnny has dialogue, hear his voice without a visible body. Ordinary
  CET operation stays quiet after restoration.

Read-only diagnostics:

```lua
local s = Game.GetScriptableSystemsContainer():Get("PTFR.SideJobsS24.SideJobsS24"); print(s:Status())
```

```lua
local s = Game.GetScriptableSystemsContainer():Get("PTFR.SideJobsS24.SideJobsS24"); print(s:Inspect("mq015_wizardbook"))
```

At the S24 boundary, fresh The Gun, Paid in Full, Heroes and The Prophet's Song
were deferred. S25 above adds bounded routes for all except Heroes while
preserving existing restoration owners. This paragraph is historical context.

## Short smoke test

1. Cold-launch after installation. Preserve the original save and use a new manual
   save branch for testing. Close CET and menus for about 20 seconds, on foot in a
   safe location with no call/conversation running.
2. Check that existing Epistrophy, Beat on the Brat, The Gig and Moving Heat retain
   their progress. Completed quests must remain completed.
3. Read the S23 status when needed; it is intentionally quiet otherwise:

```lua
local s = Game.GetScriptableSystemsContainer():Get("PTFR.SideJobsS23.SideJobsS23"); print(s:Status())
```

4. No Easy Way Out should resume the captured Aaron follow-up, not the clinic.
   Check the existing Aaron text thread and current objective. Do not force its
   facts or replay its opening to make an entry appear.
5. Visit one new quest's normal start location or follow its original message.
   Mark a pass only after a real interaction, not merely a map icon or Issued flag.

Not every job immediately appears in the journal. Native prerequisite quests,
local triggers, phone queues and delays remain in effect. Completed roots are not
added back. A refused/mismatched stage remains untouched; report its diagnostic
instead of forcing Permit/Issued/start/done facts.

```lua
local s = Game.GetScriptableSystemsContainer():Get("PTFR.SideJobsS23.SideJobsS23"); print(s:Inspect("mq306_dumpster"))
```

## Deferred full playtest

Record save branch, job, exact objective, observed result and any diagnostic. For
each applicable row verify start/resume, dialogue, objective progression, one
reward, cleanup, new-save/cold-reload and no replay/duplicate NPC. Keep existing
earned rewards and completed siblings unchanged.

| Family | Checks still required |
|---|---|
| Full Disclosure; Send in the Clowns; Burning Desire; Gun Music; Fortunate Son; War Pigs; Sex on Wheels | Original local/phone prerequisites, real scenes and native completion/rewards; Sandra's data-carrier branch |
| Machine Gun / Skippy | Preserve firing mode, gun and counters; no pickup or 50-enemy conversation replay; follow the separate confirmed-history recovery instructions |
| A Day in the Life; Bullets; Shoot to Thrill | Quest interactions coexist with ordinary shop service; Zane/Wilson return to service after quest exit/reload; no duplicate scene owner |
| Big in Japan; Brendan's three jobs; Over the Edge; The Prophet's Song | Original hooks, staged progression and waits; existing sermon/choice history is retained |
| No Easy Way Out | Resume Aaron's existing SMS outcome, no clinic replay or duplicate earlier payout; final native cleanup |
| Voodoo Treasure; New Person, Same Old Mistakes; Go Your Own Way; Addicted to Chaos; The Show Must Go On | Native prerequisites/messages/rewards; Bill and Hasan's persistent services; Steven does not duplicate an active Spy in the Jungle owner |
| Hidden Rayfield/Colby vehicle jobs | Native vehicle availability and ownership checks; no duplicate grants; stock local spawn/unlock behavior |
| Existing S1/S2/S22 adapters | Only Pain and Sacrum Profanum admission; boxing sibling progression; unfinished Delamain cars with completed ones protected; existing The Gig/Moving Heat progress |
| Cross-cutting | Johnny voice remains, body hidden; phone traffic not blocked; quiet CET; death/reload; no completed/out-of-whitelist/main-story restart |

## Separate future integration

- Genuine pre-Tower Inactive-history certification and a complete ending-to-H10
  run are separate future acceptance tests. This development capture is not such
  a certificate.
- Alternate partial-progress seams, all branching outcomes and all live reward
  variants are not certified by the current source/policy tests.
- File rollback cannot undo quest progress already written into a test save.
  Retain the original branch.
