# Side-job entry and phone/message audit — preparation

26 October 2026. Read-only audit preparation. No game, installed mod, save, quest fact, or release changes.

**Audit completed across all 81 restored sidejobs:** see [the results and full per-job matrix](sidejob_entry_phone_audit_20261026.md). That audit found a consolidation resource-selection regression which discarded parts of earlier Dennis, Delamain, service and cleanup repairs. The preparation table below records the expectation before that discovery; its repaired-status assertions must be read with the newer results. Existing CET log copies also now preserve the Raymond captures.

## Reproduced Raymond Chandler Evening issue

The user's pre-ending capture shows `sq018_done=1`, journal `mq040_biosculpt=Inactive`, `mq040_active=1`, `mq040_done=0`, `mq040_pepe_intro=0`, and `elcoyote_barman_default_on=0`. The post-ending capture still shows the last four values, with the S29 diagnostic `Ready=1`, `Permit=0`, `Issued=0`, `Entered=0`, `Fault=0`, `baselineFresh=true`, `currentMatch=false` (`mq040_active=1 expected=0`). The B0 Pepe service has `Ready=1`, `Enabled=0`, `OwnerActive=0`, `Entries=0`, and `SceneRequests=0`.

**Issue statement:** A save can reach the Tower with Raymond's native `mq040_active` reservation and Pepe's default service disabled while the quest journal root remains inactive. After the ending, S29 treats the historical root as fresh but rejects the current nonzero quest fact, so it does not issue its native entry. The separate Pepe service also cannot enable while `elcoyote_barman_default_on=0`. No PTFR owner has claimed the quest or bar service in the captured post-ending state. The saved original MQ040 phase's liveness has not been established; `mq040_active=1` alone does not prove that it still executes. S29's `safe=false` is an additional player-state gate, but the fact mismatch remains independently decisive.

This is an **initiation/owner handoff problem**, not a missing MQ040 phone controller. S29 includes scoped Pepe and Cynthia controllers for later calls. Do not clear `mq040_active`, turn the default service on, or issue a second quest owner without proving the old owner's state and its cleanup/reward obligations.

Sources: [Coyote native graph audit](../research/coyote_sidejobs_audit/assessment_01.json), [S29 fresh observation and Inspect](../prealpha/sidejobs_s29/runtime_06/SideJobsS29.reds), [Pepe service driver](../redscript/PTFR_B0_StoryServices/StoryServiceDriver.reds), [B0 service assessment](../research/b0_story_services/assessment.md). User screenshots in this chat are the live evidence; they are not copied into the repository.

## Similar mechanisms to distinguish

| Mechanism | Existing evidence | Audit disposition |
|---|---|---|
| Historical journal root inactive, native setup fact already set | Raymond live capture | Confirmed gap on this save. Identify native saved owner before repair. |
| Phone request writer exists but no restored listener/cleanup | Prior static audit found Karl Ginsky in Nasty Hangover, Pedro Aimar in Desperate Measures, Mark Bana and Janet in Spy in the Jungle | Four contacts across **three gigs**, outside the 78 selected side-job roots. Source-confirmed omission, live consequence untested; include as adjacent phone cohort. |
| Conditional service phone return without controller | Nix and Viktor private-service returns | Source gap, but not proof that KOLD MIRAGE, Spellbound, or Paid in Full cannot start or finish. |
| Initial or follow-up message rejected as supposedly nonfresh | Earlier Delamain/Epistrophy finding | SR1 removed the seven incorrect predecessor-message Inactive checks and repaired shared phone-controller adoption. Installed in the consolidated build; targeted route/reload validation remains useful. Do not report the old source finding as an unfixed installed bug. |
| Call requested but no notification | Dennis in Big in Japan | JD1 added native controller/cleanup support and is included in consolidation. User reports previous fixes worked, without a route-by-route audit log here. Regression control, not an open omission. |
| Call/text expected only after original outcome, delay, location, or choice | Many vanilla owners | Do not treat absence alone as a mod defect. Compare original prerequisites, messages, journal, and owner receipts. |

The [earlier phone-request census](../diagnostics/restored_audit_20261025_01/phone_audit_01.json) checked 51 explicit request facts and found six listener gaps: the four gig contacts and two conditional service contacts above. It does **not** certify SMS delivery, all dynamic phone calls, or live timing. S29's six phone-dependent job owners have scoped support for Kirk, Nancy, Blue Moon, Pepe/Cynthia, Rachel, and Delamain; controller presence is not gameplay proof. [S29 prepared ownership](../prealpha/sidejobs_s29/prepared_04/prepared.json).

## Side-job candidate groups for the next pass

These are **audit targets, not newly confirmed failures**. Separate a start contact from a call or message used later inside an already active quest.

