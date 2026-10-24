# Tower Continuation: Alpha Test

Version: `v0.1.1-alpha.20261024`

This is a **full mod snapshot**, not an incremental patch. The ZIP contains 117
Tower Continuation files: 22 archives, 20 ArchiveXL registrations, 72 REDscript
files, one tweak, and two CET scripts. It includes the history snapshot fallback,
loading cover and current H10 housing logic. It does not bundle third-party
frameworks, other mods, saved games, generated history JSON or development data.

This is an alpha test release. A 24 October local session showed H10's
purchase offer, a payment receipt and its icon changing to owned. Physical door
access, apartment services, save/reload, genuine first transition, and other new
paths still need verification. Use a separate test save.

## Requirements

Windows, Cyberpunk 2077 with Phantom Liberty, and a compatible mod framework
stack are required. The development environment used Patch 2.5 and:

| Dependency | Tested development basis |
| --- | --- |
| RED4ext | [1.30.0](https://github.com/WopsS/RED4ext/releases/tag/v1.30.0) |
| REDscript | [0.5.32](https://github.com/jac3km4/redscript/releases/tag/v0.5.32) |
| Codeware | [PR 63](https://github.com/psiberx/cp2077-codeware/pull/63), with the local two-line [PR 65](https://github.com/psiberx/cp2077-codeware/pull/65) empty-variant guard |
| TweakXL | [PR 22](https://github.com/psiberx/cp2077-tweak-xl/pull/22) |
| ArchiveXL | [PR 31](https://github.com/psiberx/cp2077-archive-xl/pull/31), with the SDK230 slot-lookup correction and local [PR 32](https://github.com/psiberx/cp2077-archive-xl/pull/32) empty-parts guard |
| Cyber Engine Tweaks | 1.38 development installation; **required** for the included history snapshot exporter |

The Codeware and ArchiveXL builds include local source patches; this table does
not identify a single official binary release with those exact bytes. Framework
binaries are not in the ZIP. The local Codeware, TweakXL and ArchiveXL builds used
MSVC 14.44 and xmake 3.1.2. Other framework combinations remain unverified.

## Install

1. Close the game. Back up saves and existing Tower Continuation files.
2. Install compatible frameworks using their own instructions.
3. Download `TowerContinuation-v0.1.1-alpha.20261024.zip` under this release's
   **Assets**. GitHub's automatic **Source code** ZIP does not contain the mod.
4. Extract the ZIP to a temporary folder. Merge the supplied `archive/`, `r6/`
   and `bin/` into the Cyberpunk 2077 game folder. Keep the paths exactly as
   supplied. The `bin/` folder installs both CET scripts, including the required
   `PTFR_HistorySnapshotHS1` exporter.
5. Start the game on a separate manual test save. Do not force quest facts or
   replay rewards to bypass deferred content. On a post-Tower save without a
   captured pre-ending snapshot, HS1 makes a one-time
   `post_ending_fallback` snapshot; it is not pre-ending history.

The ZIP contains only this mod's paths. Merge these directories; never replace
the game's entire `archive`, `r6`, or `bin` directories. Installing over the
previous 23 October pre-alpha adds eight mod files and updates the changed
files. Migrating from arbitrary older development builds requires individual
review of stray files and saved progress.

## Known limits

- Current H10 purchase uses an automatic confirmation when V approaches the
  private apartment door. A conversation-style interaction is planned for a
  later version. The purchase offer, receipt and icon switch have local log
  evidence; physical access, services and reload still need testing.
- Bounded entry coverage is 80 gigs and 60 side jobs, not every quest stage.
  Eighteen selected side jobs have no added implementation.
- The history fallback records the current post-ending state when no valid
  pre-ending snapshot exists. Unsupported unfinished quest paths defer.
- Final prerequisite policy, full initial-state validation, measured startup
  speedup, and beta-to-stable save-upgrade fixtures remain incomplete.

## Verify or remove

The separate `.zip.sha256` asset contains the ZIP's SHA-256 hash. In PowerShell:

```powershell
Get-FileHash -Algorithm SHA256 .\TowerContinuation-v0.1.1-alpha.20261024.zip
```

`TowerContinuation/FILES.json` inside the ZIP lists each packaged mod file, size
and SHA-256. For removal, close the game and remove only these version-owned
files, then restore the pre-install backup as needed. Removing files does not
undo saved purchases or quest state. Do not remove shared framework files.

Report issues through GitHub Issues with the release version, framework versions,
steps and relevant logs. Do not post personal saves or private data publicly.
