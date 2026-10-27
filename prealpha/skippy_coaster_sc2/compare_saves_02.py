"""Explain save changes across SC2 deployment without modifying save files."""
from datetime import datetime
from hashlib import sha256
from pathlib import Path
import json

h = Path(__file__).resolve().parent
c = h / "candidate_01"
root = Path(r"C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077")
baseline = json.loads((c / "save_baseline_01.json").read_text(encoding="utf-8"))
receipt = h.parents[1] / "recovery/skippy_coaster_sc2_01/receipt.json"
installed_at = receipt.stat().st_mtime

def digest(path):
    hash_ = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hash_.update(block)
    return hash_.hexdigest().upper()

old = {row["path"]: row["sha256"] for row in baseline["files"]}
new = {str(path): path for path in root.rglob("*") if path.is_file()}
changed = []
for name in sorted(set(old) | set(new)):
    actual = digest(new[name]) if name in new else None
    if old.get(name) != actual:
        path = new.get(name)
        changed.append({
            "path": name,
            "before": old.get(name),
            "after": actual,
            "modified_local": datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds") if path else None,
            "modified_before_install_receipt": path.stat().st_mtime < installed_at if path else None,
        })
assert len(old) == 301 and len(new) == 301
assert len(changed) == 4
assert all(row["modified_before_install_receipt"] for row in changed)
assert all("ManualSave-23" in row["path"] or row["path"].endswith("user.gls") for row in changed)
report = {
    "status": "USER_SESSION_SAVE_CHANGES_BEFORE_SC2_INSTALL",
    "baseline_files": len(old),
    "current_files": len(new),
    "unchanged_files": len(old) - len(changed),
    "changed": changed,
    "install_receipt_local": datetime.fromtimestamp(installed_at).isoformat(timespec="seconds"),
    "save_writes": 0,
}
out = c / "save_comparison_02.json"
assert not out.exists()
out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({key: report[key] for key in ("status", "unchanged_files", "install_receipt_local")}))
