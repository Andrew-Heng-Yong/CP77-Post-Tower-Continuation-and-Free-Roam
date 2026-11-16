# KOLD MIRAGE marker and encounter repair — KM1

KM1 is installed over the JP1 pilot. It allows `mq016_active=0` or `1` in KOLD MIRAGE's two private entry guards and the matching S29 script range. Its original quest setup then owns both the undiscovered POI and freezer approach/scan wait. Installation and gameplay status are recorded separately below.

## Cause and bounded evidence

The user confirmed a pre-ending baseline with `mq016_active=1`, the seven other queried MQ016 facts zero, and the quest and queried objectives Inactive. Approaching Dexter's body then produced Johnny and started the encounter. On the post-Tower fixture the matching approach did nothing and the marker was missing. The installed S29 diagnostic reported common startup ready, private Issued/Entered both zero, and rejection of `mq016_active=1` because it expected zero. These observations are preserved under JP1's `observations/`.

Fresh extraction checked 134 installed archive indices and found one provider for each of the twelve queried resources. Vanilla sets the active flag before waiting for discovery. The original owner descends from `[0,2,82,6,5]`; the Tower journal success route reaches the containing main-game phase's terminating output. In separately pinned historical bodies, six original KOLD MIRAGE handlers were retained before cleanup and none remained in the later post-Tower event registry or freezer. This is source and historical owner evidence, not an exact live-owner inspection of the user's current save. [Review](analysis_01.json) and [providers](source_01/providers.json).

## Exact change

Only private entry nodes `65003` and `65004` gain the equivalent `active=0 OR active=1` predicate. Every other condition remains, including all 63 Inactive quest journal entries, the seven other zero MQ016 facts, private ownership receipts and existing common/support gates. S29's `FactMax0` changes one array value from zero to one. Its minimum stays zero, so negative or larger values remain excluded. Its baseline/history checks and two settled samples remain unchanged.

All graph nodes, edges, saved identities, registrations and original prerequisite waits remain. The existing native prefix sets the already-required active flag exactly to one, acquires the existing shard/freezer prefab scopes, disables premature cyberdeck pickup, activates the native POI and arms the original encounter waits. This normal prefix grants no items, currency, achievements or rewards. Later pickup, Nix, outcome, reward and cleanup routes remain native. No independent marker writer, forced start, fact reset or new controller is introduced.

The candidate keeps all three JP1 scene resources byte-identical. Its 25 Johnny and 12 V cuts and four menu-option bypasses remain. All other archive resources, scripts, XL registrations and external mods are retained. Prepared KOLD MIRAGE states with active objectives or any other recorded progress still defer.

## Verification

- Cooked resource readback passed 357 checks, including exact independent predicate reconstruction, positive 0/1 cases, out-of-range rejection, every retained progress guard and complete source/package delta checks.
- All 148 registered REDscript sources and 151 installed compiler inputs passed a fresh isolated compilation. Installed compiler inputs were unchanged.
- All 1,581 packed resources were extracted and hash-checked: exactly one private entry differs from JP1, with 1,580 payloads retained.
- The full 51-path developer ZIP was reopened and every member hash checked. Only the archive and S29 script differ; there are no new depots or ArchiveXL phase IDs.

Transaction fixtures and actual installation have their own receipts. Gameplay remains pending; no game was launched and no save was written by the agent. [Test card](TEST_CARD.md).

## Installed result

The closed-game transaction replaced exactly the archive and S29 script. Preflight, installation, post-install verification and rollback readiness passed. All 51 Core paths and 26 dependencies verified, with all 313 saved files and unmanaged game metadata preserved. The exact JP1 archive and script recovery copies are ready. Twenty-seven fixture actions across ten isolated roots covered full Core51 install/rollback, interrupted first and second replacements, recovery, game-running refusal and unknown-file refusal. No real rollback, save write or game launch occurred.

Current archive SHA256: `37974E1E5798FDAE06A5CA17B54A6B41E329E8ED4CFBA14ED27550645AD7FF1B`. [Installed manifest](deployment_01/installed_manifest_01.json), [preservation verification](deployment_01/verification.json), [transaction fixtures](fixture_results.json) and [test card](TEST_CARD.md). Gameplay is pending.
