# Prepared marker and encounter admission — PE1

PE1 is installed over KM1. It applies the user's Boolean setup policy across the installed restored entry families, adding support for 17 entries whose source initializes 20 setup fields exactly to one before the relevant discovery/progress boundary. The native owner supplies the marker and encounter. Deployment and gameplay results are separate from the static findings below.

## Scope and evidence

The audit inventoried all 1,000 installed quest/phase resources in the 1,581-member consolidated archive, 827 registered roots and 305 rows across 12 runtime data classes. It reused normalized models only at exact current resource hashes and freshly exported the 21 changed/new phases. Current-provider checks passed for all 1,000 phases and 29 native prefix/retirement resources across 134 archive indices. [Inventory](inventory_02.json), [root traces](roots_03.json), [provider proof](providers_01/manifest.json) and [decisions](decisions_01.json).

The trace follows actual phase input sockets and nested graph/call paths. It is a may-path analysis, not an engine scheduler or proof that a saved owner executes. Base-game Tower success reaches its main-game terminating output; the EP1 Tower-success route cuts the reviewed minor/open-world parent branches before the killed receipt. This is stronger than relying on a killed fact alone, but it does not decode every live owner on every save.

The newly covered entries are:

| Family | Entry | Setup fields now accepted at 0 or 1 |
| --- | --- | --- |
| Side job | Sex on Wheels (`mq044_jakes_vehicle`) | `mq044_started`, `mq_044_started_in_main` |
| Side job | Bullets (`mq030_melisa`) | `mq030_active` |
| Side job | Shoot to Thrill (`mq011_wilson`) | `mq011_active` |
| Side job | Addicted to Chaos (`wst_ep1_04`) | `wst_ep1_04_active` |
| Side job | Happy Together (`mq010_barry`) | `mq010_active` |
| Side job | Shot by Both Sides (`mq305_combat_zone_report`) | `mq305_active`, `mq305_01_active`, `mq305_started` |
| Side job | The Gig (`sq_q001_wakako`) | `sq_q001_active` |
| Side job | Ezekiel Saw the Wheel (`mq022_ezekiel`) | `mq022_active` |
| Side job | Every Breath You Take (`mq028_stalker`) | `mq028_started` |
| Side job | Sinnerman (`sq023_hit_order`) | `sq023_active` |
| Side job | Nitro (`mq060_nitro`) | `mq060_active` |
| Pickup | `sts_ep1_12_pickup` | `wst_ep1_02_start` |
| Gig | `sts_bls_ina_11` | `bls_ina_11_active` |
| Gig | `sts_cct_dtn_05` | `dtn_05_active` |
| Gig | `sts_ep1_03` | `sts_ep1_03_start_community` |
| Gig | `sts_ep1_13` | `sts_ep1_13_active` |
| Gig | `sts_ep1_06` | `sts_ep1_06_active` |

KM1's KOLD MIRAGE rule, MQ040's idle-service handoff, QR19's retained-message MQ018 adapter and N21's four exact initialized scanner adapters remain unchanged. The policy review also covers the unchanged families; it adds no wildcard exception to ordinary phone, combat, stage or outcome guards. Shared `mq011_active` is widened only for Shoot to Thrill's ID, not The Gun.

## Implementation and protected behavior

Twelve private entry resources change 25 condition-node payloads. Each selected exact-zero fact predicate becomes `zero OR one`. No graph node, socket, edge, root/nested prefab scope, resource path, phase injection, input or saved identity changes. All other guard leaves stay identical. The five gig entries need no graph change: their current private parent already enters the original native setup when the runtime eligibility checks permit it.

Six scripts change. Four side-job tables widen only the selected maxima, leaving minima and other fields intact. Their samplers and the native gig sampler require the accepted Inactive baseline whenever a newly allowed setup flag is one. The U9 history getter recognizes only the selected per-ID Boolean fields and still requires the existing accepted history and state indices. A static, read-only helper holds the exact ID/field mapping. The saved snapshot data class, catalogue fingerprint, classification, persistent fields and schema remain unchanged. No native setter, marker writer, journal reset, item/reward grant or owner restart is added.

