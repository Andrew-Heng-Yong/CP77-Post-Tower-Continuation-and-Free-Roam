# R5 one-run private-variant and original-owner diagnosis

Use an unmodified disposable completed-Tower save and quit without saving.
R5 is installed idle; this route checks whether its private shell/street
variants truly switch, then isolates the surviving original Misty objects.
It does not claim to repair the wall or NPC navigation. Do not force q307
facts, save, fight NPCs, or run the old R4 route.

1. Cold-load and stay on known supported public ground. Before Start, look at
   the clinic from across the street. Record whether the Zetatech shell and
   added Tower street dressing are absent or already visible. If the building
   looks unsupported, do not enter.

2. While freely moving, teleport to the established safe point outside 80 m
   and arm R5:

   ```lua
   Game.GetTeleportationFacility():Teleport(Game.GetPlayer(), ToVector4{x=-1658.87463,y=997.365662,z=23.6999989,w=1}, ToEulerAngles{roll=0,pitch=0,yaw=-170})
   GetMod("PTFR_MistyViktor_World").Start()
   ```

   Close CET, wait two seconds, then:

   ```lua
   GetMod("PTFR_MistyViktor_World").Inspect()
   ```

   Require Revision5, Registered1, Enabled1, Applied1. Walk back by supported
   public routes. From outside, verify Zetatech shell, floor and street art
   appeared. Do not enter if the floor/door is missing. Record:

   ```lua
   GetMod("PTFR_MistyViktor_World").Mark("r5-private-range-visible")
   ```

3. Only if the shell/floor appeared, stand on supported ground **outside** the
   shop and use this explicit Codeware diagnostic for the *original* Misty
   interior. It modifies the current disposable world state; do not save:

   ```lua
   local s=Game.GetWorldStateSystem(); if IsDefined(s) then s:TogglePrefabVariant(CreateNodeRef("$/03_night_city/c_watson/little_china/loc_mystic_mistys_ripperdoc_prefabH2DWJJI/#loc_mystic_mistys_ripperdoc_env/#loc_mystic_mistys_ripperdoc_interior"),"q307_hide_misty",false); print("requested original Misty OFF") else print("WorldStateSystem unavailable") end
   ```

   Close CET, wait, and look at the candle cluster **from outside** first.
   Enter only if the shop floor and access remain intact. Report whether the
   candles disappear. This distinguishes a native-request timing/owner issue
   from a different live candle source; it is not a permanent repair.

4. Police props, wall gap and NPC pathing need only a visual note on this run.
   Do **not** toggle the whole original `q307_misty_alley` range yet; that
   mixed range owns other world nodes and could remove support or scene art.

5. Return to the safe point while freely moving. Stop, close CET and wait at
   least two seconds before Inspect (R4's immediate Inspect was too early):

   ```lua
   GetMod("PTFR_MistyViktor_World").Stop()
   ```

   ```lua
   GetMod("PTFR_MistyViktor_World").Inspect()
   GetMod("PTFR_MistyViktor_World").Finish()
   ```

   Expect Enabled0/Applied0/Releases1 on normal guarded release. If support
   is missing or V cannot leave safely, do not Stop under V; quit without
   saving and report it. In every case quit without saving and send the two
   key observations: private shell off-before/on-after, and candles after
   the direct original-variant request.
