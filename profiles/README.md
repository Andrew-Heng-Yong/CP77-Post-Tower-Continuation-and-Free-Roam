# Modular restriction profiles

[Tower Implant Focused](tower_implant_focused/profile.json) is the installed selection in [active.json](active.json). It retains maximum HP 150, unchanged direct stamina, Body 3 with all Body perks blocked, closed Relic, cosmetic-only Casius tattoos and no smart targeting. In the other trees it removes the physical-balance bans and keeps the implant, quickhack, smart-targeting and dependency restrictions. The original [Strict Tower](tower_strict/profile.json) and all five of its source modules are preserved unchanged.

R3 compiles the selected JSON modules into a versioned runtime definition. This is not a live settings menu: changing the selector or modules requires regeneration, testing and deployment, and a reviewed transition for already-active saves. See the [activation and test checklist](../docs/restriction_profile_r3_check.md).

## Modules

| File | Responsibility |
| --- | --- |
| [profile.json](tower_implant_focused/profile.json) | Profile identity, revision, activation, persistence contract and module references. |
| [vitals.json](tower_implant_focused/vitals.json) | HP target and current-health handling; stamina remains untouched. |
| [nerf_rules.json](tower_implant_focused/nerf_rules.json) | Body, Relic, smart targeting, refunds and preservation rules. |
| [cyberware.json](tower_implant_focused/cyberware.json) | Exact approved records, grouped into all ten equipment categories. |
| [perks.json](tower_implant_focused/perks.json) | Exact retained perk records. The blocked list is derived, not separately hand-maintained. |

The [stock catalogue](catalogues/cp2077_231_modern_188.json) defines the 188 exposed modern perk records, ranks and prerequisites. Its source hashes and unresolved bindings are retained. The obsolete `Cool_Right_Perk_3_3` enum record is not a purchasable tree entry and is excluded. This is not a live modded-database census.

The first format supports the reviewed strict rules, alternate finite HP values, and dependency-valid edits to the reviewed lists. It does not support arbitrary script expressions, inheritance, relaxed Body/Relic rules or silent fallback for unknown keys. Such extensions require a schema and runtime implementation update. Module references can share files within `profiles/`; they cannot escape that directory.

## Whitelist size

The active profile retains 93 records and blocks 95: 33 Body, 9 Relic and 53 other-tree records. The preserved strict profile retains 72 and blocks 116. These are perk records, not purchased ranks or refunded points. R3 must be explicitly activated to extend an existing Body/Relic-only save.

| Tree | Retained | Blocked |
| --- | ---: | ---: |
| Body | 0 | 33 |
| Relic | 0 | 9 |
| Intelligence | 2 | 36 |
| Technical Ability | 20 | 14 |
| Reflexes | 36 | 1 |
| Cool | 35 | 2 |
| Total | 93 | 95 |

The new selection restores permission for the 19 physically restricted Reflexes perks and Cool's Deep Breath and High Noon. Lead and Steel, Bullet Deflect, Bullet Time, the blade finisher branch, Dash and Air Dash are allowed subject to native prerequisites. Air Kerenzikov remains blocked. Road Warrior remains blocked as a whole mixed perk because it enables implant operation; Vanishing Act uses Optical Camo. Lucky Day remains blocked because its required All Things Cyber parent is blocked; no native tree is rewired.

All eight smart-weapon branch perks stay blocked. Eye in the Sky and ForceKill Cypher remain allowed. Parasite, Creeping Death, Finisher: Act of Mercy and Pounce remain allowed. Body is the explicit exception to the implant-focused selection: the user kept Body 3 and the complete Body-perk ban.

Cyberware also uses a whitelist: eleven Basic Kiroshi records and two Casius records, representing two approved models. Empty categories are intentional. Personal Link, Base Fists and Splinter stay outside the selectable-implant list. Unknown cyberware is denied installation without destroying owned items. By contrast, an unknown or changed perk catalogue stops a progression migration before mutation; the complement must never mean “refund every unrecognized modded perk.”

## Tattoo permission does not permit smart targeting

Both `Items.CasiusTattoo` and `Items.AdvancedCasiusTattoo` retain item permission for their appearance. A functional denial takes priority over an item permission. Basic Kiroshi keeps its separately approved stock effects; this does not introduce a general stripping of all passive bonuses.

The earlier claim that Johnny's tattoo has no practical Smart Link effect was too strong. Empty inspected equip packages do not establish the complete effective behavior, including parts, native paths and other mods. Neither the current whitelist nor removing smart-weapon perks independently proves that smart lock-on/homing is disabled.

R3 adds player-owned HasSmartLink and smart-weapon lock-count modifiers, a straight-shot request before firing, and smart-handler disabling, including the vehicle path. Weapons and inventory remain owned; NPC and pre-Tower paths are excluded. These native calls compile, but actual lock acquisition and projectile homing still need an in-game test, especially on self-targeting iconic weapons. HUD appearance alone is not proof.

