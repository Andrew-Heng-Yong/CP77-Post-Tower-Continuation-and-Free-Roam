# Jason Foreman comparison for the user-selected AutoSave-8

The user identified the latest save as **AutoSave-8**. It is the newest valid menu timestamp in the game save directory, **November 4, 2026 at 12:30:56 AM**. Its body and metadata hashes match the existing QR15 capture exactly. The comparison now applies to the selected file. Earlier JF01/JF02 session identities remain unbound. [Machine-readable comparison](compare_01/result.json)

| Saved evidence | October 26 AutoSave-16 backup | November 4 AutoSave-8 |
| --- | --- | --- |
| `q307_ep1_killed` | No captured record | `1` |
| Jason preparation flag | `1` | `1` |
| Shared courier force counter | `1` | `1` |
| Jason descendant registrations | `12`, including the approach wait | `0` |
| Broken-car saved activation | Active byte `1`, associated ID `10229047` | Same fields and associated ID |
| Four bound vehicle state keys in PS2 | No matching record | No matching record |

The selected save also has `q307_done=1` and `q307_finished=1`. It retains Jason’s interned paths but lacks the authored approach registration and the other Jason registrations seen in the earlier body. The fresh-only entry gates reject `sts_ep1_03_start_community=1`. The combination explains why the prepared state stays outside the restored entry path. The two historical bodies have matching saved identities and consistent facts for the scoped comparison. An uninterrupted ancestry between them was not established. [Source gate analysis](../REPORT.md) and [earlier fixture evidence](../earlier_saves_01/REPORT.md)

The earlier body’s version-277 CommunitySystem component was decoded to its exact end. For source-bound global node ID `17433794865907239043`, all saved spawner fields agree with the selected file, including the same reserved/filtered entity ID. This establishes persisted activation intent across the comparison. The two PS2 scans check the raw associated ID and three exact component keys across all rows. Missing entries in both saves still cannot distinguish a completed visual or door command from state filtered during saving. [Persistence filter evidence](../identity_01/REPORT.md)

The remaining engineering work is a supported rebind of the native approach and startup waits that preserves the existing car record, completed setup and courier history. The earlier retained registrations provide a concrete fixture for that work. The actual post-ending body has no matching slots for native save restoration to consume. Its saved car record supplies no final application receipt. This evidence does not justify restoring a phase by replaying its startup entry.

The earlier car component was captured with the pinned reader by `capture_car.ps1` into `car_capture_01`. The capture contains the community span, its framing data and the four PS2 membership results. To check the retained comparison with fresh output from the workspace root:

```powershell
& 'C:\Users\Ayong\.local\bin\python3.14.exe' -X utf8 -B 'prealpha\quest_restoration_qr15\latest_save_01\compare.py' --out compare_02
```

The command checks both exact save and metadata hashes before and after analysis, reuses the existing captured native registration and fact records, and writes only the new result. An overwritten AutoSave-8 requires a new file binding.