Initialization counters remain protected. Moving Heat's `q304_car_retrieval_started/active` increment on entry; the five considered gig community fields `arr_10_community_start`, `ina_02_ready`, `ina_03_community_start`, `spr_03_community_start` and `arr_05_community_start` also increment. Re-entering with one would make two. Supporting those states needs a counter-stage handoff, not this Boolean widening. Later-stage, fight/chase, phone, lease and completion/reward fields remain protected.

Three native trace scopes remain unresolved and unchanged: courier's outro input mismatch/bounded scan, the embedded combat input in `sts_hey_gle_01`, and four dangling cached edges in `sts_std_rcr_02`. They receive no approval inferred from an unfiltered export. This audit changes entry admission; it does not establish full quest parity or universal stage support.

## Verification and preserved evidence

- Cooked resource readback passed 12,671 checks: exact independent predicate reconstruction, all selected 0/1 combinations, invalid values, and boundary variations for every retained fact/journal/vehicle condition against the predecessor guard semantics. Only the planned 25 payloads changed.
- A fresh isolated compile passed all 148 registered REDscript sources and 151 current installed compiler inputs, with the exact six overlays. Installed compiler inputs remained unchanged during compilation.
- All 1,581 packed members were extracted and hash-checked. Only the 12 private entries differ; the other 1,569, including KM1's KOLD entry, JP1's three edited scenes and HH1 support, are retained.
- All 51 developer ZIP paths were reopened, CRC-checked and SHA256-checked. Exactly seven installed paths are planned replacements: the archive and six scripts. XL bytes and registration order/IDs are unchanged; no new depot or phase-node namespace is introduced.

[Cooked/source verification](verification.json), [compile](compile_01/result.json), [archive readback](archive_readback.json), [package manifest](candidate_02/package_manifest.json) and [transaction review](installer_review.json).

The first preparation stopped on a CRLF-sensitive source match; its partial candidate and failure report are preserved. The selected successor uses fresh `input_02` and `candidate_02` directories. Inventory 02 corrects snapshot row ID labels without changing source/model pins. No failed/partial output is selected as installed evidence.

Static verification does not prove native scheduling, all saved-owner transitions, gameplay, reward idempotence or future-version save compatibility. Previously passed user routes remain accepted and need no repetition. The [post-Tower test card](TEST_CARD.md) uses natural entry and read-only diagnostics, without changing saves or facts.

## Installed result

The closed-game transaction passed real preflight, installation, post-install verification and rollback readiness. Exactly seven existing paths changed: the combined archive and six scripts. All 51 Core paths and 26 dependencies verified. All 313 save files and unmanaged game metadata remained unchanged. Exact KM1 recovery copies of the seven replacements are verified. No game launch, runtime command, save/fact edit or real rollback occurred.

Twenty-seven fixture actions across ten isolated roots passed full Core51 install/rollback, interruption before/after replacement, hard-crash recovery, interrupted rollback, game-running refusal and unknown-file refusal. Static and deployment results do not certify gameplay.

Current archive SHA256: `7DE1F4753DF98F549CA7D15A03533191F5A47D51BA9F1FF6DDD054F492E03DEC`. [Installed manifest](deployment_01/installed_manifest_01.json), [preservation result](deployment_01/verification.json), [deployment report](deployment_01/REPORT.md) and [post-Tower test card](TEST_CARD.md).

## Later marker observation — 8 November

The user initially saw no KOLD MIRAGE/new undiscovered markers, then reported restoration and noted that the markers needed time to appear. Record **USER_REPORTED_PASS for marker appearance on this attempt**. The initial CET sample had Issued1/Entered0, all five queried native fact prerequisites passed, and aggregate/finalboards content blocking were both false. No new fix was applied. Exact delay and later executing-owner state remain unmeasured; freezer interaction, dialogue/progression, rewards and reload remain pending. [Bounded observation](observations/kold_no_marker_20261108_01/REPORT.md).
