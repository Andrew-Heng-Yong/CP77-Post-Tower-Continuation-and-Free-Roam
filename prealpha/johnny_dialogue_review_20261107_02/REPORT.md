# Five-quest Johnny dialogue review

The user clarified that the review unit is **five quests, with every Johnny line and its context**, without a total line limit. The selected editable document is `output_03/Johnny_review_five_quests_03.txt`, revision **J5-03**. It contains all **49 caller-qualified indexed Johnny dialogue events** in the five selected quest source closures:

| Quest | Johnny events |
| --- | ---: |
| KOLD MIRAGE | 19 |
| Small Man, Big Mouth | 11 |
| The Highwayman | 5 |
| Sweet Dreams | 6 |
| These Boots Are Made for Walkin' | 8 |

Each Johnny event has its own review entry. The document includes three preceding spoken lines from any speaker and the next five V lines where their order can be traced within the scene. Alternatives are separate. Scene entries/ends, independent triggers, repeated-topic limits and uncertain parallel timing are explicit boundaries, with fewer available lines shown. It does not invent conversation order across separately triggered scenes. Preceding and following alternatives are independent source contexts, not a fabricated combined playthrough.

**Any numbered dialogue entry can be marked as a removal selection**, including every Johnny line appearing in context. The user's subsequent instruction is to type `(remove)` immediately after its `[J5-…]` ID and leave the remaining document intact. Only explicitly marked IDs select removals; unmarked or deleted entries do not. One marked copy of a repeated ID selects that exact event once. This instruction supersedes the delete-to-select wording in the issued document; its original bytes and proof remain preserved. The current format is recorded in `review_protocol.json`. Both V wording variants appear together under one ID where they differ. Headings and route labels are not selections. Approved removals remain zero until the edited document returns and its selections are checked.

The artifact is editable UTF-8 text, continuing the first pilot's format. The required Word rendering dependency is unavailable; no unrendered DOCX is presented as verified. The previous count-limited SQ023 pilot remains preserved under `../johnny_dialogue_review_20261107_01/`.

## Source qualification and verification

`evidence_01/source_inventory.json` records five registered entry routes, the current selection registry, exact ArchiveXL registration hashes and 43 graph-resource providers across the quest closures. No graph import is missing or provider-ambiguous within those captured inputs. `evidence_02/` contains 28 fresh phase/quest exports with raw/export hashes; `evidence_03/phase_graphs.json` preserves their normalized graphs, support references and conditions. The 15 scene imports include native/shared resources as well as private PTFR copies.

The selected review uses connected, reachable phase scene-input callers. Eight called scenes contain the 49 Johnny events. An imported MQ023 conversation also appears in MQ042's resource census, but its scene node has no connected input and is not reachable in that quest route. Its 19 source events were explicitly excluded from this batch on caller evidence. Import presence did not become execution proof or expand MQ042 into a different quest.

The selected Step 2 database hash is `A60FEA94BDD5C7777484710E57753F558C80CFD36E553BE03DF02CB8EF459D2E`. It was hashed and opened read-only. Every transcript item was compared with its raw decoded scene event, exact line ID, actor/player binding, localization ID and authored time. The external English text variants were independently checked at their original localization JSON pointers, with raw/export provider hashes verified.

`evidence_05/review_manifest.json` maps every short ID to exact event/source identities, variants, caller inputs, context paths and revision. Its original text copy is preserved beside it. The selected document has **455 displayed transcript entries and 121 unique event IDs** because context overlaps and branches differ. Its SHA256 is `D898BECCEE1F05D392207B46253B79EB1C04BFC9EDACF2E6ACCF33A8D9FD9C78`.

`qa_03/verification.json` and `qa_03/independent_verification.json` record PASS with explicit context boundaries. Independent readback accounts for all 49 qualified Johnny occurrences, verifies every displayed ID and original-copy equality, and checks 263 context paths against edges reconstructed directly from raw scene JSON. The KOLD MIRAGE check confirms that the fresh entry's zero recognition flag and the scene's increment select V's corresponding recognition wording. Eighty-four contradictory context-path candidates were rejected. Raw phase inspection found no additional Johnny voiceset dispatch candidate in these captured phase graphs. Earlier intermediate outputs and generators remain preserved; only output_03 is selected.

## Limits and next action

This completes the five-quest source transcript batch, not the whole game's Step 3 review or a runtime chronology audit. Native prerequisites, entitlement, earned history, original/saved owners and normal progression remain necessary. Small Man, Big Mouth is conditional on Streetkid history; These Boots Are Made for Walkin' is conditional on Nomad history. No single save is claimed to admit both life paths.

Context paths retain source choices and conditions but do not simulate the engine, all concurrent controllers or legacy/native saved owners. Unknown ordering remains marked. Audio delivery, nonverbal reactions, choice removal and any adaptation of outcomes/timing require their later review. The global post-Tower occurrence denominator remains unmeasured.

Next, import the user's edited J5-03 copy using only IDs explicitly followed by `(remove)`, deduplicate marked IDs, and hold partial text edits, variant-specific requests or source changes for review. No game resources, installed files, saves, facts or admission policy were changed. No build, deployment or gameplay test was performed.
