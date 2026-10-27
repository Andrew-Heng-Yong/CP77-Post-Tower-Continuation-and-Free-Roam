"""Build a complete, unreleased 51-path package from the installed RC2 candidate."""
import hashlib
import json
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parent / "candidate_03"
manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
files = manifest["files"]
assert len(files) == 51
dest = root / "dist" / "Post-Tower-Continuation-and-Free-Roam-RC2-unreleased.zip"
assert not dest.exists()
dest.parent.mkdir()
with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for item in files:
        path = root / "package" / item["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest().upper() == item["sha256"]
        z.write(path, item["path"].replace("\\", "/"))
with zipfile.ZipFile(dest) as z:
    assert len(z.namelist()) == 51
    for item in files:
        assert hashlib.sha256(z.read(item["path"].replace("\\", "/"))).hexdigest().upper() == item["sha256"]
digest = hashlib.sha256(dest.read_bytes()).hexdigest().upper()
(dest.with_suffix(dest.suffix + ".sha256")).write_text(digest + "\n", encoding="utf-8")
print(json.dumps({"entries": 51, "sha256": digest, "bytes": dest.stat().st_size}))
