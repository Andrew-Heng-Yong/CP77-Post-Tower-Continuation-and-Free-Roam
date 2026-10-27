"""Read-only save-file checksum snapshots around the additive install."""
import hashlib
import json
import sys
from pathlib import Path

H = Path(__file__).resolve().parent
P = H / "probe_05"
ROOT = Path(r"C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077")
mode = sys.argv[1] if len(sys.argv) == 2 else ""
assert mode in ("before", "after") and ROOT.is_dir()


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


rows = []
for path in sorted(ROOT.rglob("*")):
    if path.is_file():
        assert not path.is_symlink(), path
        rows.append({"path": path.relative_to(ROOT).as_posix(), "size": path.stat().st_size,
                     "sha256": digest(path)})
assert rows
result = {"status": "READ_ONLY_SAVE_SNAPSHOT", "root": str(ROOT), "files": rows,
          "file_count": len(rows), "total_bytes": sum(r["size"] for r in rows)}
target = P / f"save_{mode}_01.json"
assert not target.exists(), "Preserve earlier snapshot"
target.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
if mode == "after":
    previous = json.loads((P / "save_before_01.json").read_text(encoding="utf-8"))
    assert previous["root"] == result["root"]
    before = {r["path"]: (r["size"],r["sha256"]) for r in previous["files"]}
    after = {r["path"]: (r["size"],r["sha256"]) for r in rows}
    added = sorted(after.keys()-before.keys())
    removed = sorted(before.keys()-after.keys())
    changed = sorted(k for k in before.keys() & after.keys() if before[k] != after[k])
    comparison = {"status":"UNCHANGED" if not (added or removed or changed) else "CHANGED",
                  "before_count":len(before),"after_count":len(after),
                  "added":added,"removed":removed,"changed":changed}
    (P / "save_comparison_01.json").write_text(json.dumps(comparison,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(comparison))
    assert comparison["status"] == "UNCHANGED"
else:
    print(json.dumps({"status": result["status"], "file_count":len(rows),
                      "total_bytes":result["total_bytes"]}))
