# Post Tower Continuation and Free Roam: experimental pre-alpha

Version: `v0.1.0-prealpha.20261023`

This is a full snapshot of the currently installed Post Tower Continuation and Free Roam mod,
including Housing H1, S28, and the earlier installed components. It is not just
an incremental housing patch. It contains 109 mod files: 22 archives, 20 ArchiveXL
registrations, 65 REDscript files, one tweak file, and one optional CET diagnostic
helper. Frameworks, unrelated mods, saved games, and development test fixtures
are not bundled.

This is an experimental testing release, not the planned beta. Current package
bytes match the recorded development installation. That check does not establish
successful gameplay on a new installation. Housing, purchases, native quest
behavior, cold/death reloads, and a genuine first transition still need live
verification. Keep a separate pre-install save and use a disposable test branch.

## Requirements

Windows, Cyberpunk 2077 with Phantom Liberty, and a compatible mod framework
stack are required. The development environment recorded for this package is
Patch 2.5 with the following exact framework versions/sources:

| Dependency | Development version/source |
| --- | --- |
| RED4ext | [1.30.0](https://github.com/WopsS/RED4ext/releases/tag/v1.30.0) |
| REDscript | [0.5.32](https://github.com/jac3km4/redscript/releases/tag/v0.5.32) |
| Codeware | [PR 63](https://github.com/psiberx/cp2077-codeware/pull/63), commit `6ef34ff0dd01ce9406e809e56e268f20fab367c4` |
| TweakXL | [PR 22](https://github.com/psiberx/cp2077-tweak-xl/pull/22), commit `fee3a9427c321445c67487e42e79dd2977c35701` |
| ArchiveXL | [PR 31](https://github.com/psiberx/cp2077-archive-xl/pull/31), commit `5f7dc88292ba010d871c6d24797591359f243a11` |
| Cyber Engine Tweaks | Optional for the included diagnostic helper; obtain a compatible version from [upstream releases](https://github.com/maximegmd/CyberEngineTweaks/releases) |

The three PR builds are experimental source pins, not ordinary stable download
versions. The local builds used MSVC 14.44, xmake 3.1.2, and a build configuration
pin for `tiltedcore.mimalloc` 2.2.4. Their binaries are not included in this mod
download. Obtain/build compatible dependencies separately; if you cannot provide
that stack, wait for a release based on supported stable dependencies. Installing
an arbitrary older stable framework is not a substitute. ArchiveXL PR 31 has
journal extension and hot reload disabled. Compatibility with other combinations
has not been established.

## Install

1. Close the game. Back up your saves and any existing Post Tower Continuation and Free Roam files.
2. Install the required frameworks using their own instructions.
3. Download `TowerContinuation-v0.1.0-prealpha.20261023.zip` from the release's
   **Assets** section. Do not use GitHub's automatic source-code ZIP.
4. Extract the archive to a temporary folder. Copy `archive/` and `r6/` into your
   Cyberpunk 2077 game folder, beside the existing `bin/` directory. Keep all file
   names and directory paths exactly as supplied; archive ordering matters.
5. If using CET diagnostics, also copy the included `bin/` directory. The helper
   is optional and does not activate the mod by itself.
6. Start the game and test on a separate manual save. For a first transition,
   install before completing The Tower and play through the genuine ending.
   Existing post-Tower saves can lack required ownership/history observations;
   unsupported paths defer. Do not force facts or replay rewards to bypass them.

The ZIP contains only this mod's paths. Merge the supplied directories; do not
replace or delete the game's entire `archive`, `r6`, or `bin` directories.
Older development installations can contain superseded files at other paths.
They require an individually reviewed migration; copying this ZIP over an
arbitrary old development setup is not a tested upgrade procedure.

## Known limits

- Live validation is pending for the newest housing and S28 changes.
- Bounded entry coverage is 80 gigs and 60 side jobs. This is not full quest-stage
  coverage; 18 selected side jobs still have no added implementation.
- Final R6.1 prerequisite enforcement and the Heroes/Brendan admission policy
  updates remain unfinished. Some installed paths still predate those policies.
- Completed progress must remain completed. Unsupported unfinished continuation
  defers; general quest restart or reward replay is not supported.
- Initial post-Tower state checks, startup latency work, and release save-upgrade
  fixtures are incomplete. Pre-alpha-to-stable migration has not been verified.
- The future beta must honor the separate beta save-continuity contract; this
  experimental download does not certify that requirement as passed.

## Verify or remove the package

The release includes a `.zip.sha256` checksum. In PowerShell, run
`Get-FileHash -Algorithm SHA256 .\TowerContinuation-v0.1.0-prealpha.20261023.zip`
and compare the result with that checksum file.

`TowerContinuation/FILES.json` inside the ZIP lists every installed mod path,
size, and SHA-256. For removal, close the game and remove only those files if
they still belong to this version, then restore your pre-install save. Do not
remove shared framework files or unrelated mods. Removing files does not undo
changes already stored in a saved game. There is no tested downgrade guarantee.

Report bugs through the repository's Issues tab with the release version,
framework versions, steps, and relevant logs. Avoid attaching personal saves or
private data to a public issue.
