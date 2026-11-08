# QR5 — source verification and staged repair report

Completed **64 new deep investigations**, bringing the total to **128/161**. Primary coverage: 48/48; stretch: 16/16. 33 selected quests remain for the next session.

Every new quest has ten source-specific dispositions and independent actual-resource review. **0 quests have all ten contracts statically resolved**. Deep reviewed does not mean fully restored or proven playable.

## Confirmed defects and dispositions

7 new unique defects affecting 10 quests: 5 repaired in staged resources; 2 explicitly blocked. Prior QR3/QR4 corrections remain preserved.

| Defect | Affected quest | Disposition |
| --- | --- | --- |
| QR5-G04-ARR12-MISSING-FUTURE-FAILURE-MONITOR | sts_std_arr_12 | REPAIRED FUTURE ONLY SERIALIZED AND PACKAGE STATIC VERIFIED LIVE PENDING |
| QR5-CHEETAH-FUTURE-FALLBACK-MONITOR | sts_wat_nid_03 | REPAIRED FUTURE ONLY SERIALIZED AND PACKAGE STATIC VERIFIED LIVE PENDING |
| QR5-NID02-FUTURE-VAN-FAILURE-MONITOR | sts_wat_nid_02 | REPAIRED FUTURE ONLY SERIALIZED AND PACKAGE STATIC VERIFIED LIVE PENDING |
| QR5-STEVEN-U9-FUTURE-DEFAULT-OWNER | sts_ep1_08_steven_meeting_night_city | REPAIRED FUTURE ONLY SERIALIZED AND PACKAGE STATIC VERIFIED LIVE PENDING |
| QR5-CVI02-EP1-ALTERNATE-HANDS-CONTROLLER | sts_pac_cvi_02 | CONFIRMED REPAIR BLOCKED EXACT MARKER LEASE AND OWNER EVIDENCE |
| QR5-G18-Q304-S22-MISSING-CAR-PREFAB | q304_car_retrieval | REPAIRED FUTURE 9 EDGE BODY LEASE SERIALIZED AND PACKAGE STATIC VERIFIED LIVE PENDING |
| QR5-RONALD-POST-GIG-NEWS-OWNER | sts_ep1_01, sts_ep1_03, sts_ep1_08, sts_ep1_12 | CONFIRMED REPAIR BLOCKED EXACT BAR MARKER LEASE SHARED QUEUE AND SAVED TIMER SCOPE |

Repair evidence, exact before/after hashes, source proposals, independent reviews and limits are in [the ledger](defects_and_repairs.json), [allowlist](approved_changes_04.json) [primary repair adjudication](adjudications/repairs_01.json) and [MovingHeat adjudication](adjudications/moving_heat_01.json). Original defective resources and frozen findings remain available.

The five packaged QR5 changes restore native ARR12 failure monitoring, Steven’s future U9 actor consumer, Cheetah’s fallback monitor, NID02’s van-failure monitor and MovingHeat’s dedicated accepted-body prefab lease. They preserve native callbacks, joins, journal/reward/cleanup payloads and saved identities. Only future attachment edges gain support; already executing child descendants are unchanged. A claimed MovingHeat owner still pending before9.True can use the new wrapper if its late guards pass.

CVI02’s alternate EP1 Hands calls have real request producers but a retired specialized listener/outcome owner. Its three selected scene inputs are holo-only; metadata containing Johnny/physical Hands is not evidence of a visual failure. Existing FO1 can provide the required default-scene marker under earned conditions, but CVI02 does not prove that lease. Safe independent marker acquisition and saved-owner arbitration remain blocked. See [independent context review](groups/G11/reviews/CVI02_EP1/verification_03/review.json).

