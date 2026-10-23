# N2 — Citywide NCPD scanner restoration

## Current — N2.2 user-reported visibility/functionality pass

14 October: the user reports the missing activities are restored, visible on the
map and working. No repeat basic visibility test is needed. This does not establish
exhaustive completion/rewards for all 157 encounters, new-save/reload, or fresh-ending
coverage. The installation and original test steps below are retained as history.

One existing script was replaced; all quest archives and encounter owners are
unchanged. For an already-issued, unfinished native encounter with independent
completion facts, an inactive journal entry can now activate even if its saved
marker record is absent. Completed/terminal entries and unavailable game systems
remain blocked. No synthetic icons, native progress resets or console chatter.

Quick check:

1. Cold launch and load **AutoSave-9 — level 48, 14:20:26 on 14.10.2026**.
   Its verified `sav.dat` SHA is
   `4239ED680E1970223F474B01FA3FB689139998D877294AB333BC79176F3DD412`.
   This is the existing post-Tower save with the issued encounter owners.
2. Close CET and menus for **20 seconds**. Check the previously sparse City
   Center, Heywood, Westbrook, Santo Domingo and Pacifica maps with NCPD enabled.
3. If convenient, approach **one newly visible** encounter. The already-working
   Westbrook encounter does not need another full playthrough just for this fix.
4. Later create a **new save** and reload to test persistence. Keep this original
   fixture; its byte-exact backup is under
   `research/ncpd_n21_live_20261014/snapshot_03/AutoSave-9`.

No ending replay, startup command or forced facts are needed. If markers are
still missing, this getter is read-only and should identify the version as N2.2:

```lua
print(Game.GetScriptableSystemsContainer():Get("PTFR.NCPDRepairN21.ScannerRepairN21"):Inspect("ma_cct_cpz_01"))
```

`phase=-2` means the saved-marker lookup found no record; `-1` means unavailable
systems/entry or delayed journal changes. `mapAck=1` remains entry-state evidence,
not independent proof of a rendered icon or playable encounter.

Limits: the six supplemental startup-permission paths remain unchanged, and
previously started encounters are still separately guarded. Five table entries
without independent completion facts do not use the missing-record fallback.
This fixes the broad activation gate, not every remaining eligibility exception.
Compilation/full mod integration, 24,576 policy cases and 46 installer cases/63
checks passed offline; actual visibility and new-save/reload are pending.

Recovery **N22 first**: `prealpha/ncpd_marker_n22/deploy.ps1`
`ValidateRollback`/`Rollback` with `recovery/ncpd_marker_n22_01`; then N21, C1,
N2, N1, FO1 and older transactions. Installed N22 sources/build/tools/reports are
pinned. Evidence: `research/ncpd_marker_n22/assessment.json`.

## Earlier — N2.1 still misses most non-Watson markers

The user reports Watson looks fully restored, but Westbrook, City Center,
Heywood, Santo Domingo and Pacifica still show only one or two scanners.
One visited Westbrook encounter works. This is a **citywide visibility failure**,
not a completion/reward/reload pass or proof all Watson content works.

The latest run compiled successfully and merged all 154 N2 plus six N21 phases.
Read-only AutoSave-9 inspection (14:20:26, 14 October) finds 128 startup requests
issued, but only 24 N21 marker acknowledgements. City Center has 10 issued/0
acknowledged, Heywood 19/0, Pacifica 11/0, Santo Domingo 21/2 and Westbrook 12/1.
These are saved ownership facts, not rendered-object counts.

The repair still requires saved marker data before activating an inactive
journal POI. Its helper returns -1 when that lookup fails and does nothing.
Raw save evidence strongly supports missing marker records as this blocker:
all 24 acknowledged entries have their hash in the saved POI node; most issued,
unacknowledged entries do not. This is corroboration, not a captured live getter
result or a fully validated POI binary decoder. Watson's native prefixes already
activate entries, unlike most other districts' phase-only prefixes.

Next repair: remove that circular dependency only for safely admitted,
unfinished native entries; retain completed-content guards and do not restart
owners or reset progress. Supplemental/factless admission needs separate care.
No new patch was installed in this diagnostic turn. No repeat ending/playtest
is needed yet. Current N21-first recovery and pinned artifacts remain unchanged.

Evidence: `research/ncpd_n21_live_20261014/assessment_01.json` and frozen
`snapshot_03`. The save was made before the logged Westbrook start at 14:20:49;
do not infer completion from it.

## Earlier — N2.1 installation and initial test instructions

