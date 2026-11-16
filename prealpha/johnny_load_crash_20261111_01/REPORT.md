# Manual Save 26 load crash repair

Installed on 11 November 2026 as `QP2_JOHNNY_LOAD_REPAIR` over `QP2_REED_CRASH_AND_JOHNNY_WORLD`. The repair replaces `PTFR_JohnnyVoiceJV1.reds`. [Installed manifest](deployment_01/installed_manifest_01.json)

## Crash trace

The user reported a crash while loading Manual Save 26. The crash report at 17:22:09 Toronto time contains a save with the same SHA256 as the live Manual Save 26. The executable faulted on a null write at `Cyberpunk2077.exe+0x196a0b8` while initializing an array element. The VM frame resolves to `JohnnyVoiceJV1.Register` from `OnGameAttached`. Its array destination is the actor registry in `ArrayPush(this.actors, actor)`. [Crash evidence](crash_evidence.json) · [RED4ext stack layout](https://github.com/WopsS/RED4ext.SDK/blob/master/include/RED4ext/Scripting/Stack.hpp) · [RED4ext function layout](https://github.com/WopsS/RED4ext.SDK/blob/master/include/RED4ext/Scripting/Functions.hpp)

NPC attachment appended to the registry, the timer could erase entries and system detach cleared it. The dump identifies the failed append. The exact sequence of overlapping operations is unknown.

## Repair

Actor registration, visibility polls and restore scheduling now enter the same scriptable system request queue. Registration and polling handlers own the registry writes. Detach invalidates scheduled polls by advancing the generation, and polling prunes expired weak references. The existing completed-Tower condition still gates hiding Johnny. The replacement adds request types and reuses the existing runtime fields. [Source diff](source.patch)

## Verification

The exact 148-source registry compiled offline. Ten fixture actions exercised install, readback, rollback, interrupted replacement recovery and running-game refusal. Closed-game preflight and installed readback verified 51 Core paths and 26 required dependencies. The before and after save tree hashes match across all 316 save files. The combined archive and the rooftop repair script match the predecessor hashes. The rollback copy of the replaced script verified. [Compile result](compile_01/result.json) · [Transaction fixtures](fixture_results.json) · [Installed readback](deployment_01/verify.json) · [Rollback readiness](deployment_01/rollback_readiness.json)

Gameplay validation is pending. Load Manual Save 26 first. A successful load covers the reported failure point on that attempt. Reed’s rooftop call and snapshot export remain separate checks after the load.