1. **Early call/contact routes:** The Beast in Me (Claire bootstrap), War Pigs (Frank), Send in the Clowns (Ozob), Small Man, Big Mouth (Kirk; user's failed post-ending branch is intentionally excluded), Killing in the Name (Nancy), Every Breath You Take (Blue Moon), and Don't Lose Your Mind (Delamain follow-up). Verify original parent gates, controller/cleanup, request/ack, journal transition, actor availability, and actual notification. [A-cohort](../diagnostics/restored_audit_20261025_04/cohort_a/per_job_01.json) · [B-cohort](../diagnostics/restored_audit_20261025_04/cohort_b/per_job_29_01.json) · [C-cohort](../diagnostics/restored_audit_20261025_04/cohort_c/matrix_22_02.json).
2. **Message-heavy entry/follow-up routes:** Sex on Wheels (Jake's message and journal), Over the Edge (BD/Falco messages), These Boots Are Made for Walkin', Violence, The Gun, Human Nature/Epistrophy, Claire's race stages, Venus in Furs, and Where Eagles Dare. For each, determine whether a given message **starts** the job, follows a native entry, or is merely later dialogue before classifying a missing popup. The game's [2.3 patch notes](https://www.cyberpunk.net/en/news/51674/update-2-3-patch-notes) explicitly tie Sex on Wheels' journal appearance to Jake's message.
3. **Calls inside a quest or service:** Raymond's Pepe/Cynthia contacts, Big in Japan's Dennis call, Sinnerman's Rachel calls, Full Disclosure's Sandra call, and Nix/Viktor returns. Audit these for progression and cleanup without calling all of them missing *start* calls.

The game's holocall settings can replace muted fixer/NCPD calls with text, and rejecting certain calls also produces text. Check phone history and settings before concluding a notification was lost. [CDPR patch 1.5 notes](https://www.cyberpunk.net/en/news/41435/patch-1-5-next-generation-update-list-of-changes).

## User-reported side-job map drop: 19 undiscovered before, 8 after

The user clarified that both counts refer to **yellow undiscovered side-job markers**, not fixer gigs. This is a reported 11-marker difference, not yet an identified list of 11 lost quests. Keep only suspected restoration defects in the cause list below:

| Suspected defect mechanism | What would distinguish it |
|---|---|
| A quest root remains Inactive while its separate POI/map-pin entry is no longer activated after the Tower handoff | Compare the exact journal root, child map-pin/POI state and registered mappin for one missing marker across the same save lineage. |
| A restored entry is ready/requested but its original parent or map-entry node never runs | Compare PTFR Ready/Permit/Issued/Entered/Fault with original parent-entry receipt and native marker writer. A request is not proof that the parent reached its marker stage. |
| A saved partial native quest state is misclassified as fresh by a root-only snapshot, then rejected by current-state checks | Raymond is the observed example: Inactive root, `mq040_active=1`, S29 `baselineFresh=true` but `currentMatch=false`; look for this pattern in other missing jobs. |
| A shared admission safety check stays false during ordinary settled gameplay | The Raymond screenshot had S29 `safe=false`. Recheck after normal idle, with weapon holstered and no scene, combat, menu, vehicle, workspot or transient status. A transient false result is not itself a defect. |
| A required initiation call or text is requested but its controller, acknowledgement, journal transition or cleanup does not execute after the ending | Inspect the original producer, restored listener, start/end/cleanup receipts and actual phone history for each missing marker. Do not infer this from a missing popup alone. |
| A native or PTFR marker exists in memory but fails to render as the side-job icon | Compare journal quest/POI hashes, marker registration, active/visible flags, phase and actual map rendering. `IMappin.IsVisible()` alone is not rendered-icon proof. [Marker diagnostic distinction](../prealpha/postending_pa5/gigs/GigDiagnosticsPA5.reds). |

For the count comparison, control for the same save lineage, map category, zoom and timing, then record the missing markers' names or coordinates. Those controls are **not** listed above as suspected mod defects. The earlier [78-job audit](../diagnostics/restored_audit_20261025_04/combined_78_01.json) verified selected entry bindings but did not certify 78 rendered map pins or replay every saved entry state.

## Read-only audit method

For each of the 78 selected side-job roots, record: original entry channel and producer; prerequisite story/choice/lifepath/time/location; pre-ending and post-ending root plus relevant child journal states; current versus frozen native facts and message history; PTFR `Ready/Permit/Issued/Entered/Finished/Fault`; phone request, start, end and cleanup acknowledgements; actor/service lease; and actual call/text, map, journal and world behavior. Use the same save lineage and distinguish pre-ending origin from the accepted post-ending fallback snapshot. An inactive root does not establish a fresh native owner. A request or receipt does not prove that a visible call or quest played. Completed/failed histories must not be reset to manufacture eligibility.

Start with Raymond and a few controls: one genuinely fresh phone-start job, one message-start job, one completed job, and the installed Dennis/Delamain repairs. Then extend the same checks across the [78-job audit matrix](../diagnostics/restored_audit_20261025_04/combined_78_01.json). Preserve the existing 51-file consolidated install layout for any later fix; this document authorizes no implementation or installation.
