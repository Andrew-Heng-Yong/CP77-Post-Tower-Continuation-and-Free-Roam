"""Project exact Minefield keys from a fully traversed saved community component."""
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PREALPHA = HERE.parent
sys.path.insert(0, str(PREALPHA / "resume_dispatcher_rd5_gigs_20261113_01"))
from capture import read, sha, write

sys.path.insert(0, str(PREALPHA / "quest_restoration_qr15/lifecycle_01/save_community"))
from decode import Reader
from decode_full import decode_full


def inspect(data, outer_keys, targets):
    decoded = decode_full(data, outer_keys)
    assert decoded["consumed_bytes"] == len(data) and decoded["unparsed_bytes"] == 0
    reader = Reader(data)
    named = {}
    for outer in outer_keys:
        for inner in reader.ids():
            record = reader.record()
            name = reader.name()
            if outer in targets.values() or inner in targets.values():
                key = f"{outer}/{inner}"
                assert key not in named
                named[key] = {"outer": str(outer), "inner": str(inner), "phase": name, "row": record}
    assert reader.pos == decoded["second_map_start"]
    return {name: {
        "world_key": str(key),
        "in_outer_list": key in outer_keys,
        "entry_rows": [row for row in named.values() if str(key) in (row["outer"], row["inner"])],
        "spawner_row": decoded["second_rows"].get(key),
    } for name, key in targets.items()}


def main():
    shared = sys.argv[1:] == ["--include-shared-patrols"]
    if sys.argv[1:] and not shared:
        raise SystemExit("Expected --include-shared-patrols or no arguments")
    captured = HERE / ("capture_02/manifest.json" if shared else "capture_01/manifest.json")
    manifest = read(captured)
    targets = {name: int(key) for name, key in manifest["targets"].items()}
    assert len(targets) == len(set(targets.values())) == (6 if shared else 3)
    results = []
    for item in manifest["saves"]:
        source = Path(item["trailing_path"])
        assert sha(source) == item["trailing_sha256"]
        keys = list(map(int, item["outer_keys"]))
        assert len(keys) == len(set(keys))
        data = source.read_bytes()
        assert item["node_size"] == 8 + 8 * len(keys) + len(data)
        results.append({"slot": item["slot"], "source_sha256": item["source_sha256"],
                        "component_sha256": item["trailing_sha256"], "target_rows": inspect(data, keys, targets)})
    out = HERE / "evidence_01"
    out.mkdir(exist_ok=True)
    evidence = out / ("communities_with_patrols.json" if shared else "communities.json")
    if evidence.exists():
        raise FileExistsError(evidence)
    write(evidence, {"capture_sha256": sha(captured), "refs": manifest["node_refs"],
                     "saves": results, "save_writes": 0})
    for row in results:
        print(row["slot"], {name: (value["in_outer_list"], len(value["entry_rows"]),
              value["spawner_row"] is not None) for name, value in row["target_rows"].items()})


if __name__ == "__main__":
    main()
