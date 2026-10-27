"""Unreleased full 51-path local package with exact member readback."""
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import json

H=Path(__file__).resolve().parent
P=H/"candidate_02"
manifest=json.loads((P/"install_manifest_01.json").read_text(encoding="utf-8"))
assert manifest["status"]=="W2_51_PATH_SUCCESSOR_STAGED_NOT_INSTALLED"
dest=P/"dist/Post-Tower-Continuation-and-Free-Roam-W2-unreleased.zip"
assert not dest.exists(),"Preserve previous ZIP"
dest.parent.mkdir(parents=True,exist_ok=True)
with ZipFile(dest,"w",compression=ZIP_DEFLATED,compresslevel=6) as z:
    for f in manifest["package_files"]:
        z.write(P/"package"/f["path"],f["path"])
with ZipFile(dest,"r") as z:
    assert sorted(z.namelist())==sorted(f["path"] for f in manifest["package_files"])
    for f in manifest["package_files"]:
        assert sha256(z.read(f["path"])).hexdigest().upper()==f["after"],f["path"]
record={"status":"UNRELEASED_FULL_51_PATH_ZIP_VERIFIED","path":str(dest),
        "sha256":sha256(dest.read_bytes()).hexdigest().upper(),"members":51,
        "public_release":False,"game_writes":0}
(P/"zip_proof_01.json").write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8")
print(json.dumps(record,indent=2))
