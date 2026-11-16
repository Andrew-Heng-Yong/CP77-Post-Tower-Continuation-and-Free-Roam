# RD1 shared resume dispatcher and first earned-stage entries

Candidate **04** is now installed as **RD1_EARNED_STAGE_RESUME**, following the user’s installation request. [Installed manifest and preservation report](deployment_01/REPORT.md). It passes the bounded offline checks; gameplay verification is pending. This implements the shared decision foundation and two reviewed stage entries, with global-latest snapshot selection retained; it does not establish arbitrary-moment resumption for every quest.

Selected evidence: [qualified candidate manifest](candidate_04/qualified_manifest.json), [354-check assessment](verification_03/assessment.json), [148-source compilation](compile_02/result.json), [archive readback](archive_04/readback.json), [registration inventory](candidate_04/registration_inventory.json), [additional provider checks](candidate_04/additional_providers.json). The [composition manifest](candidate_04/manifest.json) retains its original pending status; the later assessment and [checkpoint](checkpoint.json) select the qualified candidate without rewriting earlier evidence.

## Changes

The shared dispatcher distinguishes preserved terminal history, existing private ownership, positively proven original ownership, fresh entry, earned-stage entry and defer. Production does not enable native-owner preservation: HP1/HP2 did not qualify that lifecycle. Historical observations use stable primitive access to the existing snapshot rows, avoiding the temporary-row access associated with the earlier crash. Snapshot selection remains global latest.

Existing adapters share the history eligibility predicate and retain their narrower guards. Full earned-stage decisions currently apply to these two entries. Extending the same system to more stages still requires generated stage contracts and owner/support/reward review; a registry entry alone does not supply that review.

| Quest | Candidate behavior | Preserved behavior |
| --- | --- | --- |
| Machine Gun — Deliver Skippy | A new private entry requires the captured earned delivery stage, matching live choices, non-regressing kill counters, one existing Skippy and no previous controller receipt. It waits for genuine SC1/SC3 stop acknowledgement or a fenced, never-claimed owner. | Native delivery, Regina callbacks, item removal, reward and cleanup nodes; original choices/counters; reviewed five-day reacquisition follow-up and its existing shared receipt. |
| Moving Heat — first door | The current S22 controller gains a historical Active-stage admission branch. Root/phase/first-door journal states may reflect Tower interruption; later objectives and native progress must still match. | Existing controller/node identities, complete continuation body, q305-or-q306 entitlement, exterior safety checks and the scoped car-retrieval support wrapper. The original guard remains the first branch. |
| The Highwayman — inactive control | No new route or source changes. | S28 script, private resources, native conditions and installed Johnny edits remain byte-identical. |

Skippy's new entry bypasses the owner-reveal route and the test input that grants another gun. All original body node parameters and nested graph edges remain intact except the two earned-entry connections. Delivery starts from the outputs already earned after owner reveal. Genuine delivery outcomes still use native nodes; the adapter does not award a reward or force completion at admission. The new boot activates the earned quest/phase as needed, then native delivery nodes restore the earned objective. It does not perform a blanket Failed-to-Active conversion.

The prior Skippy adapter remains unchanged for its existing saved owners. Its earlier-stage predicates expected owner-known zero and specific counters. Readback also exposed an intermediate wait still carrying those predicates in the first RD1 archive; archive 04 updates every admission boundary. Candidate 03 is retained as a rejected example and must not be installed.

## Exact scope and validation

The 51-path package changes five files: the combined archive, its XL, HistorySnapshotHS1, SideJobsS22 and SideJobsS23. All 26 required dependencies remain at the installed baseline. Archive 04 contains 1,742 members: 1,739 unchanged predecessors, one changed Moving Heat boot and two new Skippy resources. Every packed member was extracted and hashed. Native Tower resources, capture gates, Johnny corrections and all old S23 owners remain unchanged.

The new registered depot is `towercontinued\resume_rd1\mq007_delivery_boot.questphase`, generated phase ID **8694**. Its depot keys were checked against current archive providers. The ID was independently calculated and compared with native EP1 root nodes and every installed addition targeting that parent. Old XL bytes and registration order are preserved. Other-parent registrations are recorded without applying the EP1-root ID formula to them.

