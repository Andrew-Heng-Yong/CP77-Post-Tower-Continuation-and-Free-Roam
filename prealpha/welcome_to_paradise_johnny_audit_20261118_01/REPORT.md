# Johnny dialogue audit for Welcome to Paradise

The staged MQ061 tour has **six distinct Johnny lines on connected quest routes**, three voiced V lines addressed to Johnny, and one player choice that directly starts a V–Johnny exchange. **No tour objective or interaction caption says “Talk to Johnny.”** This is a static audit of the staged 2.5 build. Actual playback is untested. [Staged candidate and scope](../welcome_to_paradise_20261118_01/REPORT.md)

## Lines on connected routes

| Stage | Speaker and English subtitle, in order | Trigger and scene nodes |
|---|---|---|
| 01 · Night Corp Tower | **Johnny** “Damn, globe-sized ego. Why am I not surprised?” | During the drone tour. The scene takes node 735 on the route after the connect-to-drone choice. |
| 03 · Arasaka Memorial | **Johnny** “Devised a solid plan and pulled it off.” **V** “Done pattin' yourself on the back?” | Automatic exchange during Richard’s account of the bombing. Scene node 581 leads to 623, then 629. Node 629 returns to Richard’s narration at 582. |
| 07 · Rancho Coronado, Coronado Dam stop | **Johnny** “Hm, prolly not a great sign.” Then **Johnny** “See that? Best stay on our toes.” | Entering the `#mq061_07_rancho_johnny` area starts the scene’s `johnny` input. The scene waits for the Johnny actor to spawn, then reaches 281 and 288 in order. Its `End johnny` output feeds the quest at node 48. |
| 12 · Kabuki tour, Haze’s recording | **V** “Damn, Haze has guts. Gotta give 'er that.” **Johnny** “Better to die on your feet than live on your knees.” | Choosing **“Haze has guts.”** at node 710 sends the scene directly to 123. Both lines are in that section. The on-screen speaker label for this choice group is **Richard Night**. |
| 12 · Kabuki, after the tour narration | **V** “Bridge Haze mentioned – should scope it out.” | V is addressing Johnny in the screenplay. Node 484 sends its false output to 172 if the earlier bridge choice was skipped. Choosing **“A bridge in Kabuki?”** sets the flag and skips this reminder. |
| 12 · Finding Haze’s body | **Johnny** “Shame, feel bad for her.” | The body-investigation scene plays this at 74 after either of V’s body-identification lines. The same subtitle is also present in the main Kabuki scene at 239. Its `Start 1` input has no caller in the audited tour phases. Counted once. |

The other options at Kabuki node 710 are **“She took it too far.”** and **“A bridge in Kabuki?”** Their immediate destinations are nodes 125 and 129. Neither enters Johnny’s reply at 123. V’s bridge reminder at 172 can still follow the first option. [Staged Kabuki scene](../welcome_to_paradise_20261118_01/work/cook_02/readback/towercontinued/paradise/base/quest/minor_quests/mq061/scenes/mq061_12_kabuki_scene.scene.json)

## Recorded lines behind a fact check

| Stage | Johnny’s English subtitle | Gate |
|---|---|---|
| 12 · Kabuki tour | “What a steamin' load of shit. Plug your ears to this corpo scuz.” | Scene node 307 waits for `travelling_merchant_lives >= 9999` before 238. |
| 13 · Meeting Aera | “Like a fuckin' ray of sunshine.” Then “Don't like this at all. Corps always win. Ordinary people always lose.” | Node 285 waits for the same fact, then 275 leads directly to 276. They form one sequence, independent of the shard choice. |

The audited pre-cleanup history snapshot recorded a stable **0** for this fact. It would need to reach **9999** for those branches to open. The two empty, 100 ms dialogue events in the Memorial (700, V to Johnny) and Haze-body scene (82, Johnny to Johnny) have no English subtitle. The scene data gives no words to transcribe for either.

## Prompts and objectives

All 14 MQ061 scenes, 19 quest phases, 69 wired choice captions across 38 choice nodes, and 90 journal objective records were inspected. The actor-attached choice nodes target Aera or the squatter. The tour’s Rancho `johnny` entry is an automatic player-area trigger. Kabuki’s reply is an on-screen choice. Neither requires aiming at Johnny to interact. The journal has **“Talk to Aera.”** and **“Speak with the stranger.”** The latter belongs to the introductory call. None of the quest’s 14 journal phases or 90 objectives is called **“Talk to Johnny.”**

The four staged private scene copies and the ten retained native scenes were checked against their matching native resources by hash. Their dialogue-event identities, screenplay stores, and embedded localization stores matched. The English subtitle index was joined by native resource hash, with the phase caller and scene socket checked separately. The candidate manifest SHA-256 was `B40DCB11B13739552FEB0F35E105B6563E3C35E5C9763CACF3F1192740E3D9F8`. [Staged build verification](../welcome_to_paradise_20261118_01/candidate_01/verification.json) · [English dialogue index and provenance](../johnny_dialogue_index_20261107_02/README.md)
