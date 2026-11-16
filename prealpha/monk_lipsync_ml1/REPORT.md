# ML1 — Losing My Religion lip-sync

The first monk spoke without moving his lips in the opening conversation on JB3. The restored quest uses private copies of the opening and epilogue scenes. Both scene keys were absent from the English lip-sync lookup, which binds each scene and actor voice tag to its animation set.

ML1 copies the two vanilla entries under the private scene keys in the existing `towercontinued\sidejob_repair_sr1\en-us.lipmap`. The entries reuse the native animation sets and rigs. Both scenes retain their original bytes in the rebuilt archive.

| Scene | First monk actor | Private scene key | Retained lines with stock clips |
| --- | --- | --- | ---: |
| `mq032_01_hook.scene` | `Cyberware_Monk` | `16255777967962415059` | 27 |
| `mq032_03_epilogue.scene` | `Monk_Cyberware` | `11118091249325218262` | 14 |

## Verification

- Matched the 51 installed Tower files and 26 required inputs to the JB3 manifest. Checked the native English map, six animation set providers, their rig references and the two new keys against the other configured English map.
- Reopened the cooked archive and checked every member. The lip map grew from 48 to 50 entries with both additions matching their stock donors. The other 1,635 archive members retained their JB3 hashes.
- Reopened the [51-file candidate ZIP](ML1_Core51_01.zip) and compared each file with the candidate. The combined archive is the sole changed package file. See the [package manifest](candidate_01/package_manifest.json), [scene evidence](plan.json) and [clip checks](candidate_01/prepared.json).

ML1 is staged for the verified JB3 baseline. Deployment and in-game playback are pending. The gameplay check is the first monk's opening dialogue in an eligible post-Tower save, followed by his epilogue if that stage is available.