All 148 registered REDscript sources compile offline with the exact installed compiler, dependencies and cache inputs. Candidate 04's three changed scripts match those compiled in candidate 02. Persistent field declarations are unchanged. The new coordinator's transient epoch discards stale scheduled ticks; native graphs own durable Issued/Entered/Finished receipts.

The 354 checks combine source identity, serialized graph diffs, package/provider checks and bounded state-contract fixtures. They are not 354 gameplay tests. The admission replay consumes serialized native conditions and follows the whole boot path. It catches intermediate gates, verifies one owner claim, and rejects a second admission, changed objectives/facts, missing or duplicate Skippy, altered choices, regressed counters, pending ambient stop and absent Moving Heat entitlement. Dispatcher cases preserve completed/failed history and existing owners and defer unsupported/unknown states.

The positive fixture combines the exact good HS1 snapshot (revision 151, `C1CFCBB5…BD26BE`) with saved journal/fact observations from the historical AutoSave-5 (`2971FA17…0DC01`). An additional read-only projection confirms `q305_done=1`, `q001_done=1`, `q005_done=1` and `q101_enable_side_content=1`; q306_done is absent. Inventory quantity, objective-counter continuity, settled journal, safe exterior, completed private startup and the 100 ms boot delay are explicit test doubles. No AutoSave-5 command test, game launch or save write occurred.

## Remaining qualification

Native scene/callback scheduling, actor/support streaming, actual rewards, interruption and save/reload behavior remain unverified in gameplay. The original-handler preservation branch stays unavailable. This implementation does not preserve a partially elapsed native timer or claim every quest stage is supported.

The reused Skippy reacquisition placement references the reviewed native persistent exterior variant. WolvenKit 9.1 cannot fully decode its sector placement; this candidate preserves that exact reference and does not claim a complete placement audit. Moving Heat retains the installed approved Johnny presentation edits and existing native journal notification/tracking behavior. No additional restoration of arbitrary phone, optional or tracked metadata is claimed.

Global-latest selection is the user's requested policy, not evidence that the history came from the loaded run. These two contracts cross-check their reviewed live stage/choices/counters; unmodeled history is not certified. Existing earlier adapters are retained, not requalified for all saves by this work.

The separately authorized installation passed the closed-game deployment gate, current baseline hashes, recovery fixtures, save/external-mod preservation and rollback readiness specified by [prealpha/AGENTS.md](../AGENTS.md). It changed five verified Core files and preserved 355 save files. The next gameplay route is [AutoSave-2 through genuine Tower completion](TEST_CARD.md); the successful snapshot-loader test is not repeated as a separate task.

## Reproduction and retained attempts

The scripts are workspace-only builders with fresh-output guards. `prepare.py --attempt N` pins the current installation; `generate_contracts.py --out analysis_NN` generates contract data/readers; `build_scripts.py --attempt N` stages script changes; `compile_candidate.py --candidate candidate_NN --out compile_NN` compiles an exact source inventory offline. Their selected input directories are explicit in source; changing them requires a successor review, not rerunning over pinned outputs.

`build_native.ps1 -Attempt N` binds the complete donor to installed payload bytes, constructs the private successor, checks providers, packs and fully reads it back. `-ValidateTypesOnly` exercises native journal condition construction without creating outputs. `compose_candidate.py --out candidate_NN` preserves the script-only candidate and assembles a fresh complete package. `check_additional_providers.ps1` and `qualify.py --out verification_NN` bind the remaining native sources and perform bounded qualification. `read_fixture_prerequisites.ps1` reads only the already-pinned historical save and writes a small projection inside this workspace. None is an installer.

Retained failures: preparation 01 missed a Python import; archive 01 hit a null phase handle; archive 02 hit a typed integer assignment; archive 03/candidate 03 exposed the stale intermediate Skippy wait. Verification 01 needed the correct native `Out1` hub semantics in the offline evaluator; verification 02 exposed prerequisite fields absent from the earlier bounded save projection. Those fields were subsequently read from the exact pinned save. Selected outputs are inputs/base 02, contracts 03, scripts/compile 02, native archive 04, candidate 04 and verification 03.
