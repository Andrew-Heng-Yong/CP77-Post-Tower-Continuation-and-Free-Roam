# Claire — one combined check

Automatic single-site candidate on Baseline R1. No Enable/Arm/Start command.
Use the same disposable post-Tower save used for the working Yagami test.
Do not replay the ending or change race/default facts. Logging starts and
flushes automatically. This run checks service and return together.

1. Cold-launch and load the disposable save. Wait about 10 seconds in ordinary
   gameplay, outside any dialogue, seat, vehicle or combat.
2. Travel to Afterlife and approach Claire's bar counter. Check for exactly one
   Claire. If she normally serves V, use an available dialogue and open her
   Trade inventory. Close the menu and finish the conversation normally.
3. At the counter, run this optional read-only marker (also run it if absent):

   ```lua
   GetMod("PTFR_B0_Claire").Observe("first-counter")
   ```

4. Walk out of Afterlife to the street, wait 5 seconds, then walk back to Claire.
   Repeat the dialogue/Trade check. Do not teleport while a dialogue is active.
5. After closing the menu/dialogue, run:

   ```lua
   GetMod("PTFR_B0_Claire").Observe("return-counter")
   ```

6. Leave the club again and quit **without saving**. Tell me whether Claire
   appeared once and dialogue/Trade worked on both visits. I will review the
   automatically written log; no Stop or Finish command is required.

If she is legitimately angry because of The Beast in Me, refusal is expected:
check that her angry dialogue returns and report it, rather than forcing Trade.
If Claire is missing, the observation distinguishes a closed original gate,
unstarted owner, unfired native trigger and requested scene. Stop there instead
of changing facts or enabling other packages.

The log's native crossing/request counters are diagnostic evidence, not proof
that the physical menu works. A later saved cold-reload check remains separate;
this first unsaved session must not be called a persistence pass.
