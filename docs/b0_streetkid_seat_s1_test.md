# Streetkid barstool S1: one-use opt-in test

Superseded by the combined S2 action probe. **Do not arm S1 now.** Static audit
found the borrowed chair/bench clips unsuitable for the q000 stool; S2 enters
the stool workspot directly and adds the original V-only fix-nose/stand route.
Use `docs/b0_streetkid_seat_mirror_s2_test.md`. S1 remains installed idle as rollback.

Status: installed idle after offline scene/graph/Lua checks. This tests the
barstool only. No mirror action or story/Pepe/Pedro quest is enabled. The scene
uses V's original q000 stool workspot at the always-loaded bar marker, grafted
onto a small fact-free vanilla Sit/Get Up scene. Its visible animation and
native marker delivery remain unverified until this disposable test.

Use a disposable **post-Tower** save. Do not save this run. Approach the stool
beside the Streetkid-start mirror at approximately
`(-1261.89, -1001.64, 12.03)`. The earlier stood-at observation was
`(-1262.53, -1001.77, 12.04)` with scene/workspot both false. V must be idle.

1. In CET: `GetMod("PTFR_Streetkid_Seat_S1").Inspect()`.
2. If it says READY, run `GetMod("PTFR_Streetkid_Seat_S1").Start()` once.
3. Close CET. Look at the stool and use Sit. While seated, confirm V is not
   stuck, then use Get Up. Do not expect a mirror choice in S1.
4. After V is standing and can move, run
   `GetMod("PTFR_Streetkid_Seat_S1").Observe("after-getup")` and then
   `GetMod("PTFR_Streetkid_Seat_S1").Stop()`.
5. Quit without saving. Report whether Sit and Get Up appeared and worked,
   whether V was free afterward, and the Observe/Stop outputs.

Success is physical Sit/Get Up plus native `SceneRequests=1`,
`SceneReturns=1`, `Completed=1`, `Interrupted=0`, `Active=0`, and
`scene=false`, `workspot=false` after standing. Prompt visibility alone does
not pass. If no Sit prompt appears or V becomes stuck, do not teleport or
force facts while in the scene; quit without saving and report the last
Observe output if it is safe to open CET. Logs are flushed to
`streetkid_seat_s1_*.jsonl` in the CET mod folder.

See `research/b0_streetkid_seat_s1/build_manifest.json` and
`install_receipt.json`. All three installed files are additive; the receipt
verified 306 existing Tower Continued files remained unchanged. The public
El Coyote washroom mirror remains installed independently.
