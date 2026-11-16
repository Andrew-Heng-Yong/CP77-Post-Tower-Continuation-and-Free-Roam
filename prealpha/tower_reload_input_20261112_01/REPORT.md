# Input on completed Tower saves

The user reported that post-ending saves accepted no movement, camera, Escape or CET input. A pre-ending save still accepted input. On 12 November the CET game log recorded reload attempts at 00:10, 00:16 and 00:22 Toronto time. The mod opened its setup cover even though the native prepared, reveal and finished facts were already set. Each attempt reached the profile check at step 5 of 12 and logged a wait for safe gameplay. The existing `SetupPopupLC1` requests a blocking game notification and handles released input. Its blocking state persisted during the wait.

Read-only save inspection found the completed arrival and original cover acknowledgement in `AutoSave-0` and `AutoSave-4`. `ManualSave-26` is the pre-ending comparison. These samples corroborate the saved arrival state separately from the timestamped reload attempts. [Saved arrival facts](saved_arrival_facts.json)

The loading cover now determines the session type when the arrival facts first meet its requirements. Loading a save with an already finished arrival runs the existing setup checks in the background. The first handoff still shows the cover, acknowledges a rendered frame to the native graph and requires the established checks before release. Gameplay admission still uses the same completion checks, and the input repair changes only the cover script.

## Verification

Source checks preserved the existing gameplay release function, setup checks, popup teardown and native acknowledgement write. The source predicate was checked against both completed saves, the pre-ending save and a first-arrival fixture. All 148 registered scripts compiled. [Source patch](candidate_01/source.patch) · [Compile result](compile_01/result.json) · [Saved-route checks](saved_route_checks.json)

Nine installer fixture actions passed, including interrupted-install recovery and rollback. The closed-game installation and independent readback verified all 51 Core paths and 26 dependencies. All 343 save files matched their pre-install names and hashes. The previous cover script is available through the verified rollback. [Installed manifest](deployment_01/installed_manifest_01.json) · [Transaction fixtures](fixture_results.json) · [Rollback readiness](deployment_01/rollback_readiness.json)

In-game input confirmation remains pending at the installation assessment.
