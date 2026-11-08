# Step 3 human-review pilot P1

The user authorized a pilot of around 50 dialogue lines on 7 November 2026. The editable document is `output_01/Johnny_dialogue_review_pilot_01.txt`. It contains **53 displayed dialogue entries, 23 unique event occurrences and six Johnny anchors**, sampled from the SQ023 Sinnerman family conversation after the restaurant meeting. Context windows overlap and deliberately reuse exact event IDs. The pilot is awaiting human review; approved removal events remain zero.

The document follows the agreed three preceding lines from any speaker and five following V lines on one stated route. Its last excerpt has only four following V lines before the discussion ends and the stand interaction becomes available. Both V text variants appear together where their wording differs. The reviewer deletes entries to keep in the game and retains only removal selections with their IDs. One retained copy of a repeated ID selects the same occurrence once. Text edits or variant-specific requests require review on import. Menu labels describe the route and are not removal selections in this pilot.

This is an editable UTF-8 text artifact. The documents workflow was inspected, but its mandatory Word rendering dependency is unavailable in this Windows runtime. No unrendered DOCX was produced or presented as verified.

## Source and validation

The selected Step 2 index is `../johnny_dialogue_index_20261107_02/index_05/dialogue.sqlite3`, SHA256 `A60FEA94BDD5C7777484710E57753F558C80CFD36E553BE03DF02CB8EF459D2E`. It was opened read-only and its hash verified. The current private scene's raw/export hashes and the external English subtitle provider's raw/export hashes match the indexed inputs. Every selected event was checked against decoded scene data for ordinal, event ID, line ID, speaker binding, localization ID, gender usage and authored time. Subtitle variants were independently checked at their original localization JSON pointers.

Fresh phase exports in `evidence_01/` match the captured current private entry, SQ023 master and restaurant phase hashes. Their normalized graphs in `evidence_02/context_source_graphs.json` retain all conditions and support references. They establish the PTFR entry's post-Tower gate, the family controller's restaurant phase, and the restaurant phase's scene caller. The selected registry includes both Sinnerman and There Is A Light That Never Goes Out. These are conditional source routes; native prerequisites, preserved history, ownership, support and normal progression remain necessary. No new executing-owner or gameplay claim is made.

Exact review mapping lives in `evidence_02/review_manifest.json`; the unedited document is preserved separately as `evidence_02/original_review_pilot_01.txt`. The manifest retains all route timeline events, selected choice IDs, exact graph edges, variants, hashes and short-ID mappings. Choice 825 activates V's reply and Johnny's response in parallel sections; authored times put the spoken reply first. The first construct topic follows `sq023_j_smokes=0` through section 868. The subsequent topic follows the loop's write of one through section 3844. Identical text in alternate section 3837 was not substituted for section 868's event identities.

`qa_01/verification.json` records PASS for source identity, event/text mappings, explicit route edges and state transition, displayed ID order, repeated-ID handling and original-copy equality. The text document was read back in full. Its SHA256 is `78AA02A23C8EB49EF45A05F1064DD41290384A20E55BCD289BF667E84F6DA6D8`.

## Limits and next action

The pilot samples one route, not all SQ023 branches or the whole game's Step 3 review. Following V entries are contextual candidates, not automatic reaction classifications. Audio delivery, animation, nonverbal responses and choice removal are outside this transcript pilot. The full post-Tower occurrence denominator remains unmeasured. q303 and native ending-owned contexts were not introduced into this batch.

Next, import the user's edited copy, resolve its retained IDs and flag ambiguous text or variant edits before technical cut planning. No game resources, installed files, saves, facts or admission policy were changed. No build, deployment or gameplay test was performed.
