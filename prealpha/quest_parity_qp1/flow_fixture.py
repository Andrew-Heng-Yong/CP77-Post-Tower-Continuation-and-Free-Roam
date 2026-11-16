"""Exercise the repaired return after the truck-open signal."""

import sys

from stage import OUT, PRE, read, sha, write

sys.path.insert(0, str(PRE / "johnny_batch2_jb1"))
from flow_fixtures import Signals, normal


def main():
    path = OUT / "truck/scene.json"
    before = normal(read(OUT / "inputs.json")["truck"]["before"]["json"])
    after = normal(path)
    cases = []
    for model, garage_open, label in (
        (before, True, "JB3 regression"),
        (after, False, "Garage exit pending"),
        (after, True, "Garage exit acknowledged"),
    ):
        acks = (210,) if garage_open else ()
        flow = Signals(model, acknowledgements=acks, conditions={"624": True}).start("672").run()
        assert not flow.ends
        assert list(flow.journal.values()) == ["Active"]
        reached = {n for _, n, _, _ in flow.trace}
        assert {"184", "618"} <= reached
        if label == "Garage exit acknowledged":
            assert flow.and_inputs["241"] == {0, 1, 2}
            assert {"198", "925", "977", "1796", "2093", "2194"} <= reached
        else:
            assert "1786" not in reached and not flow.and_inputs["241"]
        if label == "Garage exit pending":
            assert flow.held == [[4378, "210", "NATIVE_CONDITION_ACK_REQUIRED"]]
        cases.append({"case": label, "and_241": sorted(flow.and_inputs["241"]), "end": flow.ends})

    for old_comment in (0, 1):
        flow = Signals(after, acknowledgements=(210, 1210, 925, 246, 685, 1218, 1219, 1221),
                       conditions={"624": True, "1325": False},
                       facts={"mq017_johnny_say_havefun": old_comment}).start("672").run()
        assert not flow.ends and any(n == "258" for _, n, _ in flow.held)
        flow.emit(flow.trace[-1][0] + 100, "258")
        flow.run()
        assert len(flow.ends) == 1 and flow.ends[0][1:] == ["2", "NonTerminating"]
        assert flow.and_inputs["241"] == {0, 1, 2} and flow.and_inputs["1891"] == {0, 1}
        assert all(n not in ("507", "995", "1024") for _, n, _, _ in flow.trace)
        cases.append({"case": f"Combat completion with old Johnny receipt {old_comment}", "end": flow.ends})
    write(OUT / "truck/fixtures.json", {
        "status": "PASS_BOUNDED_TRUCK_SIGNALS", "cooked_scene_json_sha256": sha(path),
        "scope": "Model starts at native truck-open handoff and supplies scenario-specific native acknowledgements.",
        "cases": cases,
    })
    print(f"Passed {len(cases)} return-path fixtures.")


if __name__ == "__main__":
    main()
