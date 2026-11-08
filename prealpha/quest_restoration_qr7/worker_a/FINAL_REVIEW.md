# Independent QR7 final artifact review

**Artifact result: PASS**, frozen source epoch QR7:04. This is a static/package result, not gameplay success or deployment approval.

`final_package_02/verification/evidence.json` records 1,738 independent checks:

- All 1,577 archive members were freshly extracted and compared to the complete canonical source inventory, with no missing, extra or colliding keys.
- Exactly six existing payloads changed and three were added relative to QR6; the other 1,568 prior payloads remain byte-identical.
- All nine changed/new final member graphs, nodes, sockets, connections and metadata equal their independently approved source-proposal trees.
- Eight inherited corrective resources retain exact bytes. Spy's inherited Mark/Ana work retains all original graphs, node payloads, sockets and phone routes; the only new route is the reviewed root/50 future-Armed splice. The comparison uses a fresh actual QR6 binary readback in `spy_baseline_readback_01/`, because the historical B JSON omitted nested graph root/50/1302.
- The package and ZIP contain exactly 51 unique file paths. Every ZIP member passes independent CRC, SHA256 and size comparison to the canonical package. Only the consolidated archive and XL differ from the QR6 package.
- The XL retains every prior registration and block in its original order. The new owner19913 and its block are appended; no old generated ID changes.

Archive SHA256: `CE7A3777EA9A7FBEE10F2AA90807D5F1727E502B349942EC6F2FA32BB7E7373F`.

ZIP SHA256: `7F2DD92C540272D2C03A8744C0665EAD0E38277D29CD2C71E587A2CE6533E34F`.

The independent runner is `run_final_independent.ps1`. Supply `source_epoch_04.json`, `approved_changes_03.json`, `candidate_01/package_manifest.json` and a fresh private Worker A output directory. Its preserved expected map derives accepted bytes from the source proposals, not the coordinator checker's verdict.

## Registration engine boundary

`restore_current_release_01/evidence.json` distinguishes the current installed ArchiveXL1.28.0 DLL (`C07DA66D…`) from the older PR63 build. The installation receipt and observed product version match the current release. Its [official versioned source](https://raw.githubusercontent.com/psiberx/cp2077-archive-xl/v1.28.0/src/App/Extensions/QuestPhase/Extension.cpp) starts a registered root phase at In1 on restore when its engine receipt is absent, then records that receipt; ordinary quest start also records it.

The actual parent/input/socket and generated ID are structurally correct. Exact installed-DLL method/address/PDB or reproducible-build instruction identity remains **UNKNOWN**. No old PR63 source is presented as current binary authority. Live restore scheduling, private marker acquisition/release, interruption and supported save transitions remain **LIVE_ONLY**. Future-only arming bounds a new waiting private owner; the registration does not justify restarting a historical native owner.

No candidate, package, installed file, save, fact or release was modified by Worker A.
