# Post Tower Continuation and Free Roam — Fred scene range repair (FS1)

Installed 25 October 2026. Offline checks and installation verification passed;
the engine behaviour still needs a cold-load check.

Fred's private vendor scene previously started within 50 metres and could
remain active until V left the wider 100-metre area. Because the scene includes
V for spoken dialogue, it is the strongest identified source of the ambient
`IsEntityInScene` result seen at H10. See the
[investigation](scene_membership_20261025.md) for the evidence and attribution limits.

FS1 gives the private scene a smaller range: it starts below 8 metres from the
existing Fred reference, and releases beyond 12 metres. Fred's NPC spawn stays
under its original 100-metre loading-marker lifecycle. Returning below 8 metres
requests one new vendor scene without respawning Fred. Between 8 and 12 metres,
the current scene state is retained. These are native distance checks, not a
new script polling loop.

The S25 fresh boxing branch keeps its original 50-metre admission and
100-metre departure conditions. Fred's scene file, cast, voiced lines, trading,
choice data and quest branch selector are unchanged. H4's purchase guard and
the H10 payment/ownership logic are also unchanged.

## Existing saves

The repair retains all existing quest-node IDs and types. It changes the
conditions on the existing admission node 4 and departure node 5, redirects
node 5's output, and adds nodes 400–403. A private scene saved with the original
departure wait can therefore reach the new release branch without restarting
the parent owner. The release cuts only private scene node 3 and pending
admission node 4. It then waits for a close return or full departure. It does
not cut the original boxing scene node 300, reset facts, change saves or replay
the spawn/quest/reward paths.

The graph model exercises legacy active/waiting states and the new saved wait.
Whether the engine resumes the saved distance condition and releases V exactly
as expected still needs an in-game test. Existing saved scene ownership was not
manually edited.

## Validation and installed scope

- One replacement: `archive/pc/mod/000000_TowerContinued_SideJobs_S25.archive`.
- Only `towercontinued\b0_story_services\fred.questphase` changes; the other
  25 archive resources are byte-identical after packing and extraction.
- Native payload/edge preservation, distance boundaries, idle/revisit behaviour,
  saved-branch models and original boxing behaviour passed offline checks.
- Fourteen real installer fixture actions passed, including rollback, changed
  baseline rejection, interruption recovery and later-edit protection.
- Validate, Install, Verify and ValidateRollback passed. All 675 protected
  files, including all 265 save-folder files, remained unchanged. The other
  116 installed PTFR files match their previous hashes.
- No REDscript, framework, scene asset, main archive or published release change.

Installed archive SHA-256:
`FABEC35F7E3EFB0A017798C0F464FD17762F8206C2EDA344780C7A3A44B35E24`.

The first workspace build failed because PowerShell resolved `Clear` to its
console alias. The successor uses `ClearFs1`; no failed candidate was installed.
Final build and evidence are under `prealpha/fred_scene_fs1/candidate_02/`,
including `build_01.json`, `tests_01.json`, `deployment_tests_01.json`,
`install_manifest_01.json` and `assessment_01.json`. Sources and evidence are
pinned; use successors.

## Live check and recovery

Cold-launch the game and load retained AutoSave 15 without overwriting it.
Check normal control at H10, then approach Fred and check trade and small talk.
Leave Fred's immediate area and return to H10; his scene should release.
Approach Fred again to check that the interaction returns without a duplicate
NPC. Use a new manual save slot for subsequent reload testing. The existing
loading diagnostic reports `scene/dialogue` after a load; it is not a continuous
attribution trace, and another legitimate scene may also set membership.

Recovery must precede any older S25 archive rollback:

```powershell
& 'prealpha/fred_scene_fs1/deploy_01.ps1' -Action ValidateRollback
& 'prealpha/fred_scene_fs1/deploy_01.ps1' -Action Rollback
```

Backup: `recovery/fred_scene_fs1_01`. File rollback is not save rollback. If a
new save contains the added FS1 wait nodes, use a retained pre-FS1 save when
returning to the old archive. Other recovery chains are unchanged.
