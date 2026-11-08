# Building and validating the consolidated mod

## B1 — Establish the source lineage

**Status:** current baseline points to PH3; full rebuild from all generic source folders is not established.

**Prerequisites:** [current-state](current-state.md), current candidate manifest, matching installed/package hashes and an authorized successor task.

Read the selected `prealpha/phone_studios_ph3/candidate_01/install_manifest_01.json`, `installed_assessment_01.json`, `build_01.json`, and `verification_01.json`. Its `archive_source/` is the complete 1,574-member snapshot. Generic `archive/source`, old `redscript/` component folders and the prepared VD1 beta are not drop-in sources for rebuilding PH3.

**Procedure:** create a fresh successor directory, copy the current complete source/package, make only reviewed replacements/additions, and record the predecessor and exact resource delta. PH3's builder is an example of an additive successor; PH1 is an example with four reviewed old-resource edits. Do not rerun either pinned historical builder. Initial consolidation's 25→1 archive merge is historical, not the current census.

**Expected output:** complete staged source/package and a change manifest. **Verify:** no corrective donor is lost while merging. CR1 exists because the first consolidation discarded 30 corrective resources. File order or “latest folder” is not semantic winner selection. Preserve each corrective donor unless its explicit reviewed successor changes it.

## B2 — Pack and fully read back

**Status:** working API recorded by PH3 and earlier successors. A fresh build still requires fresh input verification.

**Prerequisites:** V1 helper initialization, complete private source directory, fresh archive output, expected resource manifest and exact intended override list.

The existing pack call is:

```powershell
$hashService = [WolvenKit.Common.Services.HashService]::new()
$hashService.Load()
$stream = [IO.File]::Create($archiveOutput)
try {
  $writer = [WolvenKit.RED4.Archive.IO.ArchiveWriter]::new(
    $hashService, [WolvenKit.SerilogWrapper]::new())
  if (-not $writer.WriteArchive([IO.DirectoryInfo]::new($sourceDirectory), $stream)) {
    throw 'Archive packing failed'
  }
} finally { $stream.Dispose() }
```

Variables must refer to the new staged outputs. Source: `prealpha/phone_studios_ph3/build_01.ps1`; validation source: `verify_01.ps1`.

**Expected outputs:** `package/archive/pc/mod/zzzz_PTFR_Combined.archive`, its XL, and independent verification JSON. Reopen with `ArchiveReader`, extract **every** member and SHA256 it. Compare exact member inventory, every retained payload, approved changed resources, new source bytes and unexpected deletions. Check new depot keys against all current archives. Archive-level hash/count alone is insufficient.

PH3's recorded result is 1,573 old payloads unchanged plus one new owner. This count must change explicitly for a new successor. There is no new REDscript compile requirement for unchanged source bytes, but changed REDscript requires the complete-input process in [the toolchain guide](redscript-toolchain.md).

## B3 — Validate ArchiveXL registrations separately

**Status:** recorded PH2/PH3 regression checks; this gate is mandatory for new or renamed injections.

**Prerequisites:** native parent graph IDs, every current installed XL addition targeting that parent, candidate additions, exact node/input/socket and archive paths. Parse all relevant entries, including external mods; fail/report unsupported YAML shapes rather than silently skipping them.

For the current `ep1\quest\ep1.quest` node `[1]` injections, ArchiveXL's key is `path + ':1'`; ID is CRC-CCITT-FALSE (initial 65535, polynomial 0x1021). Verified independent implementations are in `tools/shark_b7_2_helpers.ps1` (`B72Id`, `B72IdIndependent`) and PH2/PH3 Python scripts. The older B72 inventory/parser can reject some current non-quest/empty XL files; PH2/PH3's bounded parser was used for their standard layouts. Do not advertise it as a universal YAML parser.

**Procedure:** adapt `prealpha/phone_studios_ph3/semantic_01.py` registration inventory into the new task, verify every generated ID against native nodes and all additions, and preserve old bindings/order. Only use the `:1` formula for the input shape it was derived for; inspect ArchiveXL source for other node paths.

**Expected output:** complete ID inventory and collision regression report. **Verify:** both depot uniqueness and registration-ID uniqueness. PH1 Mark path generated ID **40560**, colliding with an existing Watson map phase despite no depot collision. PH2's byte-identical alias uses **61197**; PH3 studio owner uses **22195**. Do not rename or move saved/registered paths casually to obtain a new ID.

## B4 — Runtime merge evidence

**Status:** log verification, distinct from static build success.

When a separately authorized user gameplay run supplies logs, snapshot `GAME/red4ext/plugins/ArchiveXL/ArchiveXL.log`, then search for the exact candidate paths and `Can't merge phase` warnings. Example read-only command against a copied log:

```powershell
rg -n "Can't merge phase|phone_studios_ph3|phone_merge_ph2" $copiedArchiveXLLog
```

**Expected output/checks:** each intended merge, no duplicate-ID refusal, correct run timestamps. A successful merge is not listener admission, rendered studio, call completion or save-reload proof. Do not launch the game simply to fill a documentation report.
