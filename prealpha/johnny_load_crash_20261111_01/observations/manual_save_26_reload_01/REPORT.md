# Quest history after the 11 November Tower run

The Tower completed and the post-Tower handoff reached Ready. Manual Save 27 has the completed ending and setup facts. The snapshot passed capture at Reed’s pickup and failed retention across the hospital restart. [Original capture](../manual_save_26_pickup_01/REPORT.md) · [Exact save hashes and fields](saved_checkpoints.json)

| Evidence | Snapshot state |
| --- | --- |
| AutoSave-15 and AutoSave-16 | Frozen `pre_ending` revision 159 with original export token. |
| AutoSave-17, following the 6:06 p.m. restart | Revision 159 remains. Origin, ready, frozen and export token are absent. The save still contains the ending boundary and both native root-kill facts. |
| EndGameSave-63 and EndGameSave-64 | Revision 159 remains without the snapshot flags and token. |
| Manual Save 27 | Finished post-Tower setup. Frozen `post_ending_fallback` revision 160 with the 6:29 p.m. token. Its next observed load produced fallback revision 161. |

The inspected save reader exposes scalar snapshot fields. The exact checkpoint body loaded at the restart and the in-memory values of boundary facts during the callback remain unobserved. The installed `Restored()` clears a frozen snapshot when `Boundary()` is false. That is the only direct assignment that clears `frozen` in this system, and it runs in attach/restore callbacks. The observed metadata is consistent with that path running before restored quest facts are available. AutoSave-16 is the latest inspected checkpoint retaining the original snapshot metadata.

The native journal marks all three sampled roots Failed beginning with the first hospital checkpoint. Both fallback exports record Failed for all 13 catalogue quest roots that were Active in revision 159. Beat on the Brat and Moving Heat’s current S22 adapters require an Inactive live root. Small Man, Big Mouth’s S29 fresh-entry path requires an Inactive baseline. Retaining the snapshot addresses history. Resumption still requires recognition of each exact Tower-interrupted stage and review of ownership, progress and rewards. [Native journal mutation trace](../../../history_snapshot_cutoff/REPORT.md)
