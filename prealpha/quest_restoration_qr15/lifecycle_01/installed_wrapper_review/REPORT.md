# Installed Codeware population-spawner flags — independent binary review

**The installed DLL does not have the proposed +0x08/+0x09 flag defect.** Its RTTI-bound `PopulationSpawnerWrapper.IsActive` reads native spawner `+0x10`; `IsInitialized` reads `+0x11`. Those offsets match the exact installed game's registry-returned spawner layout. The local research header is stale at those two fields; it cannot be substituted for the installed binary.

The installed file is `red4ext/plugins/Codeware/Codeware.dll`, 1,944,064 bytes, SHA256 **808D8BCE11641073091DDA33830D06AB98BD9AC710A9A47ECD7EC56E6193440C**, image base `0x180000000`. It matches its exact entry in QR15 `baseline.json` (77 installed pins). Only this DLL pin was freshly checked here; this review does not claim a new all77 scan. All addresses below are DLL RVAs unless explicitly marked game EXE.

## Binary binding, independent of source annotations

1. Class descriptor path `0xE1CD0` loads `0x9E16D17C1829E805` and resolves that class, then calls method registration `0xE16E0` at `0xE1D81`. Independently calculated FNV1a64 of **PopulationSpawnerWrapper** is exactly this value; Codeware's local CName implementation documents the FNV1a64 name codec. The installed REDscript file independently declares this native class and both method names.
2. At `0xE1726`, registration supplies callback `0xE1360` in R9, with both method-name parameters pointing to the installed **IsActive** string at `0x172E20`, and calls registration helper `0x36080` at `0xE173E`. The next method supplies callback `0xE1390` at `0xE1778`, both names **IsInitialized** at `0x1769D0`, and calls the same helper at `0xE1790`. This excludes the separate IsActive registration for another wrapper at `0xBF000`.
3. Complete leaf spans, including the non-null branches past their first RET, are retained in `installed_04.json`. They perform:

```text
IsActive callback E1360:
    spawner = [wrapper + 40]
    if spawner == null: result = 0
    else E1379: movzx eax, byte ptr [spawner + 10]
    write byte result

IsInitialized callback E1390:
    spawner = [wrapper + 40]
    if spawner == null: result = 0
    else E13A9: movzx eax, byte ptr [spawner + 11]
    write byte result
```

The callbacks advance the script frame and clear its temporary flag. They do not activate/reset a spawner or write its native flags. They do not read spawner `+8/+9`.

## The pointer passed to those callbacks

The installed **GetPopulationSpawner** registration at `0xF17F0` supplies callback `0xEF690` (`0xF1A9E`), using the exact method-name string at `0x177368`. Its return type builder `0xF0860` reconstructs **handle:PopulationSpawnerWrapper** from two installed 16-byte constant blocks. The callback calls `0xF1290`, which calls getter implementation `0xF27D0`.

That implementation checks the community-system pointer at its receiver `+0x68`, resolves the NodeRef, calls native community virtual `+0x260` at `0xF2855`, locks the returned weak pointer, and constructs the wrapper with `0xE13C0` at `0xF29FB`. Constructor `0xE13C0` copies the unchanged pointer/control pair into wrapper `+0x40/+0x48` (`0xE13EE..E13F9`). No pointer adjustment is inserted before the two flag reads.

The separately sealed native pointer evidence is `../community_native/capture_01.json`, SHA256 **A2805CC1E047115D2D2D7188E5001E6713392D82B54CB017E4B5600E6C15E343**, game EXE SHA256 **D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4**. Critical selected bytes were independently rechecked here; its complete native proof is reused, not relabelled as a new lifecycle audit:

- Actual gameCommunitySystem instance vtable `0x30D3A18 +0x260` points to `0x38360C`, whose lookup is `0x383660`.
- The allocated spawner pointer is the registry pointer, without an eight-byte base adjustment. Native constructor `0x384470` stores the ID at `+8` (`0x384480`) and zeroes the two flag bytes at `+0x10` (`0x38449B`).
- Ordinary activation `0x9CEFB8` tests initialized `+0x11`, tests active `+0x10`, and writes active `+0x10 = 1` before its virtual callback. These are exactly the bytes read by the installed DLL callbacks.

## Existing PDBs do not match

Installed DLL CodeView RSDS identity at `0x19F770` is GUID **3EC6A6A7-5BA2-4EA5-AD63-477E26DD0262**, age **27**. Its embedded PDB path `D:\Sandbox\Cyberpunk\Extenders\Codeware\Project\build\windows\x64\release\Codeware.pdb` does not exist here.

A workspace filename search found two existing Codeware PDBs. Their MSF7 directory and PDB stream1 were read directly; neither can supply names for this installed image:

| Existing file | GUID | Age | Matches installed |
| --- | --- | --- | --- |
| `build/windows/x64/release/Codeware.pdb` | `9F441D98-5B55-43F7-94FE-B330703FFE63` | 1 | No |
| `build/windows/x64/release/compile.Codeware.pdb` | `0D7E3AB9-1E05-4C11-AAAD-0F0E59BD83D5` | 3 | No |

Exact PDB hashes and search scope are retained in `pdb_identity_01.json`. No symbols were downloaded. The result uses installed RTTI registration, method callbacks and pointer-copy bodies rather than those mismatched symbols or a guessed local build identity.

## Decision and observation limits

The **installed bool-getter ABI defect is rejected**. No framework source edit, correction candidate, compile or installation is justified by the local +8/+9 declaration. A future framework rebuild would need to resolve that stale declaration against its chosen engine version; the installed binary is not proven to have been built from the current research checkout.

The current JF02 result obtained no wrapper, so neither flag callback ran. There is no observed false flag value to correct retrospectively. The installed getter's ordinary null guards corroborate the three source boundaries—missing community system, zero resolved reference, or no lockable registry object—but no evidence identifies which boundary executed on the human's live session. This review does not change JF02 UNKNOWN into absent/inactive and does not authorize a spawner action.

The prior 25-check native prefab result is reused without repetition. It remains separate: native ticket release, queued world-streaming changes and retained NodeRef index do not certify population/spawner/persistent-state retirement. This binary review closes only the disputed wrapper flag layout and its returned-pointer binding.

## Validation

`inspect_installed.py` reads PE sections, CodeView data, `.pdata` functions, exact leaf spans and bounded references from the installed file. `read_pdb_identity.py` reads existing PDB identity streams and the current77 DLL pin. `verify_review.py` independently rechecks the retained instruction bytes, registration targets, class-name codec, unchanged pointer constructor, native layout anchors and both PDB mismatch controls. Results are in `verification_01.json`; sources/artifacts are pinned by `manifest_01.json`.

No DLL was loaded into a process. No game/framework callback, debugger, save reader/writer, compiler, installer or network download was used. All writes are fresh evidence in this directory.
