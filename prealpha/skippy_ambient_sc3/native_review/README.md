# SC3 native Skippy lifecycle review

The current `Stopped=1` / `Stop=0` telemetry matches a concrete SC1 wrapper defect. The native ambient child uses `TurnOff` for ordinary weapon unequip, while the SC1 wrapper permanently terminates on that output. SC2 only changed admission and could not repair a saved terminal receipt.

## Native evidence

Freshly decoded `base/quest/minor_quests/mq007/mq007.questphase` has parent edges `3.TurnOff -> 12.In` and `12.Out -> 3.In1`. Parent node 12 is the exact player-equipped `Items.mq007_skippy` condition (inverted false).

Within ambient node 3, node 34 waits for that weapon to be unequipped. After native two-second wait 38, condition 39 tests `mq007_interrupt_skippy_dialogue == 0`. Its true path runs entity-manager node 36 to detach `#mq007_01_skippy_prop`, then output 35 `TurnOff`. Output 35 is **Terminating**. The original parent subsequently waits for re-equip and starts the ambient child again.

The serialized SC1 wrapper instead connects `10.TurnOff -> 13.In`, writes `PTFRSKIP_Ambient_Stopped=1`, then reaches root output 14, also **Terminating**. Consequently, its parallel stop waiter 11 is no longer available after natural unequip. Clearing `Stopped` to obtain a fresh acknowledgement would lose the existing retirement proof and can deadlock migration. Preserve old claim, entry and stopped facts.

`graph_trace_01.json` records the native and existing cooked edges and hashes. Native source SHA-256 is `05546F9C5C90E2360A646F85E2FCC15C7098D2659A929C076B6A7339B1080E9E`; SC1 resource SHA-256 is `64892E9551A02C98812B90FE3633BC8D90D2C410C0DB9D2EF2FCC61A6737A021`.

## Selected SC3 resource

Use **candidate_02**, built by `build_owner_02.ps1`:

`source/towercontinued/skippy_ambient_sc3/skippy_ambient_owner.questphase`

SHA-256: `E9A06A80006EEA94ECF74D074B74942268DB42D5E4E50A3093BF5C71FA156B19`.

The new root claims `PTFRSKIP_SC3_` Ready/Request/Claimed/Entered/Stop/Stopped receipts. A nested lifecycle owns native equip wait 12, native ambient 3, and two owned Active writers. The loop is `equip -> Active1 -> ambient -> TurnOff -> Active0 -> equip`. Active describes graph dispatch, not visible hologram proof. Root Stop cuts the entire nested lifecycle, including an outstanding equip waiter, then clears Active, writes Stopped and terminates. Natural unequip has no path to permanent Stopped.

The root preserves Tower and S23 one-time owner exclusions. Old owner retirement must be either its existing Stopped receipt, or the conjunction of old Claimed=0, Entered=0, Request=0 and Stop=1. Parent script coordination must cancel an unclaimed old request and set old Stop, then wait for this condition on settled observations before requesting SC3. An old claimed but unstopped owner must acknowledge the stop; never clear old/native state to force migration. Exact native equipped-item admission replaces the additional inventory-quantity check; its condition directly checks the weapon required by the loop.

`verify_owner_02.ps1` reads the native and new binaries independently. All six native graphs, 68 nodes and 73 edges match. `verify_payload_03.py` passes 74 assertions: all native ambient payloads except the existing absolute prefab-scope substitution, exact native equip condition, complete prewrite/readback root payload, 32 old-retirement truth-table combinations, changed guard rejection, stop boundaries and negative controls against SC1's terminal wiring. Inner native gameplay counters/expression behavior are retained byte-semantically; this wrapper introduces only owned receipt writers.

## Rejected workspace output and limits

Candidate 01 is **rejected**. WolvenKit `DeepCopy()` duplicated socket identities within the ambient graph, so the graph traversal found missing resolvable connections. Candidate 02 retains the directly read native ambient object, as the proven SC1 builder did. No candidate 01 resource may be packaged or installed. The original candidate and failed verifier remain for diagnosis.

The first payload verifier compared the whole export DTO, including differing export metadata; successor 03 compares complete resource roots instead. Candidate 02's serialized resource did not change during that correction.

This agent made no game/save/fact writes or game launch. Packaging, compilation, current resource winners, installation, rollback and live acceptance are parent tasks. Static correction of the rearm defect does not certify actual combat audio or hologram rendering.
