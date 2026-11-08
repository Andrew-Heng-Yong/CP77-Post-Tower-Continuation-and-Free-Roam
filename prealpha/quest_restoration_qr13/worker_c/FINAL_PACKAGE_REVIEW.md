# Independent final QR13:02 package review

**PASS for the frozen static package and preservation gates.** No runtime, candidate, install or save files were written by this reviewer. This is not gameplay certification or deployment authorization.

The independent inputs are pinned in `final_package_01/expected/inputs.json` (SHA256 `883D63FCF6D45DB960D24BED503D35C4D3282D097054BB20F7CFADA757CCB170`). Expected payloads were reconstructed from the QR13 baseline plus independently approved actual Ronald and Brendan serialized donors, rather than accepted from the new package manifest alone.

`extract_final_archive.ps1` used ArchiveReader to extract every actual final archive member into worker C. `verify_final_package.py` then performed 2,390 checks. Evidence:

- `final_package_01/verification/review.json`: final result and exact frozen identities.
- `final_package_01/verification/checks.json`: individual assertions.
- `final_package_01/verification/payload_hashes.json`: all 1,577 actual extracted payload hashes.
- `final_package_01/verification/zip_members.json`: all 51 ZIP member hashes, sizes and CRCs.
- `final_package_01/extracted/manifest.json`: ArchiveReader extraction and changed-resource typed readbacks.

## Verified artifact

| Item | Result |
| --- | --- |
| Source epoch | QR13:02; SHA256 `A2EABC90B9A30E831703B1121BCD350D1AEA6C07C3453C696BBB5A0D56AED5F6` |
| Consolidated archive | SHA256 `97D3C65BB72F4BA4F3BCB6AECDE9ABA105315D0340918F42590363F9F90A32BF` |
| Staged ZIP | SHA256 `B2BDC04BE7CF202047C3E7CF85F9BB3BD8F0D77B9D98ACA7C1377F5E5AD52EB8` |
| Archive members | All 1,577 independently extracted and hashed; same depot/FNV keys; no additions, omissions or duplicate keys |
| Package / ZIP | Exact existing 51-file inventory; all members match package bytes, sizes and CRCs; no extras, duplicate names or unsafe paths |
| Unchanged package files | 48 of 51; archive plus exactly two reviewed REDS files differ |
| ArchiveXL | Entire file unchanged: `F22693981B0A10DB21B47AFAD7FC8BCAEF1F021D9EA99548BA4FF80F56D18245`; registration order and generated phase registrations preserved |
| Fresh compile evidence | PASS; all 134 current input pins and 131 staged sources checked; all 46 managed candidate REDS files included exactly once |
| Compiled output | SHA256 `735867A43C70E7B41F23974556C1ED5BAB4621FC6573782C1B18A8F891D137BB`; successful compiler log and exit 0 verified |
| Preservation | 60 installed Core/diagnostic/dependency hashes and all 310 save-file hashes unchanged; entire game/save and QR3–QR12 file metadata inventories unchanged |

The only changed resource depots are:

1. `towercontinued\b0_story_eight\ronald.scene` — `90B8BEEC799284011626F514834E5A888BECD24138E50246880CFE4E66475A26`.
2. `towercontinued\b0_story_eight\ronald.questphase` — `BEF87E480015E83494CB04668F4959CFD899F86E86B73654999DC0FA1D32EB2C`.
3. `towercontinued\sidejobs_s23\base_b\mq037.questphase` — `CB73F639835F8835C36BCFEDC90D16DAE31CAF4D9DCC603D58C86A8E159CE1D6`.

Each actual final member deserialized without structural errors and matched its full independently approved model, including metadata. The MQ037 inherited repair is an explicitly reviewed semantic successor; the other eight listed inherited corrective donors remain exact. All other 1,574 QR8 payload bytes remain exact. Prior CR1/PH1/PH2/PH3 controls were reused only on preserved inputs; no historical builder or full audit was rerun.

The only changed scripts are `PTFR_HistorySnapshotHS1.reds` (`ED9B0EFD0A2914E66CB5FDFA23F7A6E28179872504C6D4E2AA4F5E0C184DB445`) and `PTFR_SideJobsS23.reds` (`F29ECBA24DA9507ADD0365BA95A205406C4A4412CDDD164C12FBB7326C64BE97`). Their approval is the final A06 component review, which reaffirms these exact bytes. The earlier A03 script-specific approval is separately pinned; its blocked resource03 was never treated as approved.

## Boundaries retained

- Ronald's exact native bar lease, new consent receipt, contact prefix and terminating join are source/serialized-model approved. Already-saved child ownership acquiring new prefabs or graph edges remains LIVE_ONLY. No retrospective enrollment or pending-timer adoption is certified.
- Brendan remains conditional on the narrow genuine pre-ending earned-final-Theo history and existing guards. The exact native prefab borrowing, release acknowledgment, old-owner route, native body and official injector preservation are approved by A06. The machine-spot sector still fails WolvenKit's DynamicBaseClass/worldNode decoder. Its decoded placement and complete internal content were not verified; the exact native reference is accepted under the documented ownership/scope exception, not described as decoded or free of autonomous content.
- No new source evidence justifies widening Skippy admission. User-reported completion remains accepted without a repeat test or inference that every saved stage works.
- No executing-owner, native callback, save-transition, gameplay, all-save or future-version PASS is claimed. No genuine newly eligible runtime fixture was manufactured. Installed QR8 Core and the validated sampler remain untouched.

The frozen artifact is ready for the coordinator's staged-successor documentation and future deployment preflight. Installation and new human-driven runtime observations are separate actions.
