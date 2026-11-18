# Welcome to Paradise dialogue cut

The staged post-Tower tour skips every Johnny line and each of V’s replies to him. The edit removes 15 playback events across six scenes, including the duplicate body reaction, the gated lines, and two empty cues. All 310 other dialogue events retain their original sections, start times, durations, and text bindings. The cut sections have zero duration and no route into them from any scene entry. [Original dialogue audit](../welcome_to_paradise_johnny_audit_20261118_01/REPORT.md) · [Candidate verification](candidate_01/verification.json)

| Stage | Continuation |
|---|---|
| Night Corp Tower | After Richard’s setup, his workspot, next narration section, and hologram activation run immediately. |
| Arasaka Memorial | Richard finishes his preceding line and moves to his next position. His teleport completion starts the next narration section. |
| Rancho Coronado | The arrival trigger and both journal updates still run. The scene dispatches its native security event and signals `End johnny` to the quest without waiting for an actor or either line. |
| Kabuki tour | The reply-only **Haze has guts.** choice is removed. **She took it too far.** and **A bridge in Kabuki?** retain their original responses, including the bridge clue flag. Both clue paths rejoin the tour without V speaking to Johnny. |
| Haze’s body | Both versions of V identifying Haze lead directly to the existing investigation continuation. |
| Meeting Aera | The gated Johnny aside is disconnected. Aera’s conversation, the shard choices, and their outcomes use their original routes. |

The package resolves all 19 quest phases and 14 scenes from the tour entry. All 1,768 packed archive members passed readback. Three original graph checks specifically cover the Rancho security event and exit, the two Kabuki menu destinations, and the investigation exit after either identification line. Localization lookup slots keep their original IDs so later dialogue and menu labels resolve correctly. [Staged package](candidate_01/package) · [Core manifest](candidate_01/core_manifest.json)

The build is staged. In-game audio, pacing, and tour completion are pending. The most useful live checks are Richard’s transition at the Memorial, combat progression at the dam, and the journal update after finding Haze.
