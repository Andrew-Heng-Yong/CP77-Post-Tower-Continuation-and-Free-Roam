# Space Oddity opening — 15 November 2026

**USER_REPORTED_PASS — marker, NPC presence, opening conversation and quest activation.**

Following the three read-only console screens and the normal-location test, the user reported:

> the marker exist, npc appear conversation appear, quest is successfully triggered

This is the current live run associated with the ManualSave-32 test fixture and the previously verified RD10_MID_QUEST_RESUME_RETIRED installation. No subsequent save slot or new save body was supplied. The report does not change the earlier saved snapshot or its Inactive journal reading.

The earlier source-bound handler was waiting for `#mq003_com_homeless` to spawn at `1/51399/7/2`, node19. The successful normal visit establishes that the entry, marker, NPC and conversation concerns did not reproduce on this fixture. It supports interpreting that earlier snapshot as a pre-discovery wait, without treating source presence or Entered=1 alone as a gameplay pass.

The exact live journal enum was not sampled again; quest activation is user-reported. Briefcase resolution, later objectives, combat, rewards, terminal state, interruptions, cleanup and save/reload were not reported and remain unqualified. Do not ask the user to repeat the successful opening merely to recreate evidence.

No runtime/resource change, forced activation, deployment, game launch or save edit was performed to obtain this result. KOLD MIRAGE's separate failure remains unresolved. The next entry check is Ezekiel Saw the Wheel, followed by The Highwayman and Sweet Dreams; see the [current test card](TEST_CARD.md).
