# Body-view repair revert — 16 November 2026

The user requested removal of all Tower-mod measures aimed at the post-ending first-person body-view symptom, including the first-person refresh, after updating Immersive First Person (IFP) for game 2.50. IFP being outdated is a plausible contributor, not a confirmed cause. The latest RED4ext loader log still predates the IFP update, so native loading and the visual result remain unverified.

## Scope

BV1 changes only `PTFR_LoadingCoverLC1.reds` and `PTFR_RestrictionsR1.reds` in the 51-path consolidated Core. It removes the queued third-person activation and first-person return, their timed cover wait and stock-hands gate, the optional ending-loading hide/visual-state cleanup, and the body/presentation and fast-travel tracing added with TP1–TP3. It removes the unused TP2 hands-settled accessor. The LC5 credits cover, ordinary setup checks, and pause-menu cover dismissal remain active. The original post-Tower stock-hand attachment routine remains because it belongs to the cyberware treatment and predates the body-view repair. Previously saved fields remain declared for save compatibility; they have no active repair path.

The first derived source was set aside as `source_01` when review found that the presentation callback also handled credits-cover pause dismissal. The reviewed [source_02](source_02/PTFR_LoadingCoverLC1.reds) retains that callback's credits-cover behavior and removes its TP2 tracing. [Source derivation](prepare_source.py) records exact input guards.

## Offline validation and installation

- The installed LC5 manifest SHA-256 was `02E089A382D01A0542BA804CAA6B2892D2A411B8C25F755A8C503C1483D703DF`. Both edited inputs matched its hashes. The staged 51-file Core differs in exactly the two named scripts.
- The successor compiled all 149 current `.reds` sources with the installed compiler and cache, in a fresh offline output. The game's regenerated 16-byte cache timestamp was separately pinned; no game source or cache was written by compilation. [Compile assessment](candidate_01/compile_01/assessment.json) · [Staged manifest](candidate_01/core_manifest_01.json)
- Workspace fixtures passed exact two-file replacement/rollback and unknown-drift refusal. The guarded closed-game install then replaced the two scripts. Independent readback verified all 51 Core files, 47 protected dependencies, 14 updated IFP files, four preference/binding files and 451 unchanged save files. Exact old-file copies and the [journal](work/recovery_01/journal.json) remain ready for file rollback. [Deployment plan](work/plan_01.json) · [Installed receipt](work/installed_01.json)

No game launch, save edit, or release package was performed. The next check is a genuine Tower handoff with IFP v2.2.0: confirm RED4ext loads its native plugin, then inspect the first-person body before any vehicle workaround. If clipping recurs, use the previously agreed paired read-only CET capture at a matched angle before and after the workaround. The smaller loading-page layout request is still deferred.
