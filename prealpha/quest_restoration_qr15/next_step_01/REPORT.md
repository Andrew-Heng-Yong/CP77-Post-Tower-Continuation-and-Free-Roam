# QR15 next step — exact saved-root and car binding

The offline feasibility work is complete. **No native inspector or quest repair is selected or installed. One new, narrowly targeted manual getter check (JF02) is prepared.** It uses the source-bound absolute car reference, rather than repeating JF01's short-alias query. [One-command card](../runtime_probe_02/TEST_CARD.md).

## What changed in the evidence

1. The exact native engine cleanup path is now traced beyond graph topology: CutControl emits the cut first; the executor drains its destinations before dispatching Out. A cut to the actual phase recursively calls handler Uninitialize, erases handler registrations and removes child phases before returning. This closes the source ordering question. It does **not** acknowledge completion of external prefab/community/spawner lease release or establish every current executing owner. [Native review](../saved_graph_state_01/inspector_review_01/REPORT.md).
2. The same already-pinned historical AutoSave-8 was inspected read-only. Exactly17 parent bytes between FactsDB end and customArray start were extracted, with13 native offset/ID controls and unchanged source/metadata hashes. The native stream version is the header's **SaveVersion277**, independently distinguished from GameVersion2500 and ArchiveVersion195. This body uses the modern saved resource-array layout.
3. The two saved resource hashes resolve uniquely to base cyberpunk2077.quest at index0 and ep1.quest at index1. The complete Jason gameplay startup path is **[1,0,10,5,2,50,19,5,1]**, with native seed1=0x01800013 and phase hash0xA0D58F1A. The earlier guessed outer path is superseded for this exact body. This is source/serialization binding, not a visited or liveness decoder. [Binding addendum](../saved_graph_state_01/inspector_review_01/ROOT_BINDING_ADDENDUM.md).
4. Fresh vanilla world-block/sector evidence binds the broken-car spawner to typed sector node98/globalID17433794865907239043 and an exact absolute reference. Its sector is quest-owned by the native gunfight prefab. The WKit9.1 default node-index export uses an incompatible layout for this sector; the review decoded the pinned current2.5 packed layout and checked all101indices instead of joining nodeRefs by position. [Car binding](../runtime_probe_01/car_binding_review_01/REPORT.md).

The historical save source is SHA256 AE7331494F242FDCFA9008D86588F9C431B9ABA6092B7E9C845EE78D3D30CE9E. It is not proven to be the body loaded during JF01. No source-only binding is presented as a live observation.

## Why no native plugin

MSVC14.44 is available and the SDK offers TryLockShared, but that is insufficient qualification. Native ordinary mutations use the quest mutex; root initialization has an unclosed outer lifecycle/thread boundary and teardown clears the global path map after releasing the lock. A manual CET raw-tree reader cannot be represented as a coherent, safely admitted owner snapshot from this evidence. The saved resource array solved the immediate path-binding question offline, so no DLL was built and no new dependency installation is requested.

## Verification, kept separate

| Evidence/check | Result | Scope |
| --- | --- | --- |
| Root provider capture | Four single-provider resources,134archive indexes, no missing/decode failures | Read-only extraction, no build |
| Parent-gap extraction | 13 offset/ID controls,17bytes | One pinned historical body only |
| Exact engine review | 18 static checks | Cleanup ordering, version/root schema and inspector boundaries |
| Strict array decoder | 16 controls, including malformed inputs | Negative zero, overlong/overflow/truncated arrays refuse |
| Car binding | 34 controls | Exact type, setup index, hash/reference and ownership binding |
| JF02 primary controls | 21 PASS | Lua syntax, refusal/error paths, source pins/read-only allowlist |
| JF02 independent review | 23 PASS, no blockers | Concrete command/source review; no live Game calls |

These counts overlap in inputs and must not be summed into a quest coverage percentage. None certifies gameplay success. The proposed command reports exposed stored-list sizes; lists can overlap and are not unique/live car counts.

## Remaining repair requirements

The full native16-branch startup still needs a complete preserve/rearm/hold disposition. Source-level graph-registration cleanup is now established for the cut path; completion of external world leases is not. Car visual-destruction/door setup, pending VehicleSpawned behavior and support refresh are not proved by an ordinary spawner lookup. An isolated gameCommunitySystem RTTI lookup did not establish its instance vtable and was rejected; ordinary Activate idempotence is still UNKNOWN. No replay, reset, fresh-admission bypass or synthetic history certificate follows from these findings.

JF02 answers only whether the exact car reference resolves and what its existing getter fields contain. A result can narrow registration/state uncertainty; it does not automatically authorize a repair. No successful quest, Ronald enrollment/reload, Bullets/Jinguji, Wilson, Cynthia, D00E or Jeopardy test is requested again.

## Preservation

All77 installed Core/dependency hashes and all six original ManualSave23/24 file hashes still match the baseline. GG1 is STOPPED. The raw preservation check also exposed a previously updated **mutable QR14 checkpoint** hash, while all three immutable baseline document/source manifests matched. Its unchanged installed-state/completion fields and JF01 continuation update were reviewed explicitly; this is bookkeeping drift, not silently promoted to an all-pins PASS. See `preservation.json` and `preservation_assessment.json`.

No runtime resource, installed diagnostic, save/fact, release package or game process was modified. No compile, archive rebuild, deployment, game launch, CUA, publication or push was performed.
