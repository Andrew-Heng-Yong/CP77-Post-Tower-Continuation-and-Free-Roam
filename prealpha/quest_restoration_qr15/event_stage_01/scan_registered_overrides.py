"""Narrow read-only scan of current registered REDS for these event methods.

Reuses the source-registration census; does not compile, copy or edit scripts.
This cannot certify dynamically injected behavior or the executing script cache.
"""
from pathlib import Path
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
GAME = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def main():
    output = HERE / "registered_override_scan_01.json"
    assert not output.exists(), "Fresh output required"
    source_result = WORK / "prealpha/quest_restoration_qr14/verification/compile_01/result.json"
    evidence = json.loads(source_result.read_text(encoding="utf-8-sig"))
    registered = {Path(path) for path in evidence["runtime_registered_sources"]}
    actual = set((GAME / "r6/scripts").rglob("*.reds")) | set((GAME / "red4ext/plugins").rglob("*.reds"))
    assert actual == registered, "Registered source census changed; do not silently omit new files"
    pattern = re.compile(r"VehicleComponentPS|vehicleControllerPS|OnVehicleQuestVisualDestructionEvent|OnToggleDoorWrapperEvent|DisableAllVehInteractions|OnVehicleDoorInteractionStateChange|SetHasStateBeenModifiedByQuest|SetDestructionGridPointValues|SetDoorInteractionState")
    pins = []
    matches = []
    for path in sorted(actual):
        assert path.is_relative_to(GAME)
        assert not any(parent.is_symlink() or parent.is_junction() for parent in (path, *path.parents))
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest().upper()
        text = data.decode("utf-8-sig")
        pins.append({"path": str(path), "sha256": digest})
        for index, line in enumerate(text.splitlines(), 1):
            if pattern.search(line):
                matches.append({"path": str(path), "line": index, "text": line})
    result = {"status": "CURRENT_REGISTERED_SOURCE_LITERAL_SCAN", "source_count": len(pins), "matches": matches,
              "pins": pins, "registration_evidence": {"path": str(source_result), "sha256": sha(source_result)},
              "limits": "Exact current source inventory/literal matches only. No executing-cache, CET/dynamic-hook or arbitrary semantic-override proof. No compilation or baseline rebuild.",
              "game_calls": 0, "runtime_changes": 0, "save_reads": 0}
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "sources": len(pins), "matches": len(matches)}))


if __name__ == "__main__":
    main()
