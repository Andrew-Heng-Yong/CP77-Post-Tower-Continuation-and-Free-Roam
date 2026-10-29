# Native ambient action restoration — WA2

The user confirmed that BA1 restored the matched Coastview bottle-shooting
prototype and requested the same repair across affected NPCs. WA2 extends the
repair by native controller type, while retaining BA1 and every existing W3
owner and saved receipt.

## Scope and implementation

The audit covers all 237 W3 prefab owners and the other 240 combat-event prefab
references. It also resolves and parses 168 externally referenced quest phases.
These counts describe source owners/resources, not individual NPCs.

Five additional shooting controllers are selected: groups 172, 173, 246, 250
and 289. Group 250 also needs its original six-node support prefab and an exact
community mapping in the existing Baseline driver. Its compound native alias
was missed by the earlier support census. Admission uses the same matched living
actor and two settled safe samples as W3.

Twenty other groups have separate vehicle ambience branches: native radio,
light and door events. Each uses its own authored event payload and original
actor/vehicle selectors. Native spawn gates remain and also require the current
eligibility facts. Vehicle events fire once per ready lifetime; a safety bounce
does not restart an already-issued radio, light or door event. Native NotReady
ends that lifetime and permits a later gated restart. Shooting owners instead
cut their whole pending controller on eligibility loss and resume through the
native readiness gate. Both retain their claim. The repair does
not replay encounter initialization, reset kill counts, reactivate populations,
reset native quest facts, or reissue rewards.

Source review found three reference problems that require explicit evidence:

- Group 246's four security predicates point into an unbound decoset. The actual
  city security system explicitly connects this exact community; the predicates
  can be rebound without changing their functions or edges.
- Group 256's native readiness predicates refer to a different community.
- Group 319's native spawn predicate refers to an unbound decoset community.

The last two bindings passed a fresh registry review: only their community
references change, preserving native entry names and counts, including group
319's seven-actor requirement. Group 289's
unusual native shooting target is preserved. No target is substituted based on
proximity alone.

## Verification and limits

**Installed on 28 October 2026.** The full 51-path successor replaces only the
combined archive, XL registration and existing Baseline script. All 1,186 prior
archive members are byte-identical; 26 new resources bring the total to 1,212.
All old W3 and BA1 owner resources and receipts are preserved.

Independent verification passed 310 action/support checks and 459 environment,
registry and target checks. Fresh 64-source compilation, every archive member readback,
68-mod-archive collision checks, 23 deployment fixture actions including six
interrupted rollbacks, and actual Validate/Install/Verify/ValidateRollback pass.
All 301 save files and names are unchanged.

The full unreleased ZIP SHA-256 is `005971C576A5CC3788C434332F315595C528758F6D6B90FFAB95A52C641BCE91`.
The manifest SHA-256 is `A8DFB579F6C61C4CC3795CB788399A7CC4EFECE7BED3BFAB056C0AA1820E19EB`.
Final evidence: `candidate_01/assessment_01.json`.

With the game and launcher closed, roll back WA2 first using
`prealpha/world_actions_wa2/deploy_01.ps1 -Action ValidateRollback`, then
`-Action Rollback`. Recovery is `recovery/world_actions_wa2_01`. This restores
the prior BA1 files; file rollback cannot undo state already saved by the game.

The user's live confirmation applies to BA1's matched group. WA2's broader
shooting, vehicle ambience and save/reload behavior have not been observed in
gameplay. Source equivalence and successful installation are not live proof.

Not every native encounter is an ambient controller. Nineteen existing W3
owners have stateful vehicle mounting, story-gated security/attitude changes,
kill cleanup or environment variants. Their exact dependency findings are in
the native contracts; those operations remain untouched.

Outside W3, the remaining reviewed families include spawn/rearm-only graphs,
environment and burning-car setups, dancefloor scenes, attitude changes and
multi-community vehicle deals. The 168 external phases include 47 patrol-role
assignments, 345 combat presets and seven civilian workspot commands inside
encounter state machines. WA2 does not restore those actions or replay their
community resets and checkpoints.

Two unresolved shooting definitions, Vista del Rey group 130 and Rancho group
306, have neither their exact support sector nor their community in the current
native resource and registry census. Group 306 uses a separate weapon-use node
type, which the expanded payload scan also covers. Neither is mapped onto an
existing group. This is complete accounting within the 477-reference census,
not a claim that every NPC family in the game is repaired.

Evidence and reproducible builders are in `prealpha/world_actions_wa2/`:

- `native_review/action_contracts_02.json`: fresh native graph contracts.
- `native_review/fresh_source_proof_01.json`: all W3 native graph readbacks.
- `coverage_review/assessment_02.json`: remaining references and external phases.
- `coverage_review/support_assessment_01.json`: exact group 250 identity/support.
- `environment_review/assessment_01.json`: shooting target/security bindings.
- `candidate_01/`: serialized resources, compilation and deployment proofs.

No game launch, native fact editing, save editing, Git push or public release is
part of this repair.
