"""Package the scoped WW1 probe successor; only the REDscript file changes."""
import hashlib
import json
import zipfile
from pathlib import Path

H=Path(__file__).resolve().parent
W=H.parent.parent
OLD=H/"probe_04"
NEW=H/"probe_05"
GAME=Path(r"C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


old=json.loads((OLD/"manifest_01.json").read_text())
compiled=json.loads((NEW/"compile_02/result.json").read_text())
assert compiled["status"]=="PASS" and compiled["source_count"]==65
assert len(old["files"])==3
rows=[]
for row in old["files"]:
    rel=row["path"]
    candidate=NEW/"package"/rel
    assert candidate.is_file()
    current=GAME/rel
    assert sha(current)==row["sha256"], rel
    digest=sha(candidate)
    if rel.endswith("WW1Probe.reds"):
        assert digest==compiled["candidate_script_sha256"] and digest!=row["sha256"]
    else:
        assert digest==row["sha256"], rel
    rows.append({"path":rel,"before":row["sha256"],"after":digest})
assert sum(r["before"]!=r["after"] for r in rows)==1
zip_path=NEW/"Post-Tower-Continuation-and-Free-Roam-WW1-Scav-probe05-unreleased.zip"
assert not zip_path.exists()
with zipfile.ZipFile(zip_path,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for row in sorted(rows,key=lambda r:r["path"]):
        info=zipfile.ZipInfo(row["path"],(2026,10,26,18,30,0))
        info.compress_type=zipfile.ZIP_DEFLATED
        info.external_attr=0o644<<16
        z.writestr(info,(NEW/"package"/row["path"]).read_bytes(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
with zipfile.ZipFile(zip_path) as z:
    assert z.testzip() is None and set(z.namelist())=={r["path"] for r in rows}
    for row in rows:
        assert hashlib.sha256(z.read(row["path"])).hexdigest().upper()==row["after"]
result={"status":"WW1_PROBE05_ONE_SCRIPT_SUCCESSOR_STAGED_NOT_INSTALLED",
        "old_probe":"probe_04","game_paths":3,"changed_paths":1,
        "files":rows,"zip_sha256":sha(zip_path),
        "compiled_sha256":compiled["compiled_sha256"],
        "cause_candidate":"The last runtime log shows scene=true/dialogue=false at the Scavs; probe04 rejected scene membership.",
        "fix":"Gate on live dialogue instead; log owner-ready, safe, actor and receipt stages.",
        "archive_and_xl_byte_identical":True,"live_result":"UNKNOWN"}
manifest=NEW/"manifest_01.json"
assert not manifest.exists()
manifest.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
(NEW/"manifest_01.json.sha256").write_text(sha(manifest)+"\n",encoding="ascii")
print(json.dumps({"status":result["status"],"zip_sha256":result["zip_sha256"],
                  "changed_paths":1,"game_paths":3},indent=2))
