# Ordinary mirrors C3: opt-in live test

Built and installed 2026-09-24 with Cyberpunk 2077 closed. This is a disposable-save test package, not a claim that all ordinary mirrors are working. It adds 25 mod-owned quest/scene owners with exact vanilla trigger sectors. It does not replace vanilla resources, change story facts, or modify a save. `PTFRBM_Enabled` defaults to 0, so the new owners wait until explicitly armed. The working H10, Afterlife, and public El Coyote packages remain installed unchanged.

The 25 sites are vanilla controller leaves 5, 8, 21–23, 25–36, 38–41, 43–44, 49, and 63. Their owner leaves have one Inside trigger, one scene, and one-second rearm; their scene exits use the same trigger and their scene files only read `mirror_interactions_facials`. C3 qualifies each local entry/exit NodeRef to the exact vanilla world trigger. Build validation round-tripped all 75 CR2W resources and the packed archive, checked all 25 prefab/trigger matches and scene exits, and found no registration ID collision with 90 game-side quest registrations. `research/b0_mirror_rollout/validation_c3/build_manifest.json` is the exact installed inventory.

The other simple-shaped leaves are not silently included: Coyote is already C2; Randy's trailer and Red Dirt read additional story facts; Peralez penthouse, Konpeki, and Sunset are story/ending interiors; Police Lab and V's penthouse have different leaf layouts; Sunset Single has no matching world trigger descriptor; Joss's trailer and Kerry's villa have 52-node scenes in relationship homes. H10, Afterlife, the Streetkid prologue surface, Corpo Plaza apartment, and the eight non-simple controller leaves are separate workstreams.

## One short test

1. Load a disposable post-Tower save. Do not save during this test. At the Riot nightclub in Little China, stand outside its mirror area and out of combat/scene/workspot.
2. In CET run `GetMod("PTFR_OrdinaryMirrors_C3").Start(22)`. This starts flushed logging and writes only `PTFRBM_Enabled=1`.
3. Enter the mirror area. Test Look, one facial expression, and Stop. Leave the mirror area, then enter and repeat once. If the prompt or any action fails, stop the test; do not force story facts.
4. In CET run `GetMod("PTFR_OrdinaryMirrors_C3").Stop()`. This flushes the log and clears `PTFRBM_Enabled`.
5. Quit without saving and report whether the prompt appeared and all three actions worked on both visits. The JSONL log is in `bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_OrdinaryMirrors_C3/`.

Success for the first site requires the physical actions plus native `PTFRBM22_Requests=2`, `PTFRBM22_Returns=2`, `PTFRBM22_Active=0`, and no unexpected interruption. Do not infer that the other 24 sites are live-validated from this result alone. A second representative site and reload check precede default activation.

## First five-site physical sample

The tester reports that all five teleported sample sites (Riot, Piez, Claire's garage, Fingers, abandoned motel) showed working mirror actions. The run intentionally/incidentally teleported while a mirror dialog remained open; it did not perform a clean leave/re-entry at each site. The durable log `ordinary_mirrors_c3_20260924T155300Z_0001.jsonl` recorded 194 flushed rows. Riot reached one native request and one return with Active=0 and Interrupted=0. The logger only counted Riot; the other four reports are physical observations, not native-counter proof. At Stop, V was still `scene=true` and `workspot=true` after the mid-dialog teleports. This is not proof of a normal cleanup failure, but it prevents using this run as save-safety or natural-exit validation. The tester quit without saving.

The second, clean Riot run `ordinary_mirrors_c3_20260924T160217Z_0001.jsonl` records one normal request and one return, Active=0, Interrupted=0, and V out of both scene and workspot at Stop. The tester clarified that this run included only one completed visit; the Look prompt remained visible afterward. It does not establish a second native cycle.

Automatic C4 was then installed with the game closed. C4 has the same 25 site IDs and Tower guards but removes the `PTFRBM_Enabled` opt-in gate; no CET command is needed after loading a post-Tower disposable save. The installed C3 archive, XL registration, and logger were moved to `build/OrdinaryMirrors_C4/c3_installed_backup` for rollback. No vanilla file, save, or story fact was changed. Multi-site reload behavior and fresh-transition integration remain untested; C4 is a guarded beta rather than a finished all-mirror release.

## C4 automatic smoke result

After installing C4 with the game closed, the tester loaded an older disposable post-Tower save that predated the El Coyote mirror activation. No C3 CET arming was needed. The tester reports using the Riot mirror twice successfully. No before/after native counter output was supplied, so two C4 native request/return cycles and final workspot state are not independently logged. This is a physical two-use pass for automatic activation at one representative site, not validation of all 25 locations or of a fresh natural Tower transition. The tester asked that this be the final manual mirror test; do not request further mirror tests in this workstream.

During the same visit, the tester observed NPCs in the Riot bar standing idle. Record this as a separate world-population/ambient-behavior observation for later Phase 4 service/NPC work. The observation does not establish whether C4 caused it; do not change the mirror package or restart a bar/story root based on this alone.

Later save-state correction (2026-09-24): the tester reports that none of the available manual saves, including Manual Save 13, currently have working world mirrors. This is not reconciled with the earlier two-use Riot report. The installed C4 archive hash still matches the reviewed automatic build, so the next step is a read-only check of C4's post-Tower guard facts and a specific missing mirror on the loaded save. Do not assume a past save contains C4 state, force `PTFRBM_Enabled`, or combine an unverified mirror state into a new vendor test save.

Follow-up: the tester loaded a **later autosave** and confirmed a working world mirror there. This resolves the immediate choice of fixture for a combined vendor+mirror persistence trial, but not why older manual saves lack prompts; the exact mirror site, save slot, and native counters were not supplied. Use the later autosave only as a disposable source, then create a new manual test slot outside all interactions. Do not describe C4 as save-independent across every historical fixture.
