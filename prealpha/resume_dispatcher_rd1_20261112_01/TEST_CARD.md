# RD1 gameplay test after authorized installation

Candidate 04 is installed and file-verified. Use this card to test RD1 gameplay; the offline and installation checks do not establish quest execution or reload behavior.

Use **AutoSave-2 at Viktor** after deployment. Complete the remaining Tower sequence, Misty, final scene and credits normally in the same session. Let the mod release free roam. The existing loader automatically selects the global latest valid snapshot; no snapshot command or AutoSave-5 command test is needed. The known good snapshot has **Machine Gun — Deliver Skippy**, **Moving Heat — reach the first door**, and inactive **The Highwayman**. If the loader selects a different newer snapshot, its actual stages determine eligibility.

1. Check the journal after free roam starts. Machine Gun should return to **Deliver Skippy**, and Moving Heat to its first-door objective. No earlier quest setup or gun grant should replay. Existing completed and genuinely failed history must stay unchanged.
2. Make a **new manual test save**, then reload it. The same objectives and existing items should remain, without a second controller, second Skippy or repeated messages. Keep the original AutoSave-2 and pre-test save intact.
3. For Machine Gun, visit Regina, follow the normal delivery interaction and check that the quest advances from the delivery objective. Complete the chosen native outcome once. Check the gun transaction and reward once, then save/reload and confirm they do not repeat. The delayed reacquisition follow-up requires its own later observation; entry success does not certify it.
4. For Moving Heat, approach the native first door, follow Ashlay's normal interaction and verify that the door/control sequence advances to the next objective. The player must start outside the two native garage triggers for admission. Continue through the car retrieval and its normal outcomes before calling the whole quest tested. Save/reload once during progression and confirm no reset or duplicate message/reward.
5. For the inactive Highwayman control, confirm it still uses its existing normal start route and installed Johnny edits. Do not treat its unchanged source bytes as a gameplay pass.

Stop at a crash, duplicate reward/item, objective reset or stuck interaction and retain that test save. Report the quest/objective and last action. Log review should check the RD1 phase merge, `PTFR_ResumeRD1` reason, SC3 stop acknowledgement, S22 admission and crash/compiler errors. No fact-setting workaround is part of the test.

Gates remain separate: genuine Tower completion; history import; admission; functioning callbacks/support; quest outcomes; one-time rewards; reload. A journal objective appearing proves only part of the route. Timer-preservation testing is outside this candidate because native preservation is disabled.
