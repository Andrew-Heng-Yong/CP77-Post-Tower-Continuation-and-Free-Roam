# PA1 entry review

Read-only review, 2026-10-12. This supplements the component README and the
parent's combined compile/deployment evidence; it does not report a live pass.

## ManualSave10 compatibility

The parent's `research/pre_alpha_clean/manual10_facts.json` audit records
unchanged save SHA-256
`62742BF7E77451D5498AB724EEECD10CD2E35AFEF3442361D67A29BBDD486B3B`.
Recorded values are q307_active=1, q307_2079=1, q307_main_game_killed=1 and
q307_ep1_killed=1. Completion and retained-session marker names were absent from
the sampled serialized tables. Metadata points to
`ep1/quests/main_quest/q307_tomorrow/01_hospital_cabride/05_meet_viktor`.

This is consistent with the intended late-ending test fixture. The live arming
predicate additionally verifies the q307_tomorrow root is Active and all four
completion/handoff markers equal zero; the offline absence of a fact is not
reported as proof of its live value. If that live predicate fails, no test arm
is granted and no automatic initialization occurs. Status exposes this clearly.

The fixture is already in 2079 after world cleanup. It cannot prove what gigs
were unstarted in 2077. The explicit development flag uses the user's incomplete-
as-unstarted assumption while leaving the actual history certificate false.

## Credits and safety ordering

`PreAlphaEntry.Completed()` calls `CyberwarePolicy.Completed()`, which requires
both `PTFRP0_DR13=1` and `PostTowerFreeRoamActive=1` in addition to all completed
Tower, killed-world, no-active-quest and no-Johnny-scene guards.

`tools/build_phase2b_p0.ps1` lines 108-145 establish the retained return chain:
native credits-rolling false, delay, second false check, Tier1 and player show,
six finalboards restriction removals, finalboards content Unblock, then
PostTowerFreeRoamActive and DR13. Thus the gate is downstream of the existing
credits cleanup. q307_done alone cannot trigger entry. Historical diagnostics
in `research/phase2b_p0/runtime/analysis.md` identify the unexposed credits UI
blackboard and infer teardown from UI close/uninitialize/idle; the new source
does not invent an unavailable blackboard predicate.

After these facts, three consecutive BodyPolicy.Safe ticks require a live,
non-replacer player, safe scene tier, closed menus, no dialogue/rewind/content
blocker/workspot/vehicle/combat/time dilation, settled equipment, holstered
weapons and no Overshield. Arrival is requested first. Its completed ack precedes
the profile request. Profile stage 4 precedes any automatic U9 gig request.

## Saved-state and repeat behavior

- History schema, data fingerprint, 72 snapshots, frozen eligibility and the
  late-ending test arm are persistent. Epoch/timers/log strings are transient.
- A load after cutoff cannot certify an unfrozen snapshot. Already certified
  snapshots are validated for shape and preserved. Ordinary-world return drops
  the frozen eligibility and awaits a new observed sample.
- Two full reads must agree before a pre-ending sample is committed. Native
  cutoff freezes the old sample and only certifies individually unchanged fresh
  entries. No post-cleanup sample becomes history.
- Profile getters do not mutate. The established R1/R2/R3 transaction owns all
  refunds, already-inflight interruption handling and HP checkpoint restoration.
  A faulted profile stops coordinator dispatch and is never reset by it.
- Automatic retry uses existing U9 Request state. Acknowledged, entered or used
  owners retain the existing duplicate protection. Native terminal/outcome and
  objective guards, phone service lifetime, original tier branches and original
  gameplay poll remain unchanged from U9.
- The new coordinator never calls a save API, writes a native fact, activates a
  journal entry, grants items or manually pays a gig reward.

Remaining proof: combined compiler/readback; live late-arm, normal Tower and
credits, one-time arrival, profile completion, native phone/marker/gameplay,
and new-save/death/load persistence. True pre-Tower capture needs its own later
playtest and is outside the selected late-ending fixture's evidence.
