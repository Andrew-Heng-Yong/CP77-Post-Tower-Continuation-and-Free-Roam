"""Exercise install, rollback and every interruption point in workspace fixtures."""
from hashlib import sha256
from pathlib import Path
import json
import shutil
import subprocess

H=Path(__file__).resolve().parent
W=H.parents[1]
candidate=H/"candidate_02"
manifest=json.loads((candidate/"install_manifest_01.json").read_text(encoding="utf-8"))
old=W/"prealpha/coaster_jean_jc1/candidate_01/package"
probe=W/"prealpha/world_workspots_ww1/probe_05/package"
script=H/"deploy_01.ps1"
out=candidate/"deployment_tests_02.json"
assert not out.exists(),"Preserve fixture evidence"
root=candidate/"deploy_fixtures_02"
assert not root.exists(),"Preserve fixture directory"
digest=lambda p:sha256(p.read_bytes()).hexdigest().upper()

def run(fixture,action,fail=""):
    cmd=["pwsh","-NoProfile","-ExecutionPolicy","Bypass","-File",str(script),
         "-Action",action,"-FixtureRoot",str(fixture)]
    if fail: cmd += ["-TestFailPoint",fail]
    return subprocess.run(cmd,capture_output=True,text=True,timeout=120)

def make(name):
    fixture=root/name
    for f in manifest["package_files"]:
        src=old/f["path"]
        assert digest(src)==f["before"]
        dst=fixture/"game"/f["path"]
        dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(src,dst)
    for f in manifest["retired"]:
        src=probe/f["path"]
        assert digest(src)==f["before"]
        dst=fixture/"game"/f["path"]
        dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(src,dst)
    return fixture

def baseline(fixture):
    assert all(digest(fixture/"game"/f["path"])==f["before"] for f in manifest["package_files"])
    assert all(digest(fixture/"game"/f["path"])==f["before"] for f in manifest["retired"])

rows=[]
normal=make("normal")
for action in ("Validate","Install","Verify","ValidateRollback","Rollback"):
    r=run(normal,action)
    rows.append({"fixture":"normal","action":action,"exit":r.returncode,"tail":(r.stdout+r.stderr)[-280:]})
    assert r.returncode==0,(action,r.stdout,r.stderr)
baseline(normal)
for point in ("AfterBackup","AfterStage","AfterFirstReplace","AfterThirdReplace","AfterFirstRetire","BeforeReceipt"):
    fixture=make(point.lower())
    assert run(fixture,"Validate").returncode==0
    r=run(fixture,"Install",point)
    rows.append({"fixture":point,"action":"Install interrupted","exit":r.returncode,"tail":(r.stdout+r.stderr)[-280:]})
    assert r.returncode!=0 and "Injected interruption" in (r.stdout+r.stderr),point
    for action in ("ValidateRollback","Rollback"):
        check=run(fixture,action)
        rows.append({"fixture":point,"action":action,"exit":check.returncode,"tail":(check.stdout+check.stderr)[-280:]})
        assert check.returncode==0,(point,action,check.stdout,check.stderr)
    baseline(fixture)
result={"status":"PASS","fixture_actions":len(rows),"interruption_points":6,
        "normal_install_verify_rollback":True,"all_interrupted_states_recoverable":True,
        "rows":rows,"game_writes":0,"save_writes":0}
out.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
print(json.dumps({k:result[k] for k in ("status","fixture_actions","interruption_points")},indent=2))
