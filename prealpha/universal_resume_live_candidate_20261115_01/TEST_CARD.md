# MS31 game test

Use this card after the checkpoint v0.1.8 installation and closed-game checks pass.

1. Load **Manual Save 31**. Confirm that **Over the Edge** is still waiting on El Capitan’s response. Start the Reed route before advancing the wait.
2. Complete **The Tower** through its final scene, credits and return to free roam in the same session. Leave the world running after control returns and report that you are back in free roam so the handoff log can be checked.
3. After the handoff is verified, make a fresh manual save and reload that new slot. Report the slot and whether **Over the Edge** still shows the same pending objective.
4. With the reload verified, allow the remaining in-game wait to finish through ordinary play. Report whether Falco sends one message and the objective advances to collecting David’s jacket. Keep the pre-expiry save for comparison.

The first readback checks the captured wait at cutoff, original-owner retirement, the rebuilt Falco and Reyes registrations, and one active timer with the remaining deadline. Look for `PTFR Step 3 Over the Edge: handoff committed` in the latest `ptfr_executioncheckpoint` log before making the new save. The reload check ties the saved timer to the rebuilt handler in the new session. If the log says `restore deferred`, leave the game at the journal and report the visible objective and last completed step.
