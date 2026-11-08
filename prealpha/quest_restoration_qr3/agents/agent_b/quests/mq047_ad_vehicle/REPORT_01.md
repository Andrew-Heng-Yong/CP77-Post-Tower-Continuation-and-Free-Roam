# Dressed to Kill — QR3 deep-contract findings

All ten contracts were investigated. **No source-confirmed defect or gameplay repair; not fully STATIC_VERIFIED.**

Native resource: `base\open_world\minor_activities\badlands\inland_avenue_se1\ma_bls_ina_se1_44\ma_bls_ina_se1_44_phase.questphase` SHA256 `2FD3545F79449E3CA3BFCF887B485024C9681B37E68B53DEC70D94BA46FA352B`. Private boot: `towercontinued\sidejobs_s23\ep1\mq047_boot.questphase` SHA256 `8FB8FDE3897CABDBDA0E6C3D5E3D3A3F5F8E6DA3E923EB7A64EE9505EE54E8AB`.

{"APPROVED_DEVIATION": 2, "PASS": 3, "CONDITIONAL": 4, "OPAQUE": 1}

The exact nodes, predicates, sockets, progression, journal transitions, item/vehicle grants, cleanup and remaining limits are in [contracts.json](contracts.json). Detailed original/current models and all edges are in [graph evidence](../../verification_01/graph_evidence.json); [source pins](../../verification_01/source_pins.json) bind raw binary, JSON, normalized input and provider identities. The two-quest verifier passed210 checks including8 actual-resource mutation controls; counts describe assertions, not gameplay coverage.

The private wrapper keeps original district173 seven-tick delay and145.In1; it adds the already-existing S23 genuine-Tower/fresh-history/vehicle-not-owned/once-only wrapper and two-tick postclaim recheck. It does not alter the native activity body or reset history. Native local Onscreen email interaction is not phone SMS. Native supporting Johnny voiceset is retained under JV1 visual suppression, with rendering/camera scheduling live-only.

Remaining static inputs: exact vehicle/keycard TweakDB targets, streamed prefab/trigger/variant bindings, and full original world-owner retirement path. Saved owner transitions and actual entitlement/VO/unload effects require live evidence. No source change is justified by these gaps.

Reproduce from workspace root into a NEW directory:

```powershell
& 'C:\Users\Ayong\.local\bin\python3.14.exe' -B 'prealpha\quest_restoration_qr3\agents\agent_b\verify.py' --output 'prealpha\quest_restoration_qr3\agents\agent_b\verification_next'
```

The command checks both vehicle quests together and refuses an existing output directory. No game/write/build/deploy action is performed.