## HP and progression semantics

`health.value` is the requested final maximum, not a refill command or an additive bonus. The strict profile selects 150; it is not “base 150 plus buffs.” R3 reconciles an owned, unsaved Health multiplier against the effective maximum. It never removes foreign modifiers or forces a shared stat override. It checks the health pool after changes, submits at most one downward correction, and waits for acknowledgement. It never sends a positive health request. Native pool scaling, buff transitions and save/load behavior remain live checks. No direct stamina modifiers, regeneration changes or pool writes are made; removing approved banned perks can naturally remove their stamina benefits.

Body stays at 3, Body/Relic purchases remain blocked, and the Relic category stays hidden. Refund only actually purchased ranks, through native guarded sales in dependency order. Refund attribute points once. Relic points return to their own pool and remain unspendable under the active rule. Other attributes, level, skills, XP, items, installed parts, Personal Link and story facts are preserved.

The rules are one-way progression changes: switching a profile never repurchases refunded perks or restores a former build. The existing No Nerf path is a policy pass-through, not a reversal API.

## Save migration contract

Automatic Cyberware Only activation remains unchanged, now including the smart-targeting restriction. Full Nerf requires explicit activation after genuine Tower completion. Installation does not refund progression or enable the HP module. `PTFR.RestrictionsR3.ProfilePolicy.FullNerf()` enables the full profile; `FullNerfWithoutVitals()` excludes direct HP/stamina changes. The old R2 command delegates to the new no-vitals command.

R3 saves its profile identity, revision, content fingerprint, selected other-tree bans, HP target and transaction journal per save. A mismatched compiled definition stops the R3 migration without restarting refunds. The R2 schema and completed refund counters remain intact. Once Body/Relic finishes, R3 snapshots current legitimate progression and refunds only the selected other-tree ranks. Do not deploy modified definitions over an activated save without a separately reviewed migration; no arbitrary profile-switch or hot-reload API exists.

The installed implant-profile update accepts only the two reviewed strict fingerprints, their exact 74-entry saved selection, matching revision/HP pairs, enabled stages 1 through 4, and no in-flight transaction. On load it replaces only the profile identity, revision, fingerprint, blocked selection and HP target. Expected progression, stages, historical starting/refunded counters, tattoo-relocation state and vitals activation are retained. Faulted or unknown saves still stop; migration is not a repair API. A partially finished refund continues only for remaining restricted ranks. A completed refund is never replayed.

Already-refunded ordinary skills are not automatically restored: use the retained points to purchase eligible skills normally. The historical refund denominator can still describe the former strict plan. No-vitals saves remain off. An older strict revision 1 save also adopts the already-approved 150 target. Restoring old files does not revert saved profile metadata; retain a pre-update disposable save.

The existing command that excludes vitals must continue excluding HP/stamina writes when the new adapters are introduced. Retain old persisted fields and guard queued work with the existing epoch/ownership pattern. Do not rewrite Tower completion or Relic unlock facts to implement this profile.

## Validation and runtime readiness

From the workspace, using the project's Python runtime:

```powershell
python -B tools/validate_restriction_profile.py --verify-installed
python -B tools/test_restriction_profiles.py
python -B tools/validate_restriction_profile.py --require-runtime
```

The first command checks definitions and installed-source hashes without changing files. Tests cover approved selection, dependency closure, malformed values, catalogue drift, unsafe policy edits and path boundaries. Exit 0 means a valid definition; exit 2 means invalid input; `--require-runtime` exits 3 unless matching offline runtime evidence exists. `runtime_ready=true` means a matching compiled adapter, not live verification. No command above installs or activates a profile.

The selector feeds `tools/build_restrictions_profile_r3.py --write`. The current implementation audit is `research/restriction_profiles/profile_implant_r3_2/tests.json`; its build test and deployment fixture are predecessor-pinned and must not be rerun blindly after installation. The current recovery script is `tools/deploy_restrictions_profile_implant_r3_2.ps1`, covering two backed-up replacements and no additions/removals. Prior R3/R3.1 installers are historical for these paths. Do not use the selector as an unreviewed downgrade mechanism.

The exact stock Built Different level binding `91068214685` is absent. R3 validates that specific absence and returns no GLP only during its own acknowledged rank sale, avoiding the native-script null dereference without inventing a replacement package. Ambidextrous requires Hands slot 2 empty: R3 can relocate an approved tattoo into an empty first slot with item/part readback. If both are occupied, the migration waits for the player to clear one.

Live refund amounts, effect removal, no-free-heal behavior, real smart-projectile behavior, save isolation and cold reload remain required before a runtime release claim.
