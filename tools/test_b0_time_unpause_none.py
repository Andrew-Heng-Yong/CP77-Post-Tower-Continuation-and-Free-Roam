"""Static safety checks for the one-shot post-Tower source-None unpause probe."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "research/phase2b_p0/tooling/python"))
from lupa.luajit21 import LuaRuntime  # noqa: E402

VAL = ROOT / "research/b0_time_pause/validation"
DOC = json.loads((VAL / "manual_unpause.questphase.json").read_text(encoding="utf-8"))
MANIFEST = json.loads((VAL / "build_manifest.json").read_text(encoding="utf-8"))


def walk(value: object):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def main() -> None:
    assert MANIFEST["status"] == "EXPERIMENTAL_MANUAL_DISPOSABLE_ONLY"
    assert MANIFEST["vanilla_replacements"] == []
    assert MANIFEST["resources"] == ["towercontinued\\b0_time_unpause_none\\manual_unpause.questphase"]
    archive = ROOT / "build/B0_TimeUnpauseNone" / MANIFEST["archive"]
    assert hashlib.sha256(archive.read_bytes()).hexdigest().upper() == MANIFEST["sha256"]
    xl = (ROOT / "archive/b0_time_unpause_none/TowerContinued_B0_TimeUnpauseNone.archive.xl").read_text(encoding="utf-8")
    assert xl.count("- path:") == 1 and MANIFEST["resources"][0] in xl

    graph = {
        node["Data"]["id"]: node["Data"]
        for node in DOC["Data"]["RootChunk"]["graph"]["Data"]["nodes"]
    }
    assert set(graph) == set(range(10))
    actions = [node for node in graph.values() if node["$type"] == "questTimeManagerNodeDefinition"]
    assert len(actions) == 1 and actions[0]["id"] == 6
    action = actions[0]["type"]["Data"]
    assert action["$type"] == "questPauseTime_NodeType"
    assert action["pause"] == 0 and action["source"]["$value"] == "None"
    writers = [
        node["type"]["Data"]["factName"]
        for node in graph.values()
        if node["$type"] == "questFactsDBManagerNodeDefinition"
    ]
    assert set(writers) == {
        "PTFRB0TU_Ready", "PTFRB0TU_Request", "PTFRB0TU_Rejected", "PTFRB0TU_Done"
    }
    assert graph[2]["condition"]["Data"]["type"]["Data"]["factName"] == "PTFRB0TU_Request"
    guards = {
        item["type"]["Data"]["factName"]
        for item in walk(graph[4]["condition"])
        if item.get("$type") == "questFactsDBCondition"
    }
    assert guards == set(MANIFEST["guard_facts"]), guards ^ set(MANIFEST["guard_facts"])

    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute("registerForEvent = function() end")
    addon = (ROOT / "diagnostics/PTFR_B0_TimeUnpauseNone/init.lua").read_text(encoding="utf-8")
    module = lua.execute(addon)
    assert module["Inspect"] is not None and module["Activate"] is not None and module["Observe"] is not None
    print("PASS: one mod-owned quest resource, guarded one-shot source-None unpause, Lua load")


if __name__ == "__main__":
    main()
