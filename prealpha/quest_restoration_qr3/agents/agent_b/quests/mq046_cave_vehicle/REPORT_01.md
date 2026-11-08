# Murk Man Returns Again Once More Forever — QR3 deep-contract findings

All ten contracts were investigated. **No source-confirmed defect or gameplay repair; not fully STATIC_VERIFIED.**

Native resource: `base\open_world\minor_activities\badlands\inland_avenue_se1\ma_bls_ina_se1_40\ma_bls_ina_se1_40_phase.questphase` SHA256 `89F0E9A6AE3F619ABD75410AF677F0CE5D1F3105017BA61C2FBA41F22EA86399`. Private boot: `towercontinued\sidejobs_s23\ep1\mq046_boot.questphase` SHA256 `5DA46C136ECDD5945D9667A5871C723B48A0DCF13A85F512DDC7C1B4E0D07825`.

{"APPROVED_DEVIATION": 1, "CONDITIONAL": 5, "PASS": 3, "OPAQUE": 1}

The exact nodes, predicates, sockets, progression, journal transitions, item/vehicle grants, cleanup and remaining limits are in [contracts.json](contracts.json). Detailed original/current models and all edges are in [graph evidence](../../verification_01/graph_evidence.json); [source pins](../../verification_01/source_pins.json) bind raw binary, JSON, normalized input and provider identities. The two-quest verifier passed210 checks including8 actual-resource mutation controls; counts describe assertions, not gameplay coverage.

The private wrapper keeps original district173 seven-tick delay and141.In1; it adds the already-existing S23 genuine-Tower/fresh-history/vehicle-not-owned/once-only wrapper and two-tick postclaim recheck. It does not alter the native activity body or reset history. Native local Onscreen email interaction is not phone SMS. Native supporting Johnny voiceset is retained under JV1 visual suppression, with rendering/camera scheduling live-only.

Remaining static inputs: exact vehicle/keycard TweakDB targets, streamed prefab/trigger/variant bindings, and full original world-owner retirement path. Saved owner transitions and actual entitlement/VO/unload effects require live evidence. No source change is justified by these gaps.

Reproduce from workspace root into a NEW directory:

```powershell
& 'C:\Users\Ayong\.local\bin\python3.14.exe' -B 'prealpha\quest_restoration_qr3\agents\agent_b\verify.py' --output 'prealpha\quest_restoration_qr3\agents\agent_b\verification_next'
```

The command checks both vehicle quests together and refuses an existing output directory. No game/write/build/deploy action is performed.
