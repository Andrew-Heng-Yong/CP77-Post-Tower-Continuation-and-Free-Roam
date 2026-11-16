# Batch 5 source edits

The ten gigs now have editable private scene and quest-phase changes based on JB3. The worksheet selects 49 Johnny and 23 V speech events, including B5-10 and both subtitle variants of V’s sound reaction. The three Backs Against the Wall conversation options are also removed. The Family Matters photo and Playing for Keeps kitchen lines, and the separate Backs prologue cat occurrence, remain on their native routes. [Reviewed worksheet](source_edits_01/reviewed_worksheet.txt)

Johnny’s scene acquisition is disabled on each edited scene. The edits remove 56 Johnny presentation events and route around his scene-specific camera, spawn and workspot operations. Physical choices, non-Johnny cast and retained speech keep their authored data.

| Gig | Edited path |
| --- | --- |
| Backs Against the Wall | Skips the exchange and menu. Keeps the single gunshot signal, the room triggers and the parent’s approach-to-body gate. |
| Cuckoo’s Nest | Connects the clinic’s optional scene entry to its original exit. |
| Family Heirloom | Connects the bootleg-triggered scene to its original exit. |
| Family Matters | Keeps physical clue choices, V’s inspection barks, the safe callback and shard checks. |
| Fifth Column | Skips the exchange after the native evidence gate. |
| Freedom of the Press | Keeps the Max condition and carry signal. V’s retained line finishes before the original extraction and cleanup callbacks. |
| Greed Never Pays | The doorway trigger fires the original Use the code signal without the exchange. The native alternate-door cancellation, device checks and movable fridge interaction are retained. |
| Last Login | Keeps the scan setup, body interaction, V’s inspection bark and focus cleanup before the original exit. |
| Nasty Hangover | Disconnects the Johnny-only listener. The meeting, phone call and payment receipt remain connected. |
| Playing for Keeps | Connects both reviewed Johnny entries to their respective native exits. |

All 42 JSON files passed readback. The manifest records the ten existing wrapper depots, 32 private copies and source hashes. The phase edits preserve graph IDs, edges, prefab references and gameplay payloads through typed depot substitutions. Verification covers 48 connected call edges and 25 bounded signal fixtures. The proposed depot keys are distinct across the captured inputs and the 1,636-member JB3 inventory. [Source manifest](source_edits_01/source_manifest.json) · [Checks](source_edits_01/checks.json)

This is a source-only change. Cuckoo’s Nest carries through four original connections with null source endpoints. Their serialized representation still needs verification in a future build. Full provider collision checks, gameplay and saved-phase transitions remain pending.
