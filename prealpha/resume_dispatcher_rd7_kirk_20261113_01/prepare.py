"""Pin the current sources and the previously serialized Meet Kirk entrance."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BATCH = HERE.parent / "resume_dispatcher_rd6_batch50_20261113_01"
sys.path.insert(0, str(BATCH))
from review_batch import load_baseline, pinned, read, readonly, sha, write


def main(out):
    assert out.parent == HERE and out.name.startswith("evidence_") and not out.exists()
    game, members, xl = load_baseline()
    prior = read(BATCH / "jobs/evidence_02/assessment.json")
    graph = BATCH / "jobs/graph_03"
    readback = read(pinned(graph, ("readback.json", prior["readback_sha256"])))
    parts = {}
    for item in readback["resources"]:
        name = item["name"]
        raw = pinned(graph, (name + ".questphase", item["raw_sha256"]))
        export = pinned(graph, (name + ".questphase.json", item["export_sha256"]))
        parts[name] = {**item, "raw": str(raw), "export": str(export)}
    assert set(parts) == {"root", "main", "hook"}
    with readonly("registry") as db:
        fields = "rid,depot,key,role,archive,sha256,export_path,export_sha256"
        providers = [dict(db.execute(f"SELECT {fields} FROM resources WHERE rid=?", (rid,)).fetchone())
                     for rid in (15521, 14599, 15154, 10730, 8977, 7818, 14764, 15527)]
    for row in providers:
        pinned(Path(row["export_path"]).parent, (Path(row["export_path"]).name, row["export_sha256"]))
        if row["role"] == "PTFR":
            assert members[row["depot"]] == row["sha256"]
    manifest = read(BATCH / "evidence_03/manifest.json")
    installed = read(pinned(BATCH / "evidence_03", ("installed_readback.json", manifest["files"]["installed_readback.json"])))
    for part in parts.values():
        assert all(b["path"] != part["depot"] for b in installed["bindings"])
    out.mkdir()
    write(out / "provider_watch.json", {"game": str(game), "xl": xl, "resources": providers, "parts": parts,
          "archive_sha256": sha(game / "archive/pc/mod/zzzz_PTFR_Combined.archive")})


if __name__ == "__main__":
    main(HERE / "evidence_02")
