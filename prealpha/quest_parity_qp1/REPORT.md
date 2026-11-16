# QP1 — Quest progression and scene support

10 November 2026. QP1 is staged against the verified JB3 installation. It includes the three requested repairs and the previously staged ML1 English lip-sync map.

| Quest | Change | Verification |
| --- | --- | --- |
| Small Man, Big Mouth | Return to Kirk journal node 618 now connects to the native garage-exit wait at 210 after V’s clothes reaction. The existing branch retains the three-input staging join and the native completion callback. | From the actual scene entry, the cooked graph supplies all three inputs and reaches End 0. The recovered branch contains 123 retained events across alternatives, including the burger placement, V’s firefight line and thug staging. Five bounded fixtures cover the old regression, the garage wait and combat completion with both old Johnny receipt values. |
| Heaviest of Hearts | The U9 entry wrapper leases six native trigger placements before discovery, covering discovery, bouncer, dealer, client, dealer interruption and cleanup. A separate post-Tower phase leases the two Kurtz chat areas and calls the original scenes. The dealer route uses the stock 15 m entry and 20 m exit checks with an existing, eligible vendor. | Typed readback matches the native trigger definitions and packed placements. The four scene markers resolve in the original AlwaysLoaded EP1 sector. The cooked caller graph verifies the two chat entries, their authored exits and the dealer’s cut and rearm path. All 101 HH1 workspots retain their prior sector hashes. |
| Killing in the Name | Rebases QR20’s Bartmoss parent-contact repair onto JB3. The existing S29 tick can restore contact visibility for the entered message handoff after validating the retained texts and the untouched website step. | The current 148-source offline compile passed. The QR20 method and tick call are the only additions to the installed S29 source. |
| Losing My Religion | Includes the exact verified ML1 English lip map covering the first monk’s opening and epilogue. | The packed map matches the [ML1 candidate](../monk_lipsync_ml1/REPORT.md) byte for byte. |

The Small Man edge preserves the existing speech cuts and native waits. WolvenKit 9.1 could not fully deserialize the stock garage sector. The separate CR2W table and decompressed placement check identifies the exact base-range garage trigger and its quest notifier. The package uses the existing native prefab lease.

The Heavy Hearts ambient routes check the actual community participants. The two chats retain their Kurtz and gig-state prerequisites. The dealer route requires earned dealer information, the retained default-on state and a spawned dealer. The owner routes authored exits and loss of eligibility through phase cleanup. Other trigger families and full gig progression, including the crowd-area and elevator startup acknowledgements, remain outside the verified scope.

## Package

The [51-file ZIP](QP1_Core51_01.zip) passed exact inventory, CRC and byte readback. The combined archive contains 1,639 payloads. Four existing resources changed, three were added and the other 1,632 retain their JB3 hashes. The new ArchiveXL phase ID is `60197`. It passed the separate checks against native EP1 root IDs and the 827 existing bindings to that root.

The three changed package files are the combined archive, its ArchiveXL configuration and `PTFR_SideJobsS29.reds`. The 51 installed Core hashes and 26 required input hashes still match JB3. [Package manifest](candidate_01/package_manifest.json) · [Graph verification](candidate_01/verification.json) · [Truck fixtures](candidate_01/truck/fixtures.json) · [Compile result](compile_01/result.json)

## In-game checks after installation

1. **Small Man, Big Mouth.** Use an eligible post-Tower save before the truck scene. Open the truck, leave the garage and follow the return objective. Observe the thug confrontation and check whether the quest continues after it.
2. **Heaviest of Hearts.** Use an eligible save before discovery. Follow the client and club approaches. Check the ambient chats when their Kurtz prerequisites are satisfied and check the dealer cue on a save with the vendor already enabled.
3. **Killing in the Name.** Load the retained-message save, open **Phone → Messages** and read the existing Bartmoss conversation. Check that the website step appears and note any new notification.

Installation, actual playback and transitions from saves already inside the affected scenes remain pending.
