# ArchiveXL integration assessment — QR8 Worker A

Status: bounded static evidence ready for independent peer review. The old QR7
exact-DLL/source correspondence gap can be closed only after that review; live
dispatch, serialization and streaming observations remain separate.

Installed ArchiveXL.dll is 1,958,912 bytes, SHA256
`C07DA66DF4E4D57401FA3DF0F6288F3B780F01102A98807B6ADAABAEF45F69BF`,
FileVersion `1.28.0.2610250100`, ProductVersion `1.28.0`. Actual CodeView record:
GUID `713A7EC9-1DDA-4BC8-B59B-15478CB129D9`, age 8. No matching PDB is available;
the developer PDB pathname is identity evidence, not symbols. The old PR63 package
is not this binary. Exact official v1.28.0 source files were captured separately
under `source_v1_28_0/` with source SHA pins in the binary evidence.

The unique QuestPhase GetName function and neighboring virtual Load pointer lead
to actual hook installation instructions. The restore hook resolves address ID
`0x7A20106E`, uses wrapper RVA `0xF4E80`, and stores callback `0xF5A10` in the same
slot the wrapper calls before the original trampoline. Matching preload/root-start
routes use `0x2F1F26CC`/`0x2F8E2179` and callbacks `0xF5F40`/`0xF6160`. These are
instruction/dataflow observations, not a version-based inference.

The restore callback searches the actual parent quest path in the saved quest
list (+0xA8, length +0xB4), derives the root-index path hash, creates a missing
node-hash-map entry (+0x78), and derives the receipt from that hash and the
generated phase ID. FactManager is read at +0xF8. Its actual GetFact call uses
store 1 and virtual slot 0x10; a nonzero result branches over startup. The zero
route builds one literal In1 socket, dispatches QuestsSystem virtual slot 0x240,
then calls SetFact slot 0x18/store 1/value 1 for the same receipt. Normal-root
start derives the same receipt and writes it without a ForceStart dispatch.
This is the bounded released-source mechanism implemented by the installed DLL.
It does not restart a historical native owner; QR7's separate future-only owner
guards still determine supported acquisition.

The actual streaming PostConfigure method, RVA `0x130A00`, routes each configured
block path through RegisterPatch (`0x122630` then `0x122440`) for main-world hash
`0x611101B4BB2A5E9C`. Resource-ready RTTI dispatch `0x120430` selects the world
merge `0x120BB0`, which obtains the typed block token and appends path/token refs
to blockRefs. Private descriptor acquisition/release remains a native engine
behavior; a successful block merge is not proof of the quest-scoped marker lease.

`binary_verification_01/` has 91 installed-instruction assertions and six actual
byte mutations that are rejected for their changed behavior: receipt bypass,
wrong callback, wrong ForceStart slot, zero receipt write, In2 socket and wrong
main-world target. `identifier_algebra_01/` independently checks the optimized
CRC against binascii on all 826 observed target-root keys and proves distinct
uint16 IDs yield distinct same-parent receipt hashes. It does not claim a full
native named-fact hash census or actual saved receipt values.

The fresh namespace check expands QR7's historical bounded archive/pc inventory:
185 indexes including the staged candidate, 76 XL files including ArchiveXL
Bundle scopes and ModSettings, 1,728 parsed phase additions, no unsupported YAML
shapes skipped. Effective EP1 root additions are 826. New ID 19913 is unique
and clear of native IDs 0/1/2/12/27. The full staged XL tree equals the previous
tree plus only the reviewed owner and block appends; all old order is retained.
All three new depot hashes occur only in the staged QR7 archive, and fresh
extracted bytes equal canonical source. They are absent from the unchanged
installation. The expanded archive inventory includes inactive storage as a
conservative collision superset; it is not a claim those archives execute.

No runtime defect or repair is established by this integration investigation.
No QR7 candidate, package, installed file, save or fact was modified. Do not create
a replacement ZIP from these diagnostic artifacts.

Remaining limits are exact: successful runtime address resolution and hook
installation, native virtual dispatch effects, save receipt serialization/reload,
private owner/descriptor acquisition and release, and arbitrary external world
global or different-parent/named-fact hash collisions. The first group needs
controlled live observation; no binary/source mismatch was found on the inspected
integration path. The namespace limits are disclosed bounded scopes, not hidden
full-world proofs. `DIAGNOSTIC.md` specifies minimal future observations without
installing or activating instrumentation now.

Reproduce the byte checks into a fresh private directory:

```powershell
& 'C:\Users\Ayong\.local\bin\python3.14.exe' -X utf8 -B prealpha/quest_restoration_qr8/worker_a/recheck_binary.py --output prealpha/quest_restoration_qr8/worker_a/replay_FRESH
```

Expected: 91 assertions and six rejected mutants in `result.json`, current DLL
SHA and stable size/mtime, exact checker pins. Stop if the binary differs; don't
transfer RVA claims across versions. A new targeted provider capture is available
through `capture_namespace.ps1 -Output <fresh worker_a subdirectory>`. The full
frozen assessment inputs/results are indexed by `evidence_index.json`.
