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
As of 24 October 2026, the development environment includes a history snapshot
fallback, a setup cover, and [H10 apartment purchase and map icon changes](docs/h10_h4.md).
Local logs now show the H10 offer, payment receipt and owned icon. Door access,
services and reload need more testing. A public beta has not been published, and
the initial post-Tower state is not yet declared complete.

The current implementation covers bounded beginnings for 80 gigs and 60 side
jobs. That does not establish every quest stage, eligibility on every save, or
complete gameplay verification. Completed content and earned progress must be
preserved; unsupported unfinished quests defer instead of restarting.

The beta release target requires save continuity into future stable versions.
Actual transition and save-upgrade fixtures are still required. See the
[beta release contract](docs/beta_release_contract.md).

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
File rollback restores mod files only; it does not reverse changes already
stored in a saved game.

This is an independent fan project and is not affiliated with CD PROJEKT RED.