A second blocked family affects Ronald’s optional news after Dogtown Saints, Jason Foreman, Spy in the Jungle and Treating Symptoms. Main gig/call/reward proofs remain valid. Native controller11 is retired; B0 restores services but omits news11/12. The native root owns the bar prefab and area-marker lease; SMS children require no physical actor, yet that marker support and shared pause/timer cleanup are not established by B0. Native sent1 precedes the two-game-day delay and cannot prove delivery. No unfiltered bar/controller clone, fake receipt or timer reset is approved. [Four-quest family adjudication](adjudications/ronald_01.json) and [independent context review](groups/G21/reviews/RONALD/verification_05/review.json) retain exact routes and units.

## Validation and source identity

Canonical candidate: `prealpha\quest_restoration_qr5\candidate_03`; epoch `QR5:08`. Package has 51 stable paths and 1574 payloads; 5 payloads differ from QR4. All others, XL registrations and 46 managed REDS files remain identical. Independent readback verifies every packed payload and ZIP member.

- Archive SHA256: `39A12BC8BFCBE8D82AA40F5D39AAF61CECC652BA179014575863A31222D1F402`
- ZIP SHA256: `B04D9AC2430689FBD96ED3D5C6E5AD4B3B349D8DD71B75327113385390333BFF`
- Canonical source epoch SHA256: `B8BC8D6630F51E07125789FAB5A54D188EB45CE7044F35E2E6F09DE460B91D83`

Root repair checks: 324 assertion events and 17 mutations of actual readback documents. Independently implemented serialized checks: 513 assertion events and 30 raw-document mutations. These are fault-detection controls, not unique gameplay coverage. The independent final package review checks all packed keys, bytes, ZIP members, unchanged files, prior repairs, compile-input equality and canonical epoch08 linkage. Metadata-only scope corrections are explicit and do not change package bytes. See [independent package review](groups/G21/reviews/QR5candidate03/verification_01/REPORT.json).

Compilation was reused only after exact equality of 131 source files, 134 compiler/cache input pins and 46 packaged managed sources. No new SCC invocation or unchanged-baseline rebuild was performed. [Compile reuse](compile_reuse_03.json) records the boundary.

The main stock TDB capture is bounded: 1,200 records, 1,197 found, three missing direct targets and 1,469 uncaptured immediate descendants. A separate one-record depth0 supplement resolves the exact native MovingHeat vehicle alias; its child references remain open. These are source definitions, not runtime merged winners or executed rewards. Exact per-quest applicability is in the [shared registry](shared_evidence_registry.json). DynamicBaseClass/worldNode placement and engine scene/lease semantics remain opaque where recorded.

Independent review corrected the outgoing Padre call description, WWD05 Embedded-versus-Soft donor envelope, Cheetah XOR-versus-AND shorthand, Hasan’s timer arithmetic (88 game hours), the flattened-fact false tier-cohort restriction, and inherited source-epoch prose. Originals and failed verifier attempts are retained; source-specific supersessions are indexed in [review issues](review_issues.json), [adjudications](adjudications/) and [group evidence](group_evidence_index.json).

[Coverage JSON](coverage.json), [161-quest matrix](quest_status_matrix.csv), [1,610-contract matrix](contract_status_matrix.csv) and [queue](queue.json) retain FAIL, CONDITIONAL, OPAQUE, UNKNOWN and live-only limitations. The bounded [phone-family census](phone_family_census_02/inventory.json) covers 47 primary evidence schemas plus a separately reviewed Steven case; name matching is not exhaustive semantic or live-owner proof.

## Preservation and remaining limits

Protected-file verification passed for **6585 hashes**. Entire game/save filename, size and modification-time snapshots have no differences. No game launch, deployment, save/fact change, release update or Git publication occurred. PH3 remains installed. [Preservation evidence](protection_after.json).

Native topology, input equality and static reachability do not certify phone scheduling, interruption, timers/reloads, streamed actor/workspot/camera behavior, effective external TDB overrides, rewards or future-version save transitions. Unresolved prior MQ007 saved states, Brendan earned-history admission, Delamain parent evidence and native timing/context discrepancies remain unchanged.

Continue from [HANDOFF.md](HANDOFF.md); do not repeat QR1’s census/compile/reproduction or rebuild the unchanged QR4/PH3 baseline.