The missing native entry activation is now handled after an N2 encounter owner
is issued. Native marker phase/type is preserved; completed or terminal POIs
are not activated. There are no synthetic icons, native progress resets, reward
repairs or console chatter. Existing issued owners are not restarted.

Six guarded native startup paths cover Charter Hill 02/03/04, Rancho Coronado 07
and the factless-start CPZ16/NOK05 exceptions. The first four stock start flags
are initialization flags, not proof V visited the activity. They require exactly
one prior initialization and unfinished POI/completion state. Other previously
started scanners are still protected: this is **not generic partial-progress
migration**, nor a claim that every unfinished activity is now playable.

Quick test:

1. Cold launch and load **AutoSave-8, level 48, 12:10:04 on 14.10.2026**.
   Its `sav.dat` still matches the SHA below. No ending replay or forced facts.
2. Close CET/map/menus for **20 seconds**. Then check the same City Center,
   Heywood and Westbrook areas with the NCPD filter enabled.
3. Visit one restored marker and check for the native encounter/evidence. Later,
   make a **new save** and reload it; keep the original fixture unchanged.

If something remains missing, this read-only getter checks a representative
Corpo Plaza scanner (replace the ID for another known scanner):

```lua
print(Game.GetScriptableSystemsContainer():Get("PTFR.NCPDRepairN21.ScannerRepairN21"):Inspect("ma_cct_cpz_01"))
```

`mapAck=1` is an entry-state acknowledgement, not rendered-icon/gameplay proof.
Unknown saved POI data defers activation. Compilation, native payload/resource
comparisons and deployment/rollback fixtures passed offline; actual visibility,
completion, reload and fresh-ending integration remain unverified.

Evidence: `research/ncpd_n2_missing_20261014/repair_install.json`.
Recovery now starts with `prealpha/ncpd_repair_n21/deploy.ps1`
`ValidateRollback`/`Rollback` using `recovery/ncpd_repair_n21_01`, then C1, N2,
N1, FO1 and older transactions. N21 installed sources/build/tools/tests/receipts
are pinned; do not rerun or overwrite them.

## Earlier diagnosis — 14 October: missing-activity regression

The user compared the supplied map areas against a pre-ending save and confirmed
missing scanners. **Do not treat N2 as a citywide visibility pass.** The latest
run compiled and merged all 154 additions; installed files match their build.
Stock Tower cleanup deactivates scanner POIs. Unlike the Watson pilot, many
native district startup nodes only change marker phase and do not reactivate
the entry. N2 retained that incomplete post-Tower startup path: 92 phase-only
prefixes, including all City Center, Heywood and Westbrook entries in this batch.
This is a source-level restoration gap, not proof of every live marker state.

Separately, fresh-only admission excludes previously started, unfinished
scanners, including Charter Hill 02/03/04. Those start facts were already present
before Tower. Their gameplay resumption needs separate handling; merely adding
markers or clearing progress is not a repair. Completed encounters must stay
completed. No runtime patch, save edit, settings change or game launch was made
during this investigation. Evidence:
`research/ncpd_n2_missing_20261014/findings.json`.

The checklist below records the original installation test; citywide pass and
new-save/reload are still pending the N2.1 live check. No further full playthrough needed
just to reconfirm this report.

Installed 14 October 2026. The user reports the three-activity N1 pilot works;
the **154 added encounters are implemented, not individually playtested**.
Together the packages cover 157 stock-connected scanner owners across all seven
regions: 114 Assault/Gang Watch, 26 Reported Crime/Hidden Stash and 17 Organized
Crime/Outpost POIs. These are catalog totals, **not the expected number of new
icons on this character**.

Completed and already-started pre-existing activities are not reset. Stock
tier/story/follow-up gates remain. Partial-progress migration and certified
pre-Tower scanner history are not implemented. Four journal-only entries without
connected district owners are not activated. Cyberpsychos remain untouched.

## Short test now

1. Cold launch and load **AutoSave-8, level 48, 12:10:04 on 14.10.2026**—the
   current post-Tower save from the working pilot. Match the timestamp, not just
   the slot. Its metadata says `ma_wat_lch_01_start`; that pilot owner must
   continue without being restarted. No ending replay, overrides or `StartAll`.
2. Once in control, close menus/CET for about 10–15 seconds. Enable **NCPD
   Scanner** in the map's Custom filter. Look across several districts, not only
   Little China. Only eligible remaining encounters should appear.
3. Visit any one newly appearing scanner. Check for actual enemies/evidence or
   the expected clue interaction. A marker alone is not a working-activity pass.
