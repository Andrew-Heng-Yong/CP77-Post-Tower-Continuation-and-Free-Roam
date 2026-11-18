# Automatic Photo Mode refresh test

Installed and verified on 17 November 2026. AutoSave-16 is restored to the preserved Misty's alley checkpoint, before the final scene and credits. The previous AutoSave-16 slot is preserved in the restore recovery folder. [Installed manifest](installed_manifest.json) · [Save restoration receipt](../../recovery/auto16_photo_refresh_restore_20261117_01/restore_receipt.json)

The refresh runs once after the setup checks settle in the session that ran the genuine Tower credits close. The existing permanent cover stays up while the blocking setup popup detaches. The installed Codeware API executes the native Open Photo Mode node directly with an empty screenshot fact and regular camera admission. The active menu also receives a cover within its own layer. After the intro and the preview item callbacks finish, the mod calls the menu's normal exit once. The mod waits for the menu to hide and for V's gameplay camera to settle before releasing setup. [Loading controller](source/PTFR_LoadingCoverLC1.reds) · [Codeware quest node execution](https://github.com/psiberx/cp2077-codeware/blob/main/src/App/Quest/QuestsSystemEx.hpp) · [Vanilla entry and exit evidence](../../docs/post_tower_photo_mode_refresh_20261117.md)

CET drives the timeout during the Photo Mode pause. If the preview stalls, the mod can request normal exit when it owns the menu and the game allows exit. On interruption, it clears its covers so the native interface remains usable. The ordinary setup checks finish when gameplay returns. Loading a completed Tower save follows the normal continuation path. [CET update](source/init.lua)

The two scripts compiled against all 149 registered REDscript inputs. Compiled readback verified the entry, preview and exit wiring. The LuaJIT callback fixture and three isolated deployment and recovery cases passed. The installed file and save readback checked 51 Core paths, 65 protected game files and all 472 other save files. File rollback to the predecessor is ready. [Compile assessment](candidate_01/compile_01/assessment.json) · [Readback](candidate_01/verification.json) · [Recovery fixtures](deployment_fixtures.json)

The live torso and arms result, the rendered cover and the duration of the cycle await the first in-game trial. Load AutoSave-16 and finish The Tower through the credits. As soon as free roam returns, look down with the weapon holstered and then with it drawn. Observe whether the torso and arms look normal before using the vehicle or manual Photo Mode workaround. Also note any visible Photo Mode screen between setup and free roam. If the cycle appears to skip or stall, this read-only CET status reports its last observed step.

```lua
print(GetMod("PTFR_PreAlpha").PhotoRefresh())
```
