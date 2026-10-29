# Computer News and Atelier overlap — staged diagnosis

The supplied screenshot shows the NC Inquirer news site and Virtual Atelier drawn in the same browser page. Messages is unaffected.

The installed WA2 archive inventory has no browser, computer UI, NC Inquirer, or Virtual Atelier resource override. Its only `computer` path is the private MQ058 computer-hack quest phase. WA2 REDscript does not wrap `ComputerInkGameController`, `BrowserController`, or `WebPage`. This rules out a direct WA2 browser override; it does not establish whether post-Tower saved computer state changes which native page is opened.

The installed Virtual Atelier `SetupNewTab.reds` wraps `ComputerInkGameController.ShowMenuByName` and opens the computer's `startingPage` through `ShowInternet`. After the native `BrowserController.OnPageSpawned`, it removes children only from `page/linkPanel/panel`, then spawns the Atelier widget there. News elements outside that panel can remain visible, matching the screenshot. The message page does not use this browser handoff.

Candidate 01 was an initial broad page-root replacement and is not selected. Candidate 02 clears the native `page` widget (with the `Page` casing fallback) while keeping the outer WebPage frame, then spawns the Atelier widget there. The full-root fallback covers a missing page widget. It changes only `PopulateAtelierView` in a staged copy of `SetupNewTab.reds`, byte-matching the installed 1.6.4 archive everywhere else. All 112 installed REDscript and framework sources compiled with the candidate, and every installed source hash remained unchanged.

Candidate 02 is packaged as `candidate_02/computer_overlay_co1_candidate_02_ready.zip` (SHA-256 `7D2369AEDC1FEB1AC4A4E0E5ED53C42D0BA4D80EBB42587103D3309DD35C1053`). Its deployment script requires the exact current source hash, checks game closure for install or rollback, stores the previous file, and verifies copied bytes. Six fixture actions cover validate, install, verify, rollback validation, rollback, and restored validation; a modified target was rejected. The installed source still matches the required pre-install hash. This component is ready for a coordinated game-closed deployment after WA3 is staged and reviewed, with separate file rollback.

This is a source-level compatibility hypothesis, not an in-game pass. It has not been installed or merged into the WA3 successor. WA2 and the external mods in the game remain unchanged. The user requested that the computer fix and NPC package be installed together later.

After deployment, the Atelier tab, News tab, and Messages tab still need live verification. Do not infer that the candidate repairs all computer interactions or that WA2 directly caused this display issue.