4. Make a **new save**, reload it and check that the encounter remains usable,
   with no reset or duplicate reward. Keep the original test fixture.

No need to complete every scanner immediately. The expanded batch still needs
representative gameplay coverage; the remaining checklist can wait.

The three original files are backed up byte-for-byte at
`recovery/ncpd_n2_fixture_20261014/AutoSave-8`. Original save files were not edited.
`sav.dat` SHA256:
`A7A55B53FAE56E8EB70485711A9B9BBE8DE3159DCC34E9C7F62ABDCABC59A12B`.

## Later coverage

- [ ] Each region: Watson, Westbrook, City Center, Heywood, Santo Domingo,
  Pacifica and Badlands has eligible encounters with real content. Existing
  completed or story-gated sites are not failures merely because they lack icons.
- [ ] Assault: resolve enemies and evidence, receive native payout once, leave,
  return and verify no replay.
- [ ] Reported Crime: collect the first clue, follow the stock trail, resolve the
  destination, and check objectives/marker removal and native reward once.
- [ ] Organized Crime: dispatcher briefing, enemies/evidence and completion;
  a later ordinary gig call still works. A dispatcher call is not required for
  every scanner subtype.
- [ ] Record the relevant district achievement counter before/after an isolated
  completion. The stock phase or parent awards it; no synthetic counter repair.
- [ ] Save/reload during activity and after completion. Native owner state and
  one-shot admission must survive. Existing N1 owners must not restart.
- [ ] Check an already-completed scanner and the completed cyberpsycho set:
  no respawn, renewed Regina reports, repeat reward or extra credit.
- [ ] Special native paths: Kabuki06 reset branch, CPZ15/16 cleanup, CVI11
  prerequisite/setup chain, CVI13 alternate output, Badlands alternate outputs.
  Do not force prerequisite facts to manufacture these tests.
- [ ] CPZ16 and NOK05 have no authored start fact. Confirm their saved native
  POI state can be read; missing information safely defers them. Discovered or
  completed POIs are not restarted. This API behavior still needs live coverage.
- [ ] Existing gigs, fixer conversations, H10, camera/nerfs and quiet console
  remain unchanged.
- [ ] Later integrated alpha: a genuine pre-Tower run does not activate these
  owners during Tower or credits; they become eligible only after handoff.

## Read-only diagnostics

For any new encounter, substitute its native ID below. `Issued=1` means its
native branch was admitted, **not proof that an icon rendered or a reward ran**.
N2 does not add custom completion acknowledgements.

```lua
local id="ma_wat_kab_01"; local q=Game.GetQuestsSystem(); local p="PTFRN2_"..id; print(id.." ready/issued/refused="..q:GetFactStr(p.."_Ready").."/"..q:GetFactStr(p.."_Issued").."/"..q:GetFactStr(p.."_Refused"))
```

For the two saved-POI exceptions only:

```lua
print(Game.GetScriptableSystemsContainer():Get("PTFR.NCPDScannersN2.ScannerAdmissionN2"):Inspect())
```

```lua
local q=Game.GetQuestsSystem(); for _,id in ipairs({"ma_cct_cpz_16","ma_wbr_nok_05"}) do local p="PTFRN2_"..id; print(id.." request/permit/denied/issued="..q:GetFactStr(p.."_Request").."/"..q:GetFactStr(p.."_Permit").."/"..q:GetFactStr(p.."_Denied").."/"..q:GetFactStr(p.."_Issued")) end
```

Saved POI phases: `-1` unknown, `0` completed, `1` default, `2` discovered,
`3` undiscovered. They are **not** Journal entry-state numbers. No state is
modified by these diagnostic commands. Do not clear native or mod-owned facts.

## Recovery

Close the game. If C1 is installed, recover C1 first as described in
[the courier checklist](courier_c1_playtest.md#recovery). Then recover N2 with
`prealpha/ncpd_scanners_n2/deploy.ps1` using `ValidateRollback`, then `Rollback`,
and the exact recovery directory `recovery/ncpd_scanners_n2_01`.
Only the three added N2 files are moved recoverably; N1 and earlier repairs stay.
Then, if needed, recover N1, FO1, PA6 and older transactions in that order.
File rollback cannot undo encounter progress written into a later save.

Evidence: `research/ncpd_scanners_n2/assessment.json` and
`prealpha/ncpd_scanners_n2/build/n2_05/`. Compile, native payload/edge checks,
packed readback and installer fixtures passed; full citywide gameplay is pending.
