# Candidate02 and read-only preflight review

Status: **approved for offline preparation only**. Candidate02 contains the previously approved unchanged Lua SHA256 `1A366E1075A9EBCA46686EF76AB724B7F5C3EE51445E13A3BC02B97194D21F90` and narrowed watch configuration SHA256 `A1AAB30B9F896CD24687D82CC2160D773C04B7193BDDCA71CC933A4C93997AAA`. Manifest02 SHA256 is `15DD32010CDF40D0DFD8795554F5F2E61A22672FE11D0B4A0CB80366E5641CDE`.

## Conditional D00 natural-event card

The one watched fact is now `phonecall_player_with_regina_jones`. Independent source inspection confirms the native Regina questphase's contact binding `contacts/regina_jones` (JSON SHA256 `D14741DB0749653E8A5985732CDA3440F7B96847DE6F01B5FAD4CB413054E051`). The preserved `newHudPhoneGameController` passes `contactData.contactId`, `MessengerUtils` obtains it from `contactEntry.GetId()`, and `PhoneSystem.GetPhoneCallFactName` constructs the lowercase player/contact fact. This supports the expected fact selection as a derived natural-test target.

These are preserved historical decompiled scripts; their exact match to the current compiled phone implementation and current callable-contact availability are not independently observed. The card must require an already visible Regina **Call** option and skip if absent. It must not reset history, enable a contact, accept or restart a job, or infer call/controller ownership from a sampled transition. A successful natural difference will validate sampling for that fixture, not native callback delivery. This conditional diagnostic card does not repeat passed Wilson, Bullets, Zane shop or reload acceptance tests.

## Read-only preflight

Reviewed `preflight.py`, SHA256 `CAF56A95A465AF313188382E233CA50CB3294FA83BD6A5D82498AAA4A68E1432`. It has **no install or rollback action**. It reads exact managed diagnostic leaves, source and rollback-donor hashes, Core/dependency pins, current save hashes and process names, then writes only a fresh report. The existing actual `preflight_before_02.json` reports 57 Core/dependency pins and 310 unchanged save-file hashes; the reviewer inspected that receipt rather than repeating the same save hashing. This is a preparation check, not a deployment transaction or live runtime result.

Two source defects in result-output confinement were found and corrected during review:

1. The original `Path.absolute().is_relative_to()` check was lexical and accepted `../qr10_scope_escape.json`. The reviewer demonstrated the bypass without opening or writing an escaped file. The final helper permits one bounded ASCII leaf, verifies the task-root ancestor chain and resolved containment, and rejects occupied entries with `lstat`, including broken links.
2. The initial replacement still accepted Windows reserved device names such as `COM1.json`. The reviewer demonstrated helper acceptance only, without opening the device. The final helper rejects `os.path.isreserved(name)`.

The fixture suite now uses the same final output guard. Independently executed `test_preflight.py --out review_preflight_recheck_01`: **19 controls passed**, including before/after exact bytes, wrong-leaf/hash and process refusals, unknown-log preservation, containment and junction rejection, traversal/absolute/nested/ADS output refusal, reserved devices and occupied outputs. Result: `../review_preflight_recheck_01/results.json`. No unresolved blocking finding remains in the reviewed read-only preflight.

## Boundaries

No game/CET module was loaded or executed; no gameplay was operated; no installed file, save, Core resource or prior QR9 observation was modified. Candidate02 remains uninstalled. This review does **not** certify an atomic two-file install, interruption/crash recovery, a deployment receipt or an executed rollback. Any later deployment needs separate authorization and a fresh guarded transaction; the QR9 absent-target installer must not be reused for an overwrite.

Native callback delivery remains unsupported and unverified. Live sampled differences remain untested. Exact graph/listener ownership, engine phone acknowledgement/cleanup, timer persistence, controller termination and reward idempotence are not established by these preparation checks.
