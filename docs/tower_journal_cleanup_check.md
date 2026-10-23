# One short Tower journal cleanup and reload check

Candidate is manual until validated. Only the exact completed Tower journal
hierarchy is eligible. No teleport, ending replay, story fact command or
service retest. Installation: research/tower_journal_cleanup/install_receipt.json.

1. Cold-launch and load a disposable copy/slot of your currently working
   post-Tower save. Stand idle in an ordinary street, outside a vendor/mirror/
   dancing prompt, without combat, riding or a phone conversation. Preserve
   the original slot. Open the journal first and note whether Things Done
   Changed is Active or Completed and whether a Tower objective is tracked.
2. In CET, run this as its own line:

   ```lua
   GetMod("PTFR_TowerJournal").Start()
   ```

   It logs the original full hierarchy and guards, and makes no journal change.
   Expect PREPARED. If refused, stop and report the message; do not change facts.
3. Run this separate line once:

   ```lua
   GetMod("PTFR_TowerJournal").Repair()
   ```

   Close CET and wait10 seconds in normal gameplay. Then run:

   ```lua
   GetMod("PTFR_TowerJournal").Check()
   ```

   Expect VERIFIED_JOURNAL_STATE. Check that Things Done Changed is in Completed
   history and the Tower HUD objective/tracking is gone. Existing unrelated
   tracking may remain; the mod never untracks another quest. No narrative
   scene should play. Report any failure; do not repeat Repair to conceal it.
4. If that check passes, make a NEW disposable manual save in an unused slot,
   stop logging, and fully quit:

   ```lua
   GetMod("PTFR_TowerJournal").Stop()
   ```

5. Cold-launch and reload only that new test slot. Do NOT run Repair again.
   Check completed history and the HUD, then record the reloaded state:

   ```lua
   GetMod("PTFR_TowerJournal").Start()
   GetMod("PTFR_TowerJournal").Check()
   GetMod("PTFR_TowerJournal").Stop()
   ```

   On this read-only reload visit, PREPARED means the checker is ready; native
   states must already be Succeeded and Tower tracking absent. No Repair needed.
   Quit without saving again and report the new slot plus both UI results.

Logs are `tower_journal_*.jsonl` inside CET's PTFR_TowerJournal mod folder.
The agent reviews exact states, guards, other quest states and native events.
If the first journal was already completed, preserve that observation: an
idempotent cleanup still checks for stale Active children/tracking without
replaying a completion notification or activating unused branches.
