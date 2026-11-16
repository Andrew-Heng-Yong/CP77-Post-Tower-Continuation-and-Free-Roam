# HS3 capture observation — 12 November 2026

The new direct-Tower snapshot exists and its complete JSON matches the generated
catalogue. The game log records save-local commit before native cleanup at
**2:39:20 p.m. Toronto time**. The schema-3 file was created at **2:39:31 p.m.**

- File: `snapshot_hs3_20261112T193931Z_1_3.json`; SHA-256 `C27598B50A97F3B7D3DD4905CEF1EB8C0F8FB67DF2865933E022B58D5D13D8F0`.
- Origin `pre_native_cleanup`, route 1, ticket 1, revision 1.
- All 24,753 definitions match exactly: 4,982 journal references, 18,685 facts,
  and 1,086 item quantities. All row field types and repeated file hashes pass.
- 24,750 rows are stable. Three changing phone facts (`holo_setup_active`,
  `holo_setup_started`, `holo_v_calls_reed_start`) are explicitly unstable.
- 129 missing journal states and 12 unavailable item records remain unknown.
  Stable does not turn an unknown observation into usable stage evidence.
- Machine Gun and Deliver Skippy are Active (state 2); its total counter is 97.
  Moving Heat and Beat on the Brat roots are also Active in the extended export.
- The sampled pre-cleanup guard facts retain q307 PONR=1, 2079=0 and both native
  killed receipts=0.
- The associated newer HS1 export is revision 151, with all 158 rows stable.
  The earlier revision 150 file remains preserved and has one unstable row.

The log excerpt shows the HS1 export acknowledgement. The current scripting log
ends mid-line before an HS3 acknowledgement line is available; this observation
independently validates the completed HS3 file and the simulation commit log,
rather than claiming to have observed that final in-game export acknowledgement.

**Capture and exported-content validation passed. The full persistence test is
not yet complete.** No post-capture hospital/end/reloaded save has been bound to
this certificate and verified. The most recently visible save metadata predates
this new capture; its after-credits label belongs to an earlier run. Do not use
that old ending save as evidence for this HS3 run. Native timing across other
routes, save serialization and resumed quest owners remain separate concerns.

Source files were read only; no game command, launch, save write or mod change
was performed. Exact source hashes and bounded log excerpts are in
`assessment.json`. The prior successful revision-159 run remains historical
evidence and is not substituted for this new player-local capture.
