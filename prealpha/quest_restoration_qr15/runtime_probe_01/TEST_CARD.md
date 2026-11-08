# JF01 — one read-only prepared-state observation

Run this once on the current working branch used after Jeopardy. The exact loaded slot is not independently established; do not substitute the untouched ManualSave-23 master or an older branch to manufacture eligibility. No quest replay, save/reload test, travel, conversation, combat or quest start is requested. Stay where the working save loads.

1. Launch the game manually if needed and load that current working save. Wait for the loading/setup cover to finish and normal player control.
2. Open CET. Paste the **entire single line** from `facts.command.txt`, press Enter once, then do the same with `world.command.txt`. The self-contained chat response also contains both exact commands. No mod installation, logger command or game restart for a diagnostic update is needed.
3. Expect `[JF01-F] BEGIN`, eight named readings and `END`. The world command prints `[JF01-W] BEGIN`, two community results, one broken-car spawner result and `END`. Values are evidence, not target settings: do not change anything to match a value.
4. `LOAD_SAVE_FIRST` or `WORLD_NOT_READY` means no valid world sample. A line containing `ERROR`, `UNRESOLVED` or `TRUNCATED` is also useful: preserve it and do not treat it as zero, inactive, absent ownership or a broken quest. No retry loop is requested. In particular, the native short NodeRef aliases may fail global/context/streaming lookup.
5. Exit the game normally when finished so its existing log can flush. Report **JF01 done**, and mention any error. No new save, reload or rollback is required by this observation. Codex will collect the printed output automatically; no screenshot or manual fact transcription is needed.

The preparation may start an external bounded GG1 capture; its exact active run is selected by `prealpha/general_gig_probe_gg1/active.json`. The user does not operate that process. Existing CET printing writes the source log at:

`C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\bin\x64\plugins\cyber_engine_tweaks\scripting.log`

## Purpose and limits

The earlier55fact snapshot omitted the shared courier-control fact. Its actual value affects whether a candidate continuation could repeat an already served side branch or interact with existing courier cleanup. Readings from Codeware's existing community/spawner wrappers add current world state beyond scalar facts. They can help design admission/skip/hold rules for native startup without blindly reapplying it. All-zero or inactive-looking output does **not** authorize a repair by itself.

These are two one-shot read commands. They register no callback, hook, timer or update loop and never activate/deactivate/reset a community, set a fact or invoke a quest node. Community enumeration is confined to two exact native references and64entries each; Codeware materializes the selected community's full entry list before the Lua loop limit. The spawner query uses one exact native reference. No global world census occurs.

`UNRESOLVED` does not distinguish unloaded, inaccessible, unregistered or differently scoped references. Positive entry/spawner results do not enumerate the native/private quest-owner tree, saved pending nodes or prefab leases. The exact owner transition remains a separate source/engine question. Do not promise that this sample alone proves a safe adapter or all save compatibility.

## Offline readiness

`validation_01.json` records23bounded syntax/control/API checks and77current installed hash checks. The commands were compiled/executed offline under LuaJIT using reader doubles, not real Game calls. Controls cover a detached/missing player, unready/missing APIs, unresolved aliases, read errors without fabricated zero, nonzero values, enumeration limit and a deliberately substituted mutator caught by a tripwire. Real Lua-to-native getter delivery is pending the human run.

Installed `Codeware.Global.reds` declares the exact methods and native `CreateNodeRef(script_ref<String>)`. The currently compiled PTFR_RestorationBaseline already uses GetWorldStateSystem/GetCommunity/GetEntries/IsActive. Matching local C++ implementations are corroborating source: getters look up existing objects/read state, whereas mutators are separate functions. This is not a full binary-body equivalence claim. The exact installed DLL/script and source hashes are pinned in validation_01.json.

CET's Game binding resolves both GameInstance members and globals; its console print implementation writes to `scripting.log`. [Pinned upstream source](https://github.com/maximegmd/CyberEngineTweaks/blob/b160d68cf923f2535cb3a6ebe006de86ef21e359/src/scripting/Scripting.cpp#L99-L115), [Game lookup](https://github.com/maximegmd/CyberEngineTweaks/blob/b160d68cf923f2535cb3a6ebe006de86ef21e359/src/scripting/Scripting.cpp#L612-L640). These corroborate the interface, not full installed-ASI equivalence. No special NodeRef constructor name or hidden quest-owner API is guessed.

Original QR15 source findings and no-repair disposition remain immutable. This new, user-requested partial world-state observation supplements their interface boundary; it does not retrospectively mark owner/lease state observed.
