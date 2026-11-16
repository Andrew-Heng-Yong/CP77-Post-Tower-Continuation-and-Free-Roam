# KOLD MIRAGE actor and interaction rewrite — KM2

KM2 is installed over PE1. It removes the remaining Johnny presentation and conversation dependencies from KOLD MIRAGE's private freezer scene and disables his actor in the private Nix scene. The intended freezer route is **Open → scan → Take cyberdeck → go to Nix**. The user selected an existing save before the first fridge opening as the update/test point. Installation and gameplay results are separate.

## Accepted user result and cause

The user confirmed that JP1's selected Johnny/V speech removals were correct and had not caused bugs on the reported route. They also observed Johnny's brief digital spawn/shadow, actor title and scanner identity, cigarette/smoke, a Talk to Johnny objective, silent waits, and a Close/That stench prompt followed by more waiting. This qualifies the speech-cut result only; it identifies presentation/interaction work left by the first pilot. Wider marker-count investigation is deferred at the user's request.

The source confirms the freezer's active spawn command, spawned-actor wait, cigarette workspots, actor animation/phantom events, speaker-distance interruption, Johnny journal steps and repeated Close/Open menus. JP1 deliberately retained those fixed timings and non-dialogue events. Removing voiced events alone could not remove their actor or interaction dependencies.

Fresh capture verified the exact seven current private KOLD resources and seven native resources across 134 archive indices. There is one matching provider for each query. [Source/provider capture](source_01/manifest.json) and [selected plan](input_02/plan.json).

## Exact behavior change

- First Open keeps the original freezer animation, effects, sound and Open-objective completion, then arms native scanning directly. V's existing situational reaction runs in parallel.
- The original cyberdeck scan/focus alternatives and one-shot XOR remain. They complete the Scan objective and expose the original single-choice Take interaction. The retained V box observation still follows existing recognition history and does not gate Take.
- The original Take option, encrypted-deck item grant and pickup sound remain. The existing automatic-close branch replaces the final manual Close prompt. The Take objective completes and the native Talk to Nix objective activates. Leaving the freezer area still owns the native scene exit/cleanup.
- Normal entry cannot reach Johnny's spawn, spawned-character wait, workspots, Talk to Johnny activations, or the repeated Close/Open/Johnny menus. Inactive Johnny journal entries remain inactive; no fake conversation completion or recognition fact is written.
- Johnny's actor IDs remain serialized, with `isEnabled`, `alwaysSpawned` and `spawnOnStart` disabled in both private scenes. His section actor behaviors and presentation events are removed. This addresses the entity source of his name, scanner identity, digital effect and cigarette instead of hiding only a mesh.
- The freezer's Johnny-speaker distance interruption is disabled both in the scene and its existing phase caller. The caller reapplies that scoped operation after load for the selected pre-Open saved scene. Six optional Johnny workspot/wait branches in the Nix scene are disconnected. Nix's dialogue, rescue interactions, authored crisis timing, choices, outcomes, rewards and other cleanup remain native.

Only three private resources change: the freezer scene, Nix scene and freezer phase. All resource/node/option IDs, retained speech events, actor IDs, parent/root prefab scopes and native owner receipts remain. No new resource, phase injection, saved field, controller, script, item writer or native-resource override is added. Sweet Dreams and all PE1/KM1 admissions stay unchanged. Saved scenes already beyond the first Open are outside this transition qualification; no owner is reset or replayed.

## Verification

Cooked readback passed **896 checks and eight bounded signal fixtures**: fresh scene and saved Open choice, both recognition histories, and each native scan alternative. The fixtures verify Open before scan, Take after scan without waiting for bark completion, one encrypted-deck grant, no repeated grant on redundant signals, no Johnny journal activation, native Nix objective, automatic closing and both original exits. They are static signal/event checks, not engine or gameplay tests.

The verifier constrains every changed node payload and metadata field, checks all retained speech unchanged, removes 49 presentation/socket events with their references, and confirms no reachable Johnny command/objective/performer on the new route. Every graph/entry/node and menu option identity is retained. Nix's crisis callback at its original time and all independent actor/events remain.

All 1,581 packed payloads were extracted and SHA256-checked: three changed, 1,578 retained. The full 51-path ZIP was reopened and every member checked. The archive is the only planned installed replacement; the other 50 files, XL bytes/registrations and all scripts remain identical. The exact 148 current script sources match PE1's successful full compile and staged hashes; the compiler/base cache remain pinned, with only the normal 16-byte timestamp sidecar refresh recorded. No new compile was required for these resource-only edits.

[Cooked/delta and signal verification](verification.json), [unchanged-source compile inventory](compile_inventory.json), [archive readback](archive_readback.json), [package manifest](candidate_02/package_manifest.json) and [transaction review](installer_review.json).

The first preparation refused a direct access to a handled phase interruption operation. Its partial `candidate_01`/`input_01` and failure record are preserved. The corrected selected output is `candidate_02`/`input_02`. No game/save files changed during preparation.

The user subsequently accepted KOLD MIRAGE editing as complete with no bugs reported. [Acceptance](observations/user_acceptance_20261108_01/REPORT.md). No repeat test is requested. Exact outcomes, voices/locales, reward idempotence, save/reload and all-save transitions were not separately itemized.

## Installed result

Closed-game preflight, installation, post-install verification and rollback readiness passed. Only the existing consolidated archive changed. All 51 Core files and 26 dependencies verified; all 313 save files and unmanaged game metadata were preserved. The exact PE1 archive recovery copy is verified. Twenty-two actions across eight isolated fixtures passed full Core51 install/rollback, interrupted replacement/receipt recovery, interrupted rollback, game-running refusal and unknown-file refusal. No game was launched and no save/fact edit or real rollback occurred.

Archive SHA256: `715374F89FAFE02137C34A9C808EF527167C8A976C9B8C3C600C4AEAFF273C64`. [Installed manifest](deployment_01/installed_manifest_01.json), [preservation verification](deployment_01/verification.json), [deployment report](deployment_01/REPORT.md) and [pre-Open test card](TEST_CARD.md). Gameplay acceptance was pending at installation and was subsequently supplied by the user; see the later acceptance below.

## User acceptance - 8 November 2026

The user confirmed that the editing works with no bugs and declared KOLD MIRAGE editing complete. Status: **USER_REPORTED_PASS / EDITING COMPLETE**. No repeat test or further KOLD MIRAGE editing is requested. [Exact confirmation](observations/user_acceptance_20261108_01/REPORT.md).
