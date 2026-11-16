# Post-Tower main-world Johnny removal

11 November 2026. The staged candidate applies the seven encounter and conversation routes traced in the [main-world audit](../johnny_main_world_audit_20261111_01/MAIN_WORLD_JOHNNY_AUDIT.txt) to QP2 with the quest snapshot cutoff repair. It suppresses seven Johnny bark dispatches and removes seven Johnny speech events and one direct V reply.

| Route | Change |
| --- | --- |
| Murk Man Returns Again Once More Forever and Dressed to Kill | Skip Johnny's spawn and bark after the native vehicle trigger. Both vehicles retain their immovable setup and map-to-objective handoff. A phase already past Johnny's spawn uses its native cleanup when it reaches the new guard. |
| Little China and Northside cyberpsycho sightings | Bypass the Johnny-only scene calls. The scan and clue branches retain their own conditions and audio, including V's separate Little China clue bark. |
| Wellsprings cyberpsycho sighting | Route the three exposition entries through a private scene after the Tower. The onlooker line, fight signal, and other scene entries remain connected. |
| El Capitan's dam briefing | Route the briefing and subsequent interaction through a private scene after the Tower. Cut five Johnny lines, disable his presentation, and shorten the briefing's choice wait by 6.186 seconds. V can still ask Muamar about his behavior and the NCPD. Those choices lead to Muamar's account of the poisoned water and the truck job. |
| Yoko's MaxTac shard exchange | Remove both Johnny lines and V's “They'll have to get in line.” Leaving the shop rejoins the existing completion and interrupt-cleanup path, with the parallel shard condition retained. |

The Passenger's ordinary ride-along owner already retires during the Tower. The installed world routes reviewed for this change had no re-entry for it. The earlier audit also confirmed silent post-Tower Shape of a Pony scenes.

## Candidate verification

All nine changed or added resources cooked and read back. The six native quest phase patches preserve the original node payloads and use PostTowerFreeRoamActive to select the new paths. The false branches reconstruct the original edges. The scene checks preserve all other speech events, choice options, and reachable exits. The courier's private scene returns the original briefing and police-car signals.

The archive contains 1,737 members. All retained member hashes, 11 provider keys across 134 installed archives, and the 54 ArchiveXL configurations passed the checks. The staged package contains all 51 Core paths and changes only the combined archive. Its other files match the installed snapshot cutoff baseline, including the snapshot script. [Verification](verification.json) · [Staged archive](candidate_02/package/archive/pc/mod/zzzz_PTFR_Combined.archive)

Installation and gameplay validation are pending. Existing saves with an already-running native briefing or exposition scene have unverified transition behavior. The audit's 16 numeric stock scene providers still lack resolved callers. A scan of the current combined graph resources found no direct references to those keys. Independent third-party content is outside this build's coverage.
