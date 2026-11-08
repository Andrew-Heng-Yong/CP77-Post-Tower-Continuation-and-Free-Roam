# Heavy Hearts workspot support

HH1 was installed over QR19 on 6 November 2026 at the user's request. It restores passive workspot support for Heavy Hearts NPCs already present after The Tower. The archive and XL replacements, 51 Core paths, 26 dependencies and 313 preserved save files verified. [Installation record](deployment_01/REPORT.md)

| Reported actor | Native community entry | Position match |
| --- | --- | --- |
| Waitress | `#sts_ep1_06_com_civilians` → `waitress_fluff` | `#sts_ep1_06_waitress_fluff_night_006` |
| Patron | `#sts_ep1_06_com_civilians` → `chat_kurtz_001a` | `#sts_ep1_06_ws_chat_kurtz_001a` |
| Guard | `#sts_ep1_06_com_fake_barghest_guard` → `enemy_019` | `#sts_ep1_06_enemy_019_night` |

All three reported `workspot=false` and were within one millimetre of their native AI spots. The live gig flags were active=1, start=0 and done=0, with club closure, combat despawn and alarm flags clear. The native Heavy Hearts root owns both support prefabs under the EP1 open-world branch retired by the ending. QR19’s private gig entry can load the native job body, which does not own those two prefabs. [Exact provider capture](native_01/capture.json) and [community bindings](plan.json).

HH1 takes 75 civilian and patron workspots and 26 guard workspots from the two original EP1 sectors. Each retained workspot follows an exact native community schedule or supplies one of its two bound master spots. The two private sectors contain only `worldAISpotNode` placements. They carry no population spawners, guard areas, patrol or combat scripts, devices, doors, scene triggers or quest progression. Native placement bytes, identity, workspot resources and master links are preserved.

The private owner waits for genuine Tower cleanup and the released handoff. Each branch also waits for a member of a corresponding native community to exist and the club’s closure and combat flags to allow admission. The existing gig’s active and start values are compatible with the new support. The owner writes only its own claim and entry receipts and holds its two leases independently. The two guard spots with an external look-at dependency remain outside HH1’s scope. Crowd schedules outside these two sectors retain their original providers.

## Verification

- Typed CR2W readback checked 101 retained nodes and their placements, metadata, the two master dependencies, 70 official workspot asset providers and four new depot keys. [World verification](built_04/world_verification.json)
- The serialized guards and receipt paths passed modeled admission checks, including the observed gig flag combination, missing actors, active combat and prior claims. The new ArchiveXL phase ID was checked against the native parent and installed registrations. [Owner verification](owner_verification.json)
- All 1,581 archive payloads verified. The 1,577 prior payloads remain byte-identical. The two changed package paths are the combined archive and its ArchiveXL registration file. All 77 pinned installed Core and dependency files verified. [Package manifest](candidate_01/package_manifest.json)

## First gameplay check after authorized installation

1. Cold start and load the same post-Tower save. Go to the Heavy Hearts bar and give the actors a few seconds to settle.
2. Observe the waitress and a seated or idle patron, then the guard near the entrance. Aim the camera at the actor while holstered. Open the Cyber Engine Tweaks overlay with the configured key, select **Console**, paste the line below and press **Enter**. The command reads the owner receipts, the gig’s state and the targeted actor’s workspot.

```lua
do local q=Game.GetQuestsSystem(); for _,s in ipairs({"street","guard"}) do local k="PTFRHH1_"..s.."_"; print("HH1",s,"claimed",q:GetFactStr(k.."Claimed"),"entered",q:GetFactStr(k.."Entered")) end; print("gig active/start/done",q:GetFactStr("sts_ep1_06_active"),q:GetFactStr("sts_ep1_06_start"),q:GetFactStr("sts_ep1_06_done")); local p=Game.GetPlayer(); if not IsDefined(p) then return end; local n=Game.GetTargetingSystem():GetLookAtObject(p,true,false); if not IsDefined(n) then print("HH1 no target"); return end; print("workspot",Game.GetWorkspotSystem():IsActorInWorkspot(n)); local ok,r=pcall(function() return TDBID.ToStringDEBUG(n:GetRecordID()) end); if ok then print("record",r) end end
```

3. Record one indoor sample and one guard sample. An entered receipt shows the lease was reached. The actor’s animation and workspot status provide separate evidence. Use one save/reload check to confirm the routine comes back without a duplicate actor or a gig state change.

HH1 is installed and file-verified. Actual community wake, animation recovery and save/reload remain untested.
