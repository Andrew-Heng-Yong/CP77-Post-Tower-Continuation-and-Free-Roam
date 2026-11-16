# Batch 3 returned notes review

9 November 2026. The six quests with cut notes leave **eight Johnny lines** unlisted. Losing My Religion also leaves **three V lines and one conversation option**. The blank car quest contains **two more Johnny lines**. I treated the four whole-exchange descriptions as covering their alternate spoken branches. All fourteen quoted anchors matched source events.

## Bullets

| ID | Where | Johnny |
| --- | --- | --- |
| B3-01 | Cyberpsycho attack, before the later conversation | “Fuck, V! Get down! He's whacked!” |
| B3-02 | Immediately after V says “Can hear you, remember?!” | “How could I forget.” |

The five quoted cuts cover the other three Johnny lines and both V replies in the listed conversation. “Nope. I'm not you” and “Maybe a little…” are answers to Melissa. The attack warning sits in the encounter sequence, which also runs timed callbacks. Johnny's spawn and camera waits need attention if his presentation is removed. Keep the fight, MaxTac response and Melissa's dialogue on their original routes.

**Jinguji.** Vanilla deactivates `#mq030_suit_store_com` during encounter setup (`mq030.questphase`, root/43 node 7), then restores customers and the designer during cleanup (root/64 nodes 56–57). JB1's Bullets wrapper still calls that native phase. The two seated NPCs in the reported overlap have an unverified owner and stage. The native source confirms the intended customer clear and return, while the existing user test confirms the shop works on the tested completed route.

## Losing My Religion / Sacrum Profanum

The rescue commentary in the notes is the nonlethal branch. The alternative after lethal combat has three more Johnny lines and one V reply.

| ID | Speaker | Opening words |
| --- | --- | --- |
| B3-03 | Johnny | “Who knew monks were ungrateful little brats?” |
| B3-04 | Johnny | “Tired of assholes saying there are good and bad people in this world.” |
| B3-05 | Johnny | “Must've made a good one, 'cause why else would karma leave all this sweet gear…” |
| | V | “I like where you're going with this.” |

The epilogue's **“What's your take, Johnny?”** option opens another exchange. The monks' other options have separate routes.

| ID | Speaker | Opening words |
| --- | --- | --- |
| | V | “What's your take, Johnny? You just you... or a copy?” |
| B3-06 | Johnny | “What difference does it make? You heard 'im…” |
| | V | “Maybe Johnny Silverhand really is dead? Maybe you're just an... well…” |
| B3-07 | Johnny | “What, imitation? That what you wanted say?” |
| B3-08 | Johnny | “If the ‘real’ Johnny Silverhand's dead, then that's his problem. Not mine.” |

**[Show middle finger] is vanilla.** The original hook scene attaches choice 134 to Johnny and plays the gesture on its selected output. Your conditional removal applies. The later rescue waits for Johnny to spawn and then waits on camera focus before restoring full player control. Those dependencies matter for presentation removal even with the original rescue and monk outcomes preserved.

## I'm in Love with My Car

The returned section is blank. The installed private opening scene contains these two Johnny lines.

| ID | Where | Johnny |
| --- | --- | --- |
| B3-09 | Warehouse approach | “Hey! Over here!” |
| B3-10 | At the warehouse trigger | “V, try to get inside.” |

The scene's `ContinueQuest` callback activates the investigation objective. The current entries remain review candidates pending your selection.

## Whole exchanges covered by the notes

| Quest | Coverage | Dependency to preserve |
| --- | --- | --- |
| Space Oddity | Six Johnny lines after opening the package, including the moon and art-expert choice branches. | Keep the real package acquisition and the separate completion and cleanup outputs. V's initial “What... what the hell is this?” reacts to the package. The earlier corpse scene also declares a silent Johnny binding, which is a presentation lead. |
| Happy Together | Ten Johnny lines at the Columbarium, including the alternate replies. | Andrew's plaque supplies two of the six dialogue options. Preserve a real plaque interaction, the optional Andrew objective, and both native callbacks when removing Johnny's menus and waits. This is a wiring dependency beyond the “none” in the notes. |
| Spellbound | Five Johnny lines after opening the stash, including the recognition and Nix alternatives. | Keep **[Open]**, **[Take]**, the item grant and the route to Nix. The two opening V reactions describe the stash contents. The native Nix history check and knowledge write need to retain their intended meaning. |
| Violence | Seven Johnny lines in the post-Liam conversation, spanning the cheating and Relic branches. | Keep the earlier Liam confrontation and its choices, the `out_johnny` checkpoint continuation, footage acquisition and Lizzy's call. |

## Whitelist request

The Prophet's Song is recorded separately as your requested exclusion because you reported the scene change prevents playing it. Its whitelist removal is pending. The installed list still includes the existing entry and fresh-route adapter.

## Evidence

The supplied YouTube pages returned fetch errors, so the comparison uses the returned notes and game files. The review captured 71 current resources across 134 archive indices and matched every dialogue scene to its indexed source hash. One older Space Oddity root-phase cache differed. A separate official capture matched the current native bytes, and the reviewed painting exchange uses the installed private scene. The findings record gives exact event IDs, complete matched text and the two option identities. Source paths establish authored branches. Availability and rendered presentation on a particular save remain separate checks. [Exact findings](findings.json) and [provider capture](source_01/manifest.json).
