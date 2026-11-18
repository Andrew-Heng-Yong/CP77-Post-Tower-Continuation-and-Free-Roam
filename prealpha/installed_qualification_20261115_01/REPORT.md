# RD10 installed-build qualification — first pass

15 November 2026, Toronto. The target is the installed `RD10_MID_QUEST_RESUME_RETIRED` build. This pass checked exact installed inputs, an existing startup/load run, and the available paired save boundary. It did not launch the game, change installed files or write a save. Raymond Chandler Evening is excluded from the active marker test queue at the user's request.

## Results

| Check | Result | Limit |
| --- | --- | --- |
| Installed identity | **PASS.** All 51 Core paths and 26 required files match the exact installed manifest. The required Virtual Atelier `SetupNewTab.reds` matches its reviewed hash. | Byte identity, not gameplay. [Local proof](run_01/identity.json) |
| Startup and one post-Tower load | **LOG-BACKED PASS.** The 20:57 session compiled scripts, reached the loading cover's `Ready` state with control restored and `fault=0`, then shut down normally. | No human visual assessment or save/reload cycle. [Bounded observation](../mid_quest_resume_retire_20261115_01/observations_01/REPORT.md) |
| Selected journal catalogue | **SOURCE-PINNED.** The installed history script supplies 158 entries; the installed S30 data adds three. Across these 161 entries, the source contains 242 distinct quest map-pin journal paths. | Source presence does not prove a rendered icon. [Local catalogue](run_01/catalogue.json) |
| Paired save boundary | **READ-ONLY PARSE.** ManualSave-31 and EndGameSave-92 have matching playthrough and point-of-no-return IDs. Of the selected journal paths serialized in those saves, 14 quest roots were Active before the ending; 13 are Failed and one is absent in the after-credits save. Thirty-five selected roots remained Succeeded. | EndGameSave-92 was written before the 21:06 load and post-Tower restoration. No selected map-pin records were serialized in either body. Absence is not an Inactive state or a missing rendered icon. [Local projection](run_01/journal_fixture.json) |

The identity verifier initially treated the Atelier file as outside the 26 required files. Inspection of the manifest showed it is one of them. The verifier was corrected and then passed; the first attempt changed no game or save file.

## Next test boundary

The available after-credits save is not a saved **post-Ready** state. The [next-session test card](TEST_CARD.md) obtains one new manual save after the loading cover reaches `Ready`, plus map and journal observations from that same session. With that fixture, compare the selected journal roots and map pins, owner/entry receipts, and live map before choosing eligible quest routes. Do not use the 19-to-8 historical icon count as a measured list of missing jobs.

The active build deliberately retires new mid-journey claims. Previously reported completions remain bounded accepted fixtures; this pass does not request replaying them. Quest advancement, messages, actor support, rewards, presentation, profile/recovery persistence and save/reload still need live qualification on genuine eligible states. No release, install, rollback or Git push followed this first-pass test.

**Follow-up:** the user supplied post-Ready ManualSave-32. The first route check found KOLD MIRAGE Issued but not Entered, with its original content wait registered and no reported map marker. [Bounded KOLD failure investigation](../installed_qualification_20261115_02/REPORT.md). This does not certify the other selected quest routes.

The user also confirmed a later Ozob phone message offering Send in the Clowns and classified older messages cleared by Tower as expected. [Bounded phone observation](../installed_qualification_20261115_02/PHONE_OBSERVATION.md)
