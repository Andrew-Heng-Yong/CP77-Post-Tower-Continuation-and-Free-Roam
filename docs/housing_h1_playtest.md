# Housing H1

H1 implements the post-Tower home rule and was installed on 23 October 2026.
Final build: `prealpha/housing_h1/build/h1_02`. Package and installation evidence
is in `research/housing_h1/assessment_01.json`. Full compilation, compatibility,
compiled guard review and installation/rollback checks passed. All 215 existing
save files and five cache files were unchanged. These checks are not a substitute
for the live checks below.

## Expected behavior

The five ordinary homes are H10, Northside, Japantown, the Glen and Corpo Plaza.
Their home markers, private fast travel and home services require a post-Tower
purchase. Shared stash contents and old purchase history are preserved. Public
building access and egress remain available; this is an entitlement change,
not a replacement of building geometry or every door lock.

H10 costs €$25,000. The four rentals quote the current game's normal price.
Visit the property to buy: H10 uses its existing front-door interaction and the
other rentals use their original local purchase prompts, followed by a payment
confirmation. Website purchases redirect to the property so they cannot charge
outside the saved receipt system. Cancel and insufficient funds must leave both
money and ownership unchanged. A purchased home must never charge again.

Kerry's house retains genuinely earned friendship/relationship access, with no
fee and no Kerry quest or actor revival. Judy, River and Panam homes do not gain
a purchase route or an additional retained-home exception. An interaction
already running when upgrading must be allowed to finish safely.

## Live checks before beta release

Use a separate manual test save on the current working post-Tower branch. Keep
the original save. No ending replay is needed for the existing-save checks.

1. Load and let the normal safe-state preparation finish. Confirm the working
   H10 street arrival/camera is unchanged, movement remains available and there
   is no duplicate opening transition or profile refund.
2. Before purchase, check home markers, private apartment fast travel and home
   services at an owned rental and H10. Verify public transit, doors and exit
   from a save loaded indoors remain usable.
3. At H10 and a rental, cancel once, try insufficient funds if a suitable
   existing test save is available, then purchase normally. Record cash before
   and after. Confirm one exact charge, restored services and no second offer.
4. Save, quit fully and reload. Check the receipt, ownership, shared stash
   contents and restored services. Repeat after death/checkpoint reload.
5. Check a never-owned rental retains its normal prerequisite and price. Check
   apartment website links cannot charge separately or alter native purchase
   facts. Makeovers and unrelated websites should still behave normally.
6. Check earned Kerry access without Kerry appearing; check the other
   relationship homes do not retain home services or purchase prompts.

A separate genuine pre-Tower fixture must traverse the ending and initial
arrival before public release. Also retain beta fixtures with an unpaid home,
a paid home and an unfinished restored quest. The successor release must load
those exact saves and preserve cash, ownership, quest stage and rewards.

## Read-only inspection

Using the same CET system lookup as the existing U10 diagnostics:

```lua
local s = Game.GetScriptableSystemsContainer():Get("PTFR.Housing.HousingState"); if s then print(s:Inspect("h10")) else print("Housing system unavailable; check the compilation log") end
```

The callable REDscript API is
`PTFR.Housing.HousingState.Get(game).Inspect(id)`, with IDs `h10`, `northside`,
`japantown`, `glen` and `corpo`.
Do not set housing facts to simulate ownership or repair a receipt.

Receipt states: 0 unpaid, 1 debit in progress, 2 paid, 3 native access confirmed,
4 uncertain. An uncertain result stops automatic retries; it is not permission
to infer payment from the current balance, charge again or grant ownership.

File rollback does not undo purchases or other changes already saved in-game.
Retain both the H1 files and an H1 save when testing later upgrades. See
[the beta save contract](beta_release_contract.md).

H1 must be undone before S28 or older packages. From the workspace, with the game
closed, validate first:

```powershell
& ./prealpha/housing_h1/deploy_01.ps1 -Mode ValidateRollback -RecoveryRoot (Join-Path $PWD 'recovery/housing_h1_01')
```

To perform the file rollback, use the same command with `-Mode Rollback`.
Keep the recovery directory; do not delete or replace its saved original files.
