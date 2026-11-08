# Voodoo Treasure closed-door entry check

**The current evidence places the stall before the one-shot claim. The specific failed graph condition remains open.** The installed QR19 archive, ArchiveXL registration and S23 script match their verified hashes. The 6 November AutoSave-14 body and metadata also match the earlier pins. AutoSave-15 records the opened, emptied stash and the acquired Rook. [Prior live and saved evidence](../voodoo_treasure_20261106_01/NOV06_ROOK_ONLY.md)

## Native trace

The installed executable's `questNodeLoadingCondition` constructor installs vtable `0x31C8A90`. Its instantaneous evaluation at virtual `+0xF0 → 0x2CA9AA0 → 0x14CB0B8` resolves the authored short reference through `0x2AC4FC → 0x351030` and then queries the world service at quest context `+0x1E0`, virtual `+0x190`. The inverted flag is zero, so a null handle is false.

The installed `questDevice_ConditionType` virtual `+0xF0 → 0x802218 → 0x802790` uses the same global reference helpers before requesting the controller and invoking the `IsOpen` quest getter. This rules out an automatic change of resolution scope in these instantaneous calls just because the condition moved into the private wrapper. It leaves actual alias resolution, streaming state and retained subscription refresh open. The observed `Permit=1` sample did not capture either world predicate. The nearest closed-door save serializes Permit 0 again and keeps the original wrapper wait at node 2.

The diagnostic reads the exact static EntityID identified by the cooked placement and confirmed against the saved door controller key. The registered `FindEntityByID` route `0x8138D8 → 0x21B6FC` looks up an existing entity handle. `Door.GetDevicePS()` obtains the attached controller's existing state through the registered component getter `0x2FB0E4 → 0x2FB150`. It uses the attached component handle and an RTTI cast. `IsOpen` and `IsDisabled` are state getters. This avoids the separately traced allocation-capable PersistencySystem lookup. The diagnostic's exact-ID lookup and attached-controller checks are independent observations. They do not execute the quest graph's NodeRef predicate or establish its subscriptions. [Native traces and seven LuaJIT controls](verification.json), [CET lookup API](https://wiki.redmodding.org/cyber-engine-tweaks/patch-notes)

## Manual check

1. Load **AutoSave-14, 6 November at 11:27:43 AM**, from the same genuine post-Tower playthrough. Keep the existing autosave as the reference and play on a disposable branch.
2. Approach the closed stash door. Keep the keypad untouched, get out of any vehicle, holster your weapon and let ordinary gameplay run for ten seconds with menus and CET closed.
3. Open CET and paste the entire single-line [VT01 command](CHECK.command.txt). Report the three lines beginning with `[VT01]`.
4. If it reports `Permit=1`, an attached closed door and `Entered=0`, let ordinary gameplay run for another five seconds and run the same command once. Leave the keypad untouched until the second sample.

| Result | Interpretation |
| --- | --- |
| Entered 1 while the door remains closed | The wrapper issued on this fixture. Continue with the normal keypad and record the actual rewards. |
| Permit 0 | Script permission remains the first observed blocker. The S23 line supplies the current journal match and safety result. |
| Permit 1, attached closed door, Issued 0 in both samples | The exact physical door and script permission are present together. Investigate the native load/alias and restored condition subscription before choosing a patch. |
| Door unresolved, detached, controller unavailable or error | Keep that lookup result explicit. It cannot substitute for a closed-door sample. |
| Issued 1 with Fault 1 and Entered 0 | The late recheck failed after the one-shot claim. Preserve the state and separate this case from a node 2 admission stall. |

No gameplay successor was staged. The full Rook, money and shard route remains inside the unmodified original body. The repair decision still depends on the closed-door sample, so there is no package to install for VT01.

The source bindings, exact pre-open save, installed dependencies, command syntax, distinct outcomes and full-width EntityID were checked offline. The command made zero game API calls in the offline controls. From the workspace root, rerun in a fresh investigation copy with the same pinned inputs and an unused output file.

```powershell
& 'C:/Users/Ayong/.local/bin/python3.14.exe' -X utf8 -B prealpha/voodoo_entry_20261106_01/verify_probe.py
```
