# Voodoo Treasure first attempt on 6 November

The player opened the native stash and took the Rook. PTFR's entry never issued in the captured saves, and the saved wrapper remained at its first admission wait. This run establishes native access and the item taken. It does not exercise the PTFR reward or cleanup path.

## Live observations

- At 11:23:30, the accepted HS1 fallback reported `HistoryAllows=true`. S23 reported `postTowerReady=true`, `currentMatch=true` and `safe=false`. Voodoo had Ready 1, Permit 0, Issued 0, Finished 0 and Fault 0.
- At 11:25:47, the read-only console output showed Permit 1, Entered 0 and Fault 0. This proves the script granted permission at that instant. It does not sample the simultaneous graph door predicate.
- The user reported only the Rook and the later getters Entered 0, Finished 0 and Fault 0. This last report is user evidence. The selected verified console excerpt ends at the earlier permission sample.

[Verified console excerpt](nov06_console_excerpt_verified.json)

## Read-only save comparison

| Slot on 6 November | Door PS | Keypad authorization | Stash and reward evidence |
| --- | --- | --- | --- |
| AutoSave-13 at 11:22:14 | Closed, ON | No serialized record | No matching stash subinventory, Rook or stash shard in the parsed inventory |
| AutoSave-14 at 11:27:43 | Closed, ON | No serialized record | Same selected inventory state and money total |
| AutoSave-15 at 11:29:58 | Open, ON | `941229=1` | Exact stash subinventory present and empty. One Rook now in inventory 1, money total unchanged, and no stash shard |

All three saves serialize Ready 1 and Permit 0 and omit the private Issued, Entered, Finished and Fault values. Missing serialized rows remain distinct from the user's live zero readings. The third save also shows the exact stash's quest mark cleared and the keypad still ON. The identity comparison uses the same pinned native PS2 keys as the earlier investigation. These observations identify the physical stash. They do not identify what populated the Rook before it was taken.

The installed ArchiveXL key generates EP1 phase node `6479`. All three saves have the exact `[1,6479]` path, the parent phase registration, and the same saved logical-condition slot `7696` at wrapper node `2`. No related freezer group or deeper wrapper path was found. Node 2 is the pre-issue AND wait. The saved permit was already back at zero in the nearest closed-door snapshot. No sample proves permission, a loaded closed door and all other checks held at the same instant. In particular, neither the saved record nor the successful keypad interaction proves the wrapper resolved its short NodeRef while permission was high.

[Save pins](nov06_autosave_pins.json), [reward and PS2 evidence](nov06_autosave_readback.json), [saved wait evidence](nov06_wait.json), [entry graph and placement report](REPORT.md)

## Disposition

Classify the result as **native first access observed, PTFR entry unexercised**. The evidence does not justify changing the injection payload or setting the information-download fact. The now-open AutoSave-15 is a record of the attempt. AutoSave-14 is a pinned closed-door pre-open checkpoint for a future targeted entry check. The question for that check is whether permission stays high while the exact door is loaded and closed. The earlier-claim replay scenario remains separate.

The game installation and saves were read only. To repeat the saved graph capture on the same pinned inputs, run from the workspace root and give the reader a fresh output name. The analysis script consumes the preserved `nov06_graph_capture.json` and refuses overwriting `nov06_wait.json`. Both use the existing matching save reader and QR15 structure decoders.

```powershell
& ./prealpha/voodoo_treasure_20261106_01/read_saved_stash.ps1 -SavePinsName nov06_autosave_pins.json -CaptureGraph -OutputName nov06_graph_recheck.json
```
