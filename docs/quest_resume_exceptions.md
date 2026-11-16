# Mid-quest resume exceptions

Record exceptions when preserving an interrupted state is impractical or the implementation would risk losing progress, duplicating ownership or rewards, or disrupting the ending. Scope each entry to the affected stage or branch where possible. Use a whole-quest exception when the blocker applies across the quest or safe support for the quest is impractical.

The final 15 November selection limits new implementation to earned items waiting for collection, travelling somewhere or waiting to talk, simple timers, and multiple unfinished objectives. All other interruption stages are omitted, including pending texts/read/replies and call handoffs, mid-call/scene playback, active encounters and unresolved equipment or reward transfers. An inseparable excluded branch also excludes its cooperating handoff, even if another node is a timer or parallel objective. Existing reviewed adapters and ordinary future quest progression retain their existing behavior. [Selected scope and omission notes](mid_quest_resume_four_types_20261115.md)

An unsupported state follows normal Tower cleanup and may remain unavailable after the ending. A previously reviewed stage fallback may still apply when its own conditions pass. Eligible fresh starts follow their existing prerequisites. Exclusion does not authorize a rewind, forced completion or reward replay. Unknown states also defer, but should remain labelled unknown rather than counted as proven difficult-stage exclusions.

**New scoped omission, 15 November:** Over the Edge (`mq049_edgerunners`) at the Falco/Reyes pending message handoff is outside the implementation and playtest queue. Preserve the recorded v0.1.10 result and player progress. This does not exclude every later earned collection stage of that quest; such a stage needs separate qualification. [Recorded handoff and missing message](../prealpha/universal_resume_native_registration_20261115_01/observations_01/REPORT.md)

## Whole-quest exceptions

| Quest | Native journal ID | Post-Tower availability |
| --- | --- | --- |
| Go Your Own Way | `wst_ep1_05` | Can start after The Tower if you haven’t started it and meet the quest’s prerequisites. |
| Where Eagles Dare | `mq058_semimaru_crystalcoat` | Can start after The Tower with unused quest history, earned Claire race and Motorbreath outcomes, and the native Semimaru trigger. |
| New Person, Same Old Mistakes | `wst_ep1_11_bill_meeting` | The existing start uses unused quest history and the earned Waiting for Dodger outcome. Keep the native wait, location gate and Bill’s vendor ownership checks. [Bill’s graph and owners](../prealpha/quest_restoration_qr5/groups/G16/quests/wst_ep1_11_bill_meeting/contracts.json) |
| The Show Must Go On | `sts_ep1_08_steven_meeting_night_city` | The existing start uses unused follow-up history and the qualifying Spy in the Jungle outcome. Reading Steven’s invitation enables the native encounter and its reward. [Steven’s invitation and encounter](../prealpha/quest_restoration_qr5/groups/G15/quests/sts_ep1_08_steven_meeting_night_city/contracts.json) |

On 14 November 2026, Go Your Own Way was removed from the mid-quest resume development and playtest plan because setting up its pending Mr. Hands reply was impractical. Its original phase, phone choices, and post-Tower entry are documented in the ownership trace. [Ownership trace](../prealpha/universal_resume_owner_20261114_01/REPORT.md)

On 14 November 2026, Where Eagles Dare was removed from the mid-quest resume plan, including Claire’s pending post-completion reply. Manual Save 26 already records the completed job and the CrystalCoat upgrade. The reply still had a running game-time timer, and the inspected post-Tower saves lost its original reply listeners. The workspace candidate is retained as timer and ownership evidence. The Manual Save 26 ending and reload test is retired. [Saved reply and original owner](../prealpha/universal_resume_eagles_20261114_01/REPORT.md) · [Fresh-entry prerequisites](../prealpha/quest_restoration_qr6/groups/B01/quests/mq058_semimaru_crystalcoat/REPORT.md)

The 14 November 2026 decision also defers mid-quest resume for Bill’s and Steven’s follow-ups. Bill’s 32-in-game-hour wait, outcome-dependent scenes and vendor ownership need a coordinated handoff. Steven’s 66-in-game-hour invitation, separate actor controller and encounter reward need to carry over together.

## Stage and branch exceptions

Confirmed on 14 November 2026. Other stages of these jobs remain candidates only where they fit the four types selected on 15 November. The scope decisions use native graph and dependency evidence. Live behavior through The Tower requires separate verification. [Source registry](../prealpha/quest_resume_registry_20261112_01/README.md)

| Quest | Native journal ID | Deferred state | Progression to preserve |
| --- | --- | --- | --- |
| Dogtown Saints | `sts_ep1_01` | Mr. Hands’ post-debrief Anderson replies and their expiry after three in-game hours and an area-exit check. | Preserve Anderson’s outcome, the debrief reward and gig credit. [Native debrief and cleanup](../prealpha/quest_restoration_qr5/groups/G21/quests/sts_ep1_01/REPORT.md) |
| The Man Who Killed Jason Foreman | `sts_ep1_03` | Mr. Hands’ optional reply after the Rinder debrief and its one-in-game-hour expiry. | Preserve Rinder’s separate garage-code history for **Addicted to Chaos**. [Gig cleanup and phone paths](../prealpha/quest_restoration_qr5/groups/G20/quests/sts_ep1_03/contracts.json) · [Garage-code dependency](../prealpha/quest_restoration_qr5/groups/G16/quests/wst_ep1_04/contracts.json) |
| Prototype in the Scraper | `sts_ep1_04` | Optional debrief replies and their 22-in-game-hour expiry check. | Preserve the gig outcome and earned Hasan follow-up state. [Hasan cleanup](../prealpha/quest_restoration_qr5/groups/G21/quests/sts_ep1_04/REPORT.md) |
| Roads to Redemption | `sts_ep1_07` | Optional debrief replies and their 22-in-game-hour expiry check. | Preserve the gig outcome and the separate Nele activation for **One Way or Another**. [Nele cleanup](../prealpha/quest_restoration_qr5/groups/G21/quests/sts_ep1_07/REPORT.md) |
| Sweet Dreams | `mq036_overload` | The window between confiscation and recovery of V’s gear. | Preserve original inventory escrow and recovery receipts. Replaying the sequence can take gear again or lose track of the items. [Inventory and scene boundaries](../prealpha/sweet_dreams_sd1/REPORT.md) |
