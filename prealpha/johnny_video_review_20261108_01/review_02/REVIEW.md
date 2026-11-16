# Returned five-quest notes — source review

All 73 quoted note entries match source dialogue after accounting for spelling, ellipses and wording variants. The three repeated “like clockwork” entries collapse to one shared V event. The Raymond arrival narration and “Stop right there” have four connected copies of the same localization records; the proposal covers those copies explicitly.

The source-checked interpretation selects **72 Johnny events, 46 V events and eight dialogue options**. This includes both branches of the exchanges you explicitly requested in full. The other NPC dialogue and device/payment choices remain. The counts are proposed edit targets, not implemented changes.

| Quest | Johnny selected | V selected | Additional Johnny not yet selected |
| --- | ---: | ---: | ---: |
| The Highwayman | 5 | 2 | 0 |
| Small Man, Big Mouth | 5 | 3 | 6 |
| These Boots Are Made for Walkin' | 8 | 5 | 0 |
| Raymond Chandler Evening | 15 | 12 | 6 |
| Killing in the Name | 39 | 24 | 5 |

## What still needs a decision

There are **17 additional Johnny occurrences** and **14 associated V responses** outside the interpreted requests. The [additional-lines file](Additional_lines_to_review.txt) contains their exact source wording. Small Man, Big Mouth has an entire early Johnny conversation before the Kirk meeting, including two reply branches. Raymond has alternate target/approach and ripperdoc-exit narration. Killing in the Name has arrival/ambient bot comments and the other post-quest outcome remark. None is silently added to your selected cuts.

Killing in the Name also has a third outcome hidden behind Johnny-addressed wording: **“Chill. Not gonna ruin your fun.” leaves the bot connected**. Removing that choice outright would drop an outcome. The proposal is to present the same native choice at the bot, with wording such as “Leave it connected”, while removing its Johnny dialogue. Keep the real payment, disconnect and modify choices.

## Rewiring interpretation

- **The Highwayman:** remove the two Johnny exchanges and their speech-only time. Preserve garage/photo inspection, body investigation, clues and bike access. Both selected V lines are honored even where they describe the situation.
- **Small Man, Big Mouth:** after opening the truck, bypass the Johnny talk gate to the original return-to-Kirk continuation. After the gangoons, bypass the final Johnny conversation to the native completion path. Preserve discovery, container/player actions, combat and rewards. The separately omitted early conversation remains a review item.
- **These Boots Are Made for Walkin’:** your notes cover all three Johnny ending branches. Remove their speech-only waits and the shared selected “clockwork” line; bypass the Talk to Johnny objective. Preserve Lana choices, payment, car ownership/unlock and the genuine ending callbacks.
- **Raymond Chandler Evening:** “none” means no requested gameplay sequence rewrite. Remove selected narration/replies and Johnny presentation; preserve Cynthia’s route, following distances/failure handling, investigation, NPC conversations and Pepe outcomes. Alternate narration/replies are listed separately for review.
- **Killing in the Name:** bypass the post-router Johnny talk gates at Brooklyn, solar plant, billboard and the bot. Keep actual router discovery/hacking and the next signal objectives. At the bot, retain V’s **“Wait... What the hell’s this?”**, bot speech, payment and all three device outcomes. Once the native hack/outcome step completes, proceed directly to **Call Nancy** without another Johnny conversation. Nancy’s actual call/acknowledgement and quest completion remain native. “Every dialogue before Go to signal’s source” is scoped to that post-hack Johnny exchange; unrelated earlier clues and Nancy dialogue are not swept into it.

Johnny entity/shadow, digital spawn effects, title/scanner presence, cigarette and smoke remain cleanup targets throughout the affected scenes. An empty remnant field or “none” in that field is not a request to leave Johnny visible.

## Evidence and limits

Fresh capture decoded **41 current private resources** across **134 archive indices**, with exact expected payload hashes and unique providers. Connected phase inputs account for all **89 indexed Johnny events** in these five quest closures. Raw event IDs, line IDs, actor/player bindings and both V subtitle variants were checked. Retained subtitle provider raw/export hashes and exact text pointers were checked. This is structural source qualification, not condition feasibility, saved-owner retirement, world placement or live behavior proof.

The supplied YouTube pages failed direct fetch; no claim of independently watched videos or complete video branch coverage is made. The review relies on your transcription and the game sources. Retiming must retain non-dialogue player/NPC actions and native callbacks rather than setting every edited scene duration to zero.

Your edited file is preserved in [intake](../intake_01/user_notes_received.txt). [Exact review targets and keeps](review.json), [caller evidence](../analysis_01/scene_callers.json), [source capture](../source_01/manifest.json), [verification](verification.json). No game resources, installed files, saves or facts changed. This task reviews the notes; it does not build or install the five-quest change.
