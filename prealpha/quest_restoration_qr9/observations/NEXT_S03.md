# Next human step — short Nitro eligibility observation

Purpose: read the existing Nitro quest/vehicle/purchase state before selecting a positive, negative or already-issued test. This is a prerequisite observation, not a request to complete another gig or manufacture eligibility. The previous S00 run did not watch these signals. Ronald's contact was Inactive/messages0 there, so its positive-news card is not suitable yet.

1. Launch normally. At the main menu, enter manually in CET:

   ```lua
   GetMod("PTFR_QR9_Diagnostics").start("S03")
   ```

2. Load your working save from after completing Until Death Do Us Part. Preserve ManualSave-23 and its offline backup. Metadata last observed AutoSave-1 at November2,11:53:33 with the gig completed; choose your own matching working progress if you have since saved further. A metadata entry does not prove which slot was previously loaded.
3. Play or stand normally for1–2 minutes. No purchase, quest acceptance, forced start or special location is required for this precheck. If any quest activates or a message appears naturally, note it. Lack of activation is not a failure before eligibility is established.
4. Stop manually in CET, then quit normally:

   ```lua
   GetMod("PTFR_QR9_Diagnostics").stop()
   ```

5. Tell Codex the probe is finished and whether anything appeared. Codex will collect the S03 log and inspect the selected purchase facts, four guarded vehicle-unlock getters, journal and existing owner signals. No manual fact list is needed.

The default five-minute bound is ample for this short precheck. Stop before every deliberate reload; use a new segment afterward. Do not buy/spawn vehicles, reset quest counters, create a Ronald subscription, replay the completed gig or alter any facts to make a test available. Missing API/native-condition equivalence remains explicit; player-unlocked state alone does not prove every native VehicleAvailable predicate.

After this observation, choose the correct genuine eligibility/progress variant from the existing S03 card. This precheck itself cannot certify progression, rewards, save transitions or all Nitro contracts.
