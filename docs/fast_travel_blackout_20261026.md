# Fast-travel blackout: Buran St to El Coyote

26 October 2026. The user reports that fast travel from Buran St to El Coyote left the world and menus, including Escape, black while movement, weapons, audio and input continued. They confirmed the latest session, around 13:22–13:25 local time. This is a live bug report on the current CR1 installation; it does not establish that CR1 caused it.

The log review captured 37 files under `diagnostics/fast_travel_blackout_20261026_01`. All 51 installed PTFR files still match CR1. No game launch, installed edit, save edit, fact write or rollback was performed.

## Observations

- Script compilation succeeded for the 13:17 session. There is no new local crash report; the newest report directory was from 25 October.
- PTFR's setup cover reached **Ready at 13:21:53**. Its source immediately sets `released` and dismisses the popup. There is no later setup-cover log in the reported window, but visual popup destruction is not separately logged, so this does not prove that every UI layer was removed.
- Game fact changes continue at **13:23:47 and 13:24:04**. Immersive First Person logs pause/resume and vehicle transitions. These support the user's report that simulation and input remained active; they do not identify the exact fast-travel arrival time.
- RED4ext begins an orderly shutdown at **13:25:05** and completes it at **13:25:08**.
- RED4ext refuses the Immersive First Person **0.2.0 DLL** at startup because its requested game runtime differs. Its separate CET camera logic still logs activity. This is a compatibility finding, not a demonstrated cause of the blackout.
- A read-only Windows System-log query for 13:15–13:30 returned `NoMatchingEventsFound`. That absence does not rule out a rendering fault.

## Conclusion

The logs do **not** identify the exact cause. A stuck fade, fast-travel loading layer or other full-screen UI layer is consistent with both the scene and menus being black while gameplay continues. The available records do not distinguish those from a rendering failure, and do not justify resetting quest facts, disabling arbitrary mods or rolling back CR1.

The next useful diagnostic is a read-only capture during the same route's blackout: fast-travel loading-screen completion, active UI/fade state, popup teardown, and player destination. Current logs do not record these values. Preserve the existing evidence before a new session rotates logs. The final pinned record is `diagnostics/fast_travel_blackout_20261026_01/assessment_01.json`.
