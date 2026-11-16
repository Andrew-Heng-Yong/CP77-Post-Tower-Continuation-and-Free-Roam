# Step 2 checkpoint runtime registration

The v0.1.2 workspace candidate is ready for a main-menu startup test. It resolves the two checkpoint functions during gameplay through the installed Codeware reflection API. Its compiled history script contains zero new native declarations, so the two unresolved checkpoint names that blocked the earlier installs are no longer startup requirements. The installed game is on RD10. [Candidate manifest](candidate_04/receipt.json) · [Previous failure and rollback](../universal_resume_checkpoint_startup_20261114_01/REPORT.md)

## Repair

In the pinned Cyberpunk 2.50 executable, `CRTTISystem::GetType` falls through from an index miss to a compound-type resolver. That resolver reads the spelling from the engine’s name pool before dispatching to a type constructor. The first build passed hashed names without adding their spellings. The second build borrowed signatures from stock methods during early registration. The stock native getter constructor starts with an empty return descriptor. The live log identified all three failed getter checks and the rejected array check. [Executable and fixture checks](checks_04/results.json) · [Previous startup log](../universal_resume_checkpoint_startup_20261114_01/observations_03/ptfr_executioncheckpoint-2026-11-14-20-29-23.log)

The new registrar explicitly interns all required type names and resolves them when RED4ext enters the running state. It checks the three strong handle classes, the dynamic `Uint64` array and the scalar descriptors before publishing either function, and enables capture after both functions read back. A missing function leaves the existing history capture path available. The bridge retains the typed parameters, packed save-local checkpoint, history samples and original cutoff acknowledgement. [Registrar](RegisterReader.inc) · [Type checks](CheckpointRegistration.hpp) · [REDscript bridge](checkpoint_bridge.reds) · [RED4ext game-state API](https://docs.red4ext.com/mod-developers/custom-game-states)

## Verification

- The full 148-source compile used the restored RD10 inputs and the staged history replacement. Compiled readback removed exactly the two former native globals. It confirmed the Codeware calls, the eight persistent checkpoint fields, their type and flag identity, and the order of capture, commit and gate acknowledgement. [Compile receipt](compile_01/receipt.json) · [Compiled readback](checks_04/results.json)
- Fifteen registration fixture checks, 41 checkpoint checks and 12 Lua checks passed. The registration fixture reproduces a compound lookup miss without an interned spelling. The game executable matched eight resolver instructions and 46 existing capture anchors. The pinned Epistrophy control retained mask 70. [Verification results](checks_04/results.json)
- All 51 RD10 Core paths and 26 dependencies verified. The three staged files read back against their manifest, including the exact prior Lua recovery writer. [Candidate manifest](candidate_04/receipt.json)

## Pending live checks

After a guarded install, start the game and stop at the main menu. The checkpoint plugin log should contain `PTFR execution checkpoint runtime ready: capture and decode registered`. Verify that startup reaches the menu and that both globals registered before asking for the genuine Tower test. The next gameplay fixture is Manual Save 26 through The Tower, followed by a fresh post-ending save and reload to verify the save-local checkpoint and Epistrophy mask. Live registration and the cutoff and reload run are pending.
