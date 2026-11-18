# Red Hot Tools RC7 installation — 16 November 2026

Installed **Red Hot Tools v1.3.0-rc.7**, including the CET overlay and World Inspector, at the user's request: “if yes, install it pls”. Installation completed at 15:44 UTC (10:44 Toronto). The game and REDlauncher were closed. No game launch or save edit was performed.

The author added Cyberpunk 2077 2.5 support in [v1.3.0-beta.13](https://github.com/psiberx/cp2077-red-hot-tools/releases/tag/v1.3.0-beta.13). The selected [RC7 release](https://github.com/psiberx/cp2077-red-hot-tools/releases/tag/v1.3.0-rc.7), published 15 November, fixes sector data for v62. Its asset `RedHotTools-1.3.0.zip` includes both the native plugin and overlay; the separate VS Code extension was not installed. The installed game reports version 2.5, with RED4ext 1.31.0, CET 1.38.0, Codeware 1.21.1 and ArchiveXL 1.28.0.

The official GitHub release API supplied asset ID 752317148, size 2,423,642 bytes and SHA256 `EE58F5BB33BF9B650A8D49670CF3BA279D6F8559C0BC3DB85417AF84CD4B7BB2`. Download size, SHA256, ZIP CRC, member paths and staged readback passed. Its 18 files comprise 16 Lua sources, the x64 DLL and resource index. No REDscript or archive payload is added.

Only these previously absent folders received files:

- `red4ext/plugins/RedHotTools`
- `bin/x64/plugins/cyber_engine_tweaks/mods/RedHotTools`

All 18 installed file hashes verified. Exact before/after checks preserved the 51 KM3 Core files, 26 existing dependencies, RED4ext loader and CET bindings. All 436 save files retained their names, sizes and SHA256 hashes. Unmanaged game-file names, sizes, timestamps and reparse metadata also matched. The Tower installation remains **KM3_KOLD_PREPARED_ENTRY**. Old held copies remain outside the game.

The new installer adapts the reviewed KM3 transaction into this fresh workspace. Ten isolated fixture cases passed across 25 actions: installation and rollback, automatic recovery at three points, hard interruption recovery at three points, running-game refusal, occupied-folder refusal, and preservation of an unexpected changed target. The clean rollback fixture also preserved a newer user save and runtime-created preferences. The exact official package was used. Real closed-game preflight, installation, separate verification and rollback readiness all passed.

The [installed manifest](work/installed_manifest_01.json) records exact tool files and preserved dependencies. [Installation receipt](work/installation_01.json), [verification](work/verification_01.json), [rollback readiness](work/rollback_readiness_01.json), [fixture results](work/fixture_results.json) and [scope review](work/scope_review.json) remain local evidence. Bulk binaries, fixtures and recovery files are ignored by Git. Nothing was pushed or published by this task.

Native startup, save loading with this tool and in-game inspection remain **unqualified**. On the next game launch, open CET → Bindings and assign **World Inspector: Toggle overlay** under RedHotTools. Existing bindings were preserved; no hotkey was assigned automatically.

File rollback is prepared through `work/install.ps1` and `work/recovery/redhottools_01`. It removes only the 18 matching installed files after closed-game, receipt and preservation checks; it retains unknown files and runtime preferences. A future rollback requires its own instruction and does not undo saves. No real rollback was performed.
