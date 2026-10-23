# PA1 ending entry integration

Status: new staged sources and 16 source/lifecycle-model tests pass. The parent
must compile the full consolidated package and perform the live ending run.
No installed or historical pinned source was changed by this component.

## Selected test run

`PreAlphaEntry.DevelopmentLateEnding()` is explicitly `true` in this pre-alpha.
The selected fixture is ManualSave-10, Things Done Changed, level 48, saved
22:04:51 on 20.09.2026. Read-only save evidence is in
`research/pre_alpha_clean/manual10_facts.json` (SHA-256
`62742BF7E77451D5498AB724EEECD10CD2E35AFEF3442361D67A29BBDD486B3B`).

The coordinator arms automatically only while the Things Done Changed journal
root is active, q307 active/2079/base-killed/EP1-killed are 1, and completion and
direct-return facts remain 0. Arm state persists in subsequent game saves.
This observes an actual late-ending session; it does not manufacture a snapshot
of the 2077 pre-Tower world. The selected run tests development admission after
the normal finale, credits and retained-session return.

After the existing complete-Tower predicate and three safe gameplay ticks:

1. Request the separate one-time H10 street arrival and wait for its completion.
2. Call the existing accepted `ProfilePolicy.FullNerf()` transaction. Wait for its
   stage 4 completion. HP150, Body3, Relic and implant-related restrictions remain
   owned by the existing R1/R2/R3 modules and their saved refund journals.
3. Request current whitelist gigs through the original U9 dispatcher. In this
   test, incomplete gigs use the user-approved development unstarted assumption.
   Native terminal, objective, duplicate-owner, tier, consequence and phone
   checks still apply. Rechecks every five seconds can admit a transiently
   blocked candidate; an acknowledged Request never starts a second owner.

An already post-Tower save without a PA1 observed ending/test arm does not
silently enter this automatic test. Public U9 development commands still exist.

## Actual pre-Tower capture route

The same component can observe a genuine ordinary pre-ending world. It captures
all journal paths, local facts and terminal facts for the current 72-item U9
catalogue twice before committing a sample. The saved catalogue fingerprint is
the exact original `NativeGigDataU9.generated.reds` SHA-256. Only an observed
native point-of-no-return callback, before teardown, with a settled journal and
a sample at most six simulation seconds old can certify the frozen snapshot.
Each eligible gig must still match that sample at cutoff. An individual changed
gig loses eligibility; no subsequent fact clearing recovers its freshness.

Classification: 1 unstarted; 2 started journal content; 3 completed/failed or
terminal outcome; 4 missing/unsupported evidence. Nonzero local progression
facts with an otherwise inactive journal remain unsupported rather than being
called definitely started. Only class 1 can be certified. Native tier/ordinary
ready facts are not in the U9 local progression list.

Loading after cutoff never certifies old unfrozen history. Valid already frozen
history survives load. On the certified route `RestoreCertified(id)` verifies
the certificate itself, then uses the same U9 runtime admission. Native quest
facts, journal entries, tiers, counters, rewards and graph progress are not reset.

The selected late-ending run does **not** test this true pre-Tower capture route;
that needs a later separate production deployment playtest.

## Package integration and APIs

Install the files under `scripts/` into the single package script folder,
preserving their module/class names. This replaces the old NativeGigsU9 source
and the old ProfilePolicy source; do not include both definitions. The profile
clone adds only three read-only getters inside the original class; exact-delta
tests preserve all original profile/refund/HP behavior. ProfileEntryPA1 is now a
comment-only compatibility file because REDscript cannot add methods to a new
scripted class through annotations. Include original NativeGigDataU9 generated
data, the phone agent's new GigPhoneU9/EntryInterlocks, the arrival component,
JohnnyVoiceJV1 and all accepted R1/R2/R3 restriction scripts (with the current
checkpoint HP repair). Keep original U9 native graph archives in the combined
archive. No legacy ActivityState, ActivityDefinition or GigDataB7 class is
required by these three entry files.

Retire the old ActivityState automatic dispatcher. Old G1/G2/G3/B5/B6/B7 and
U1/U4/U6/U7/U8 runtime classes and their bootstrap roots are not prerequisites.
The phone source independently checks legacy save facts using current U9 data.
The separate Only Pain pilot can remain dormant if the overall package retains
it; PA1 does not invoke it automatically or expand sidejobs.

Primary diagnostic system: `PTFR.ActivityStateR3.PreAlphaEntry`.

- `Status()` reports observed/certified history, selected development test arm,
  actual completed-Tower gate, profile completion and the current waiting cause.
- `Inspect(id)` / `InspectAll()` report captured classification and latest
  per-gig dispatch result.
- `CaptureBeforeEnding()` permits an explicit observation only before cutoff.
- `Certified(id)` and `DevelopmentArmed()` distinguish the two admission modes.
- `PostEndingAuthorized()` is the read-only guard used by the arrival component.

The profile bridge adds only read-only getters. Actual migration uses the
existing profile public API; a faulted transaction is never reset or replayed.

## Checks

Run `test_entry.py` with Python 3. It covers whitelist fingerprint/72 unique IDs,
absence of native writes and retired pilot dispatch, unchanged U9 poll/tier/
retaliation code, certified/development separation, native cutoff timing,
changed-at-cutoff exclusion, unknown post-ending loads, exact late-fixture
admission, delayed profile completion, terminal preservation, and repeated
request/reload models. These are static checks and independent models, not
proof of engine callbacks, persistence serialization, calls or gameplay.

`test_cet.py` executes the actual unified CET diagnostics source under bundled
LuaJIT. Its 99 cases check exact REDscript system/method/argument signatures,
absent or changing sessions, absent methods and RTTI errors, malformed gig IDs,
and that importing or calling the seven diagnostics performs no native write or
event/override registration. Reports are saved beneath
`research/pre_alpha_clean/entry/`.
