# D00E narrow independent review

Status: **approved for offline preparation only**, with no blocking finding. No real deployment, gameplay or save action was performed by this reviewer.

Reviewed exact installer `A25BD28C015AD45401A8F1C16D58D58A769CC0C6BB1146E68EC44FDDF08AB66B`, manifest `C4BC8A6AB6FDF2948DAF7C2F04EDDB34B8287FA9794040701D09E48E9160B5F5` and successor watch configuration `BBEFAEC2F1975EE0590BEC6D447293AF932DFBCCF2C228393133604F6D252DEA`.

## Exact scope

Independent comparison against the pinned QR10 candidate02 configuration confirms that removing `profiles/D00E` yields semantic equality with the prior configuration. D00E watches only `phonecall_player_with_muamar_el_capitan_reyes`, with no journal targets. Existing profiles, source declaration, version and all other fields remain unchanged. No Lua or Core payload is included.

The installer differs from approved parent `400438835F72415A78D6604EC9551034A2967BEB42206132FC94714E8496806E` only in the new manifest pin, nested-directory correction to the same QR9 shared lock, private recovery name, and exact managed allowlist/count of one existing `watch.json`. The original 58 required inputs are identical; the unchanged Lua SHA `1A366E1075A9EBCA46686EF76AB724B7F5C3EE51445E13A3BC02B97194D21F90` is the 59th protected input. The two-file wording in the inherited comment does not change the enforced one-file write set.

Rollback restores the previous D01 configuration SHA `A1AAB30B9F896CD24687D82CC2160D773C04B7193BDDCA71CC933A4C93997AAA`. If a later rollback of the parent diagnostic deployment is requested, this profile update must be rolled back first; the parent correctly refuses its after-state check while the successor watch bytes are installed. File rollback never reverses a save.

## Contact and direction evidence

Independently located native graph parent node52 and nested condition node6 by IDs, rather than reusing the preparer's array indices. The `questPhone_ConditionType` is `IncomingCall`, caller `contacts/player`, addressee `contacts/muamar_el_capitan_reyes`. Native resource JSON SHA is `F4FC6E96DF5DD6C28A9CF156E33F3FE90FF032392C5BFB99C2504625A4DDCE9A`.

The preserved `PhoneSystem.GetPhoneCallFactName` builds `phonecall_` + lowercase caller + `_with_` + lowercase addressee; its source SHA is `BF483F7F6BB2706171998892B8554485EA47B4984AF4C9DF2C8C3C4137AF21E7`. The phone UI derives the call recipient from the journal contact ID. Together these support the expected outgoing El Capitan fact name. They do not prove the current compiled controller's write timing or current Lua sampling delivery.

The human has explicitly confirmed that El Capitan is callable and offers dialogue, so this is an appropriate replacement for unavailable Regina D00. The exact loaded save slot remains unconfirmed; do not relabel the observation as a particular slot or independent Tower-lineage proof. If the Call option later disappears, skip as NOT_TESTABLE without enabling a contact, changing facts, replaying a job or accepting a quest to create eligibility.

## Verification and boundaries

Inspected and independently checked the existing `test_result_01.json` binding to the exact current installer, manifest and watch hashes: **10 checks and 12 fixture actions passed**. The actual unchanged Lua source was exercised with one D00E baseline getter, two synthetic sampled differences, zero native registrations and no `FACT_DELIVERY` claim. One-file installation, verification, rollback readiness, exact rollback, hard-interruption recovery, unknown-config refusal, Lua drift refusal and wrong-scope refusal are included. No duplicate fixture run or broad suite was performed by the reviewer.

For the eventual manual card, start D00E before a normal outgoing El Capitan call, leave natural call states visible long enough for two-second sampling, then stop capture. Do not claim native callback delivery, exact native-write order or missed intermediate states. Successful sampling still requires a real natural change and human correlation. Native callbacks remain unsupported; the gameplay call's success does not by itself validate the observer. Do not repeat Wilson, Bullets, Zane shop or completed reload tests.

This approval covers prepared source/configuration and existing offline fixtures only. Final readiness and fresh closed-game preflight remain separate, and this update has no real-deployment authorization from the reviewer.
