# Cyberpunk 2077: Post Tower Continuation and Free Roam

A work-in-progress mod for continuing free roam after **The Tower** ending in
Cyberpunk 2077: Phantom Liberty, while preserving the ending and its consequences.

## Download the mod

**[Download Post Tower Continuation and Free Roam Alpha Test ZIP](https://github.com/Andrew-Heng-Yong/CP77-Post-Tower-Continuation-and-Free-Roam/releases/download/v0.1.1-alpha.20261024/TowerContinuation-v0.1.1-alpha.20261024.zip)**

[Release notes and downloads](https://github.com/Andrew-Heng-Yong/CP77-Post-Tower-Continuation-and-Free-Roam/releases/tag/v0.1.1-alpha.20261024)
| [Installation and dependencies](release/INSTALL-v0.1.1-alpha.20261024.md)
| [All releases](https://github.com/Andrew-Heng-Yong/CP77-Post-Tower-Continuation-and-Free-Roam/releases)

Choose the named **TowerContinuation ZIP** under the release's **Assets**. GitHub's
automatic **Source code** downloads are for development and do not contain the
packaged mod. This **24 October Alpha Test** includes the current
Tower mod snapshot. Framework dependencies are separate. Use a separate test save
and read the installation instructions first.

**Post Tower Continuation and Free Roam** is the mod's official name.
`PTFR`, `TowerContinuation`, and `TowerContinued` remain in internal IDs and
historical download paths for compatibility with existing saves and releases.

## Development status

The repository contains source; installable mod packages are hosted in Releases.
The locally installed consolidated build packages the current alpha and later
fixes in one ZIP. The user reports it working with public Codeware 1.21.1;
full quest coverage remains under test.
The linked public Alpha Test remains the published download.
The current local [CC1 successor](docs/coaster_post_doublelife_20261027.md) removes
new post-Double-Life admission to Jean's one-time Love Rollercoaster story. It
retains already-issued quest progress and the repeatable ride. All 51 installed
paths and 301 save files were verified; gameplay after a new load is pending.
The preceding [SC3 successor](docs/skippy_ambient_sc3_20261026.md) repairs
Skippy's equip/unequip loop after SC2 also failed to restore his combat lines.
Logs and saved state show that SC1 permanently stopped its controller when
Skippy was unequipped. SC3 preserves that receipt and starts a corrected native
loop after the old controller has retired. The same 51-file install retains
the Love Rollercoaster Johnny-dialogue removal. Installation, rollback readiness
and all 301 unchanged saves are verified. The user now reports audible enemy
reactions and matching hologram expressions. A [trigger follow-up](docs/skippy_triggers_20261027.md)
confirms native aim/autofire and draw behavior, and no authored jump-confirmation
response for that ambient line; reload remarks and the one-time quest remain
unverified in gameplay. SC3 is local and unreleased.
The earlier [CR1 repair](docs/consolidation_repair_cr1.md) restores 30
corrective resources discarded by consolidation, replacing only the existing
combined archive. Its static checks and installation verification passed;
gameplay and already-running saved quest owners still need validation.
See the [unreleased change log](CHANGELOG.md) for work since that alpha.
As of 24 October 2026, the development environment includes a history snapshot
fallback, a setup cover, and [H10 apartment purchase and map icon changes](docs/h10_h4.md).
Local logs now show the H10 offer, payment receipt and owned icon. Door access,
services and reload need more testing. A public beta has not been published, and
the initial post-Tower state is not yet declared complete.

The local development installation covers bounded beginnings for 80 gigs and 81 side
jobs. That does not establish every quest stage, eligibility on every save, or
complete gameplay verification. Completed content and earned progress must be
preserved; unsupported unfinished quests defer instead of restarting. The latest
three additions and the River hold are documented in the
[S30 side-job record](docs/sidejobs_s30_20261026.md).

The beta release target requires save continuity into future stable versions.
Actual transition and save-upgrade fixtures are still required. See the
[beta release contract](docs/beta_release_contract.md).

### Future fixes and package size

Keep the production install consolidated. Update the affected file in the current
package and ship a new complete version of that package; do not stack separate
hotfix overlays in the player's game directory. Keep the previous package and
replaced files in the development archive for comparison and rollback. Add an
installed file only when the game requires a separate resource or script module,
and remove superseded paths from the next package. See the
[consolidation and recovery record](docs/full_consolidation_v1.md).
The earlier temporary Scav workspot prototype was folded into the 51-file
successor and its three diagnostic install files were removed. The user reports
hostile NPC animations restored in their current test; the source scope is
recorded in the [ambient investigation](docs/world_hostile_idle_report_20261026.md).

## Repository contents

| Path | Contents |
| --- | --- |
| `redscript/` | Runtime systems and versioned REDscript implementations |
| `prealpha/` | Component source, templates, generators, build/deployment scripts, and tests |
| `profiles/` | Restriction profiles, configuration, and perk catalogue |
| `tweaks/` | TweakXL configuration |
| `tools/` | Project build, validation, extraction, and deployment utilities |
| `release/` | Download instructions, release notes, and exact package manifest |
| `docs/` | Design, policy, and playtest documentation |
| [PROJECT.md](PROJECT.md) | Project context and recorded development state |
| [ROADMAP.md](ROADMAP.md) | Scope, priorities, and outstanding work |
| [AGENTS.md](AGENTS.md) | Development constraints and chronological handoff records |

Versioned predecessors are retained because existing saves and pinned build
records can depend on their identities. Directory presence does not mean a
component is currently installed or approved for a new release. Consult the most
recent status entries before using older instructions.

## Local development inputs

The `.gitignore` excludes compiled `.archive` mods, extracted native resources,
research findings and dumps, generated build/package folders, deployment
fixtures, downloaded binaries, caches, logs, recovery backups, and saved games.
Those files remain local and are not part of this source upload. Small source
contracts and configuration remain tracked.

Many scripts refer to those local inputs, exact build hashes, or machine-specific
game/tool paths. A fresh clone is therefore **not a self-contained build**.
Use a legally installed copy of Cyberpunk 2077 with Phantom Liberty and the
appropriate local toolchain; do not copy all versioned scripts into the game or
run historical deployment scripts indiscriminately.

The development stack includes RED4ext, REDscript, Codeware, ArchiveXL, TweakXL,
WolvenKit, and Python, with CET used by some diagnostics. The latest workspace
records describe an experimental Patch 2.5 compatibility stack; they do not
establish compatibility with arbitrary framework versions. Build outputs and
third-party tools are deliberately not distributed here.

Source files are retained with their existing line endings because build records
use exact byte hashes. Generated outputs and pinned historical sources should
be changed through successor versions rather than overwritten.

## Playtesting and releases

Start with the [beta release contract](docs/beta_release_contract.md),
[housing checklist](docs/housing_h1_playtest.md), and
[S28 side-job checklist](docs/sidejobs_s28_playtest.md).
The remaining 18 selected side-job entries are now installed in the local S29 test stack;
follow-up quest-tree testing is pending. See [S29 test notes](docs/sidejobs_s29_playtest.md).
File rollback restores mod files only; it does not reverse changes already
stored in a saved game.

This is an independent fan project and is not affiliated with CD PROJEKT RED.
