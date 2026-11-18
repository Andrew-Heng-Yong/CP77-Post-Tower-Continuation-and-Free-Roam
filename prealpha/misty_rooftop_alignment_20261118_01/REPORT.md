# Misty’s rooftop chair placement and lighting

On 18 November the user saw the Sit prompt on the animation-repair build. Selecting it moved V through scenery to the elevator door. The user also saw the roof become overexposed on arrival, before selecting Sit. Get Up and a second use of the chair still need a live test.

## Chair

The workspot and Sit prompt were positioned at the original rooftop chair. Section 8 still played the sit-down animation with the original Kerry villa offset in the scene frame. The private scene uses the rooftop elevator panel as its origin, about 11.5 metres from the chair. The animation therefore sent V to the panel.

The successor places the entry animation relative to V’s rooftop chair using the original vanilla displacement and facing between the chair and the entry animation. The seated workspot and animation now use the same scene frame. Get Up plays at V’s current position. The packed scene passed a world-coordinate check and a full structural comparison. Both previously repaired stand-up animation references are present. All 1,750 other archive members and all 50 other Core paths match the installed build. [Placement checks](placement.py) · [Staged candidate](candidate_01/core_manifest.json)

## Rooftop exposure

The expansion sector contains a weather-dependent environment trigger named `{T_Rooftop}`. Its rotated volume covers both the elevator landing and V’s chair. It blends camera, cloud and fog settings over five seconds. The enabled camera profile has f/1.4, ISO 50 and a shutter time of 1. The private Sit scene has no screen effect definitions or instances.

The vanilla Tower pickup scene enables `Q307_AV` at scene nodes 2022 and 3050. This normally disabled variant owns the rooftop trigger. The reviewed q307 resources contained no matching explicit disable on the rooftop lighting prefab. The same variant includes six lights, four areas including the rooftop and flight areas, a reflection probe, a mesh and collision across seven sectors. The location and arrival timing identify a candidate. A live comparison is needed to establish its contribution to the reported image. [Current-sector inspection](inspect_lighting.ps1) · [Variant and volume checks](lighting.py)

### Saved lighting through The Tower

The saved world-state records establish that the rooftop pickup lighting stays enabled into free roam. The records use the full rooftop prefab identifier `0xabd74373424e4654` and the variant name identifier `0x5d43736ac09dd496`. Each inspected world-state section parsed to its end, with sorted owner keys and Boolean values. The original save hashes matched before and after reading. The sampled slots share a playthrough ID. They provide checkpoints across the ending, including repeated playthrough branches. [Save reader](read_lighting_evidence.ps1) · [Record checks](trace_saved_lighting.py)

| Checkpoint | Rooftop pickup lighting | Independent evidence |
| --- | --- | --- |
| ManualSave-26 before pickup | No saved override. Authored default off. | The four other checked rooftop story-light variants also have no override. |
| AutoSave-15 in the hospital | On | The Tower is active. Free-roam activation is absent from the serialized facts. |
| EndGameSave-124 after credits | On | Free-roam activation is 0. The clinic’s pickup lighting is off and its ordinary lighting is on, matching both writes in vanilla cleanup node 22. |
| AutoSave-16, ManualSave-32, AutoSave-9 and AutoSave-10 | On in all four | Each has `PostTowerFreeRoamActive=1` and a completed handoff. The saved V position in AutoSave-10 is inside the volume. The other three positions are outside. |

The enabled camera setting has automated exposure off. The alternate automated camera setting on the same node is disabled. The normal portal volume occupies the same space and supplies color-group settings. The two nearby q116 story camera volumes are default-off, and none of the seven saves has an enabling record for either one. The authored pickup filter depends on the current weather. These records establish the retained override and its boundaries. Isolating its contribution to the image still requires a same-position, same-weather comparison. For that comparison, target the rooftop environment trigger alone. Toggling the whole pickup group also changes its lights, mesh and collision. [Ending checkpoints](saved_ending_trace.json) · [Free-roam checkpoints and control](saved_lighting_trace.json)
