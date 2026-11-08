# Shared native holocall studio restoration

29 October 2026. PH3 was implemented and installed for the reported missing Ana Friedman call after Ribakov, with the user's request to address similar phone failures. The repair restores shared native studio support for restored calls across both the base game and Phantom Liberty.

## Finding

The latest logs show that PH2's Mark registration correction is operating: a Mark start acknowledgement appears at 17:47:52 Toronto time and later start/end counters balance, including another call after the boss cleanup at 17:55. The next native call, internally named `janet`, starts its counter and call flag at 17:55:51, then sets `holo_setup_active=1`. No start acknowledgement is recorded afterward. The user identifies the expected conversation as Ana's. No live scene-node or actor-state capture was taken; the end of logged events does not by itself measure the waiting duration.

The native EP1 initializer owns **two root phase prefabs**, `#holocalls_studio_ep1` and `#holocalls_studio`. PH1 copied the individual initializer nodes, whose instance-prefab lists are empty, but omitted these shared root prefabs. A fresh census decoded all **997 installed private quest-phase resources** and **747 root/nested prefab bindings**: none owned either studio, and there were no unresolved numeric prefab references in that census.

The missing shared ownership is confirmed in source. It fits the new request reaching the controller but failing before its scene acknowledgement. It is a different layer from PH2's registration collision and is not proof that every possible phone failure has the same cause.

## Repair

One new private phase owns the exact two native studios at their full world references:

- `$/03_night_city/c_pacifica/#holocalls_studio_ep1`
- `$/03_night_city/ne2/#holocalls_studio`

The owner is nested beneath completed-Tower, restoration and support guards, with a persistent claim and hold. It writes only its own Claimed, Entered and Ready receipts. The Ready receipt records entry into the owner; it is not a rendered-frame or streaming-completion measurement. Phone-active and interruption flags do not block this owner, allowing an already-waiting call to gain its missing support.

These are the shared studios used by the restored native phone scenes. Native descriptors cover 138 base studio variants and 36 EP1 variants, including Janet's setup and lights. The EP1 studio payload contains her actor, workspot, camera and setup references. All native variants and their normal scene controls remain authored by the game. No arbitrary calls, quests, rewards or story controllers are started.

The original studio sectors remain untouched. WolvenKit 9.1 cannot decode some of their world nodes (`DynamicBaseClass`/`worldNode` cast failure), so this change references the original prefabs and does not claim a complete independent placement audit or edit those opaque sectors.

## Validation and installation

- Fresh 134-archive capture checked the native initializer, studio sectors and streaming-block descriptors (eight provider records). New-owner depot collision scan passed.
- All **825** additions to the EP1 quest root have unique generated IDs and avoid the five native root IDs. The new owner uses **22195**. The six existing phone listeners remain registered as before.
- 25 serialized graph/binding checks and 30 admission cases passed, including pending/active/interrupted phone flags and duplicate saved-claim refusal. These checks do not simulate engine scheduling or streaming.
- Full archive readback preserves **all 1,573 prior members byte-for-byte**, with one new resource, for 1,574 total. The old phone controllers, cleanup, gig entries, PH2 alias and Lizzie restorations are unchanged.
- Full 51-path local ZIP readback passed. No REDscript changed; no new script compilation is claimed. Beta distribution files were not revised.
- Four deployment fixtures passed, including three interrupted-install rollback cases. Actual closed-game Validate, Install, Verify and ValidateRollback passed.
- Only the combined archive and its XL were replaced. All 51 managed hashes were verified after installation; all 307 save files and 49 Lizzie's Braindances files retained their names and bytes around deployment.

The game was not launched. Ana's actual call delivery, projected actor rendering, completion of an already-stalled scene and save/reload remain **live unverified**. No further gameplay test is requested by this record.

## Recovery and evidence

Evidence is under `prealpha/phone_studios_ph3/candidate_01`, including `installed_assessment_01.json`, `semantic_verification_01.json`, `state_cases_01.json`, `verification_01.json`, deployment/preservation reports and `evidence_hashes_01.json`. Source captures and logs are under `diagnostics/phone_expansion_ph3_20261029_01`; `native_04` is the complete selected capture.

With the game and launcher closed, roll back **PH3 first**, before PH2, PH1 or LR2:

```powershell
pwsh -NoProfile -File prealpha/phone_studios_ph3/deploy_01.ps1 -Action ValidateRollback
pwsh -NoProfile -File prealpha/phone_studios_ph3/deploy_01.ps1 -Action Rollback
```

Recovery: `recovery/phone_studios_ph3_01`. This restores installation files, not saved gameplay state. No save editing, direct native-fact changes or forced quest progression was performed.
