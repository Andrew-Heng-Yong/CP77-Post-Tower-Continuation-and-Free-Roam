# Native registration correction for the MS31 handoff

The v0.1.9 MS31 run detected the native expiry of Falco’s wait before The Tower removed the original handlers. It rebuilt the quest phases after genuine ending completion, then rolled back during handler setup. The live deferral grouped creation, readback, and notification enrollment under one reason. [MS31 live result](../universal_resume_expired_wait_20261115_01/observations_01/REPORT.md)

In the pinned executable, the PhaseContext key builder at RVA 0x2B2224 writes the phase hash in bytes 0–3 and the node ID in bytes 4–7. The slot allocator at RVA 0xEB6B3C copies that key into the registration row. The v0.1.9 enrollment hook expected the separate timer mapping’s encoding, with the phase hash in the upper word. The native fixture reproduces the missed enrollment on the first phase registration even though the allocator wrote the correct row. [Predecessor reproduction](run_01/PriorRegistrationChecks.txt) · [Fixture source](LiveHandoffChecks.cpp)

v0.1.10 compares the two fields in native registration order before a selected handler can notify. The fixture verifies that unrelated registrations pass through and the selected notification is released exactly once on commit. A failed handoff now reports the selected phase and node alongside the native readback and enrollment outcomes. The scope is the checkpoint DLL. [Runtime handoff](source_01/NativeHandoff.inc)

The build passed 87 checkpoint regressions, 33 integration checks, and 21 retained-quest checks. The game executable supplied the key builder and allocator instructions. Synthetic objects supplied the phase, free slots, and notification receiver. The live MS31 handoff, Falco’s message and jacket pickup, and save/reload remain to be tested. [Exact build assessment](run_01/assessment.json) · [MS31 test card](TEST_CARD.md)

The installer passed 17 fixture actions. Closed-game preflight verified the one-DLL replacement, 52 managed files, 26 dependencies, and a 409-file save snapshot that includes the original MS31 bytes. [Staged readiness](staged_01/readiness.json) · [Preflight](staged_01/preflight_01.json)

The authorized 15 November installation replaced the checkpoint DLL. Separate readbacks verified the live payload, all 409 save files, and rollback to v0.1.9. The in-game retest is pending. [Installed manifest](staged_01/deployment_01/installed_manifest_01.json) · [Rollback readiness](staged_01/rollback_readiness_01.json)

AutoSave-5 and AutoSave-6 both retain the nine selected registrations and active Falco timer 125066 before Reed’s departure. They are about 51 metres from MS31 and within one metre of each other. AutoSave-6 is 24.1 seconds ahead of MS31 in saved play time from the v0.1.9 run. Hospital and endgame saves start after the cutoff, and loading a save clears the checkpoint’s in-memory handoff. [Read-only save comparison](run_02/assessment.json) · [Load transition](source_01/NativeCheckpoint.cpp)

The subsequent v0.1.10 MS31 run committed the native handoff, and AutoSave-17 carries the restored handlers. Falco’s message stayed absent in free roam. [Live result](observations_01/REPORT.md)
