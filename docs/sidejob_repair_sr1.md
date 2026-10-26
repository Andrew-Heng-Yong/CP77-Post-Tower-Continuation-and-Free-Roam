# PTFR side-job repair SR1 — development evidence

**Status update, 26 October 2026:** The repair was consolidated into the existing three S29 files and installed locally with the user's authorization. The earlier overlay package described below is historical and was never installed. See [production install record](sidejob_repair_sr1_production.md).

26 October 2026. This is a workspace-only candidate based on the 78-side-job vanilla audits. The game, saves, runtime facts, installed frameworks and published alpha were not modified. The user's earlier instruction to hold installation remains in effect.

## Repairs in the staged package

| Area | Scoped change | Source result and limit |
| --- | --- | --- |
| This Corrosion | Restore Yoko's four native component choices and outputs only while the restored quest owns the conversation and its journal is active. | Preserves vendor dialogue, original choice conditions, component transfer and writer; gameplay still needs a Yoko visit. |
| Bullets | Restore the original Zane default-dialogue rearm loop inside the private owner. | Shop service should return after the encounter and lease releases; live timing still needs testing. |
| Where Eagles Dare | Connect the wrapper's finished receipt to the native child's `End Quest` output; retain the old output socket for saved-owner compatibility. | Native reward and cleanup routes are unchanged. |
| Don't Lose Your Mind | Remove seven Epistrophy message-*Inactive* checks from the sequel's fresh admission guard and aligned S29 runtime table. | Preserve predecessor completion and all sequel-specific checks. Does not admit a failed Epistrophy save. |
| Delamain phone | Publish a shared receipt when S25 starts the persistent controller, exclude that owner from S29's bootstrap, and adopt completed saved S25 owners at runtime. | Prevents a second controller on the proved source route; saved/active phone behavior requires live testing. |
| Sweet Dreams | Route both elevator Johnny workspot commands to the existing muted private workspot at the same world marker. | Addresses the user-observed floating cigarette. Position, transition, smoke and item behavior need live confirmation. |
| Don't Lose Your Mind / Killing in the Name / Freedom / KOLD MIRAGE | Route their exact Johnny smoking workspots through muted private assets at the original markers. KOLD MIRAGE gets a private copy of its exact native workspot with only `eventFilterType` changed to `Mute`. | These were source-confirmed smoke/item routes, not all observed visual bugs. Matching `StopWorkspot` commands were switched with each route. |
| Sinnerman | Remove only the restaurant ember event that targeted deleted Johnny cigarette prop 50. | No quest node, dialogue or other scene event changed. |
| English facial animation | Register 44 copied private scene paths in a new English lipmap through ArchiveXL. | All required voice tags have native donors; English live playback still needs checking. Other spoken languages are not in this candidate. |

The candidate consists of five files: three new archives, one new ArchiveXL registration file and one replacement S29 REDscript. The selected archives are `zzzz_PTFR_SideJobs_SR1.archive`, `zzzz_PTFR_SideJobs_SR1_Visual2.archive` and `zzzz_PTFR_SideJobs_SR1_Lipmap.archive`. Earlier `Visual.archive` is an uninstalled historical workspace candidate and is excluded from the manifest.

## Validation

- Six quest resources passed scoped native graph and condition comparisons, with no unrelated route changes.
- Full 94-source REDscript compilation including EquipmentEX passed; compiled script SHA-256 `C9DBE0E6458A31F1B8F9CE4A568D201CE98C6C070F9F92AD6D91ABC941852744`.
- The visual scene readbacks match serializer baselines after reversing only the intended workspot and orphaned event changes. Handle references resolve after serializer renumbering. The private KOLD workspot differs from the native workspot only at its event filter.
- All 44 English scene paths, required voice tags and ArchiveXL configuration match the pinned native donor plan.
- All three archives were packed and read back with exactly their intended resources. Installed override collisions and load order were checked. The new KOLD workspot and English lipmap have no installed resource collision.
- The installer passed 17 fixture actions, including normal install/verify/rollback and interrupted deployments after files 1, 3 and 5. The real five target paths stayed unchanged. A read-only validation against the actual installation reports `READY`.

Evidence: [candidate and manifest](../prealpha/sidejob_repair_sr1/candidate_02/install_manifest_01.json), [quest readback test](../prealpha/sidejob_repair_sr1/candidate_02/test_native_01.json), [visual tests](../prealpha/sidejob_repair_sr1/candidate_02/test_visual_02.json), [lipmap test](../prealpha/sidejob_repair_sr1/candidate_02/test_lipmap_01.json), [fixture deployment test](../prealpha/sidejob_repair_sr1/candidate_02/deployment_tests_02.json). Sources and prior candidates are retained for review; `candidate_02/package` is the selected staging directory.

## Live acceptance after a later install

1. Cold-load an untouched pre-ending fixture and finish the Tower transition. Ensure the setup cover releases, save manually, then reload that save.
2. For Sweet Dreams, use both elevator and payback variants. Confirm Johnny's cigarette, ember and smoke are absent while his voice, timing, Stefan's voice/facial animation and scene progression remain.
3. For This Corrosion, use each relevant Yoko component choice and complete the handoff; check vendor options remain available outside the quest.
4. For Bullets, finish the encounter and message phase, then talk to Zane and use his shop before and after save/reload.
5. For Epistrophy → Don't Lose Your Mind, use a successful predecessor save that has exchanged phone messages. Confirm the sequel appears, only one Delamain controller contacts V, and a new save/reload does not duplicate calls.
6. Check Where Eagles Dare completion receipt, Sinnerman restaurant, the four other Johnny smoking routes, and representative dialogue in all 44 English lipmap scenes. Prioritize the scenes affected by the already reported Stefan mouth issue.

No live result is claimed by these offline tests. Existing active saves may already contain a scene or owner at a changed node; keep an untouched test save and do not overwrite it. File rollback restores installed files, not saved quest state.

## Gaps intentionally not folded into this candidate

- Original-scene cigarette equip events in Shot by Both Sides and Beat on the Brat: The Glen need private scene copies and scoped native-phase retargeting. A global original-scene override would change pre-ending vanilla gameplay. Their item visibility has not been reproduced live.
- Bullets, Happy Together and Freedom Johnny appearance VFX events are source-level policy risks; visible effects have not been reproduced. Removing original-scene events globally would change vanilla play. Freedom's scene still retains its separate `johnny_appear_glitch` event.
- Nix/Viktor phone returns and The Gig/Cassius tattoo purchase need separate service/UI diagnosis. The tattoo reward exists in source, but the live purchase failure's cause is unproven.
- Four gig phone-controller omissions are outside this side-job-only repair. Other languages need their own lipmap registration and donor validation.
- This does not prove all 78 side jobs complete correctly. Arbitrary active-save resumption, actors, streaming, map refresh, phone scheduling, rewards and death/reload require playthroughs.

Installer for the selected candidate: [deploy_01.ps1](../prealpha/sidejob_repair_sr1/deploy_01.ps1). Its default action is read-only `Validate`; `Install` has **not** been invoked on the real game. The recovery path prepared for a future install is `recovery/sidejob_repair_sr1_01`.
