# Instruction-system maintenance report

29 October 2026. Scope: instruction and documentation maintenance only. No runtime/quest/resource/build/install/save/release changes were authorized. No comprehensive quest-restoration audit was started.

## Inventory and authority

Before restructuring, the only repository project AGENTS file was the root. Discovery included ignored/local trees. One vendored `CLAUDE.md` was found in `diagnostics/mod_updates_20261023_01/mod_settings_src/`; its installation/tagging guidance belongs to that third-party project, not this mod. One vendored `.cargo/config.toml` is compiler configuration, not an AI authority. No ancestor AGENTS/override was found. Global Codex AGENTS is empty; global config was inventoried by path/hash and key names only, with no values copied or edits made.

[`inventory.json`](inventory.json) records original/new instruction files, configuration scope, referenced paths and historical docs. The new system has one root and six appropriately scoped AGENTS files. Existing investigation reports are retained; knowledge/history links identify which evidence answers which question.

## Sizes

| File | Original bytes | New bytes | Result |
| --- | ---: | ---: | --- |
| AGENTS.md | 544,256 | 8,183 | 98.5% smaller; within the requested 5–10 KB range |
| PROJECT.md | 155,934 | 5,011 | Purpose, policy and authority; original diary archived |
| ROADMAP.md | 201,112 | 3,876 | Outstanding work and evidence limits; obsolete percentages removed |
| README.md | 9,962 | 10,366 | Current PH3 pointer added; older component chronology labelled historical |

Original bytes/hashes and exact snapshots: [`originals.json`](originals.json). Snapshots include all four original files and are inactive historical data, not additional automatically loaded AGENTS files. Other historical documentation, source scripts and proof manifests remain in place.

## Restructuring and knowledge base

Root rules now separate permanent invariants from current task scope, current-state evidence and historical reports. Specialized instructions are scoped by directory. PROJECT/ROADMAP no longer repeat the development diary. The [knowledge base](../../knowledge/README.md) contains current state, invariants, conflicts, history navigation and procedures for REDscript dependencies/compilation, vanilla extraction/editing, consolidated archives, quest/phone/cleanup investigation, static auditing, packaging/deployment/verification/rollback.

Every procedure states prerequisites, existing command/API/script references, outputs/checks and recorded/derived/historical/unverified status. No current all-project rebuild or comprehensive auditor command was invented. The knowledge base describes PH3 while explicitly preserving the older VD1 beta separation. The user's latest “fix worked” report is recorded in current-state without rewriting immutable pending assessments or extrapolating to every call.

## Traceability and conflicts

The [critical-rule matrix](TRACEABILITY.md) covers 32 invariant groups. Paragraph-level CSV/JSON index all 1,311 original paragraphs, including 812 marked for critical wording, to exact preserved source and topic destination. Automatic routing is a navigation aid; the manual matrix and explicit conflict register are the policy review.

Fifteen conflict/supersession records remain visible. Explicit later decisions resolve older restart/housing/override interpretations; proposed profile UI, current beta integration, stale packaging test, audit denominator, current full rebuild, opaque sectors and future-save upgrade proof remain unresolved or unverified. No runtime policy was changed to settle those questions.

## Preservation and verification

Run evidence is in [`verification.json`](verification.json), [`link_check.json`](link_check.json), [`traceability_summary.json`](traceability_summary.json), [`coverage_checks.json`](coverage_checks.json) and the captured baseline identified by [`baseline_identity.json`](baseline_identity.json). The maintenance utility compares all 380,126 pre-existing repository files by path/size/mtime and all 855 game-tree files by the same metadata; it does not follow 167 repository reparse points. SHA256 covers 4,762 protected files, including project source, candidate utilities, complete PH3 source/package, dist/release, 51 installed Tower files, required Atelier correction, 49 Lizzie files, all save files and global Codex configuration. Every original snapshot is rehashed.

Final verification is **PASS**: four existing Markdown files changed, 21 instruction/documentation files were added outside the dedicated report folder, zero pre-existing files were removed, and zero protected hashes changed. All 121 local links and 13 supplemental invariant-coverage checks passed. The manual matrix covers 32 critical rule groups; no runtime or quest-audit tool was executed. This verifies the actual maintenance delta; it is not a game/quest audit. Historical extracted/vendor/fixture resource payloads and large native game archives receive complete metadata comparison rather than an unnecessary 59.8 GB content rehash. This explicit limit is not a claim of cryptographic identity for every historical byte.

The large local metadata baseline is in `generated_baseline/baseline.json`, ignored by the existing `generated_*/` rule; no Git ignore configuration was changed. Archive/research guidance remains in the tracked knowledge base rather than new files inside those ignored data trees.

Two small utilities under this maintenance report folder generate inventory/traceability and verify documentation preservation. They do not build, audit quests, deploy, edit game/save state or replace project runtime tools. The baseline excludes only this report folder and `.git`; verification checks the changed/added repository path allowlist. No existing runtime/source/build/deployment script was edited or invoked.

## End boundary and handoff

The task ends after instruction verification. [HANDOFF.md](HANDOFF.md) gives a concise fresh-session task for building the comprehensive static vanilla-parity auditor. No quest audit, restoration implementation, build, installation, release, save/fact edit or gameplay test is to follow automatically in this session.
