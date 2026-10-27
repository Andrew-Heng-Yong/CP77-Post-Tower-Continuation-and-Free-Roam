"""Exercise one-file successor install and rollback within workspace fixtures."""
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

H=Path(__file__).resolve().parent
P=H/"probe_05"
O=H/"probe_04"
ROOT=P/"deploy_fixtures_01"
assert not ROOT.exists()
ROOT.mkdir(parents=True)
installer=H/"deploy_probe_05.ps1"
manifest=json.loads((P/"manifest_01.json").read_text())
script=next(row for row in manifest["files"] if row["path"].endswith("WW1Probe.reds"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def fixture(name):
    root=ROOT/name
    for row in manifest["files"]:
        dest=root/"game"/row["path"]
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(O/"package"/row["path"],dest)
        assert sha(dest)==row["before"]
    return root


def run(root,action,fail=""):
    cmd=["pwsh","-NoProfile","-File",str(installer),"-Action",action,"-FixtureRoot",str(root)]
    if fail: cmd += ["-TestFailPoint",fail]
    return subprocess.run(cmd,text=True,capture_output=True,timeout=60)


rows=[]
for fail in ("AfterBackup","AfterStage","AfterReplace","BeforeReceipt"):
    root=fixture(fail)
    assert run(root,"Validate").returncode==0
    result=run(root,"Install",fail)
    assert result.returncode!=0, (fail,result.stdout,result.stderr)
    assert sha(root/"game"/script["path"])==script["before"]
    assert not (root/"game"/(script["path"]+".ptfr-ww1-stage")).exists()
    receipt=json.loads((root/"backup/failed_receipt.json").read_text())
    assert receipt["status"]=="FAILED_ROLLED_BACK" and receipt["old_script_restored"]
    rows.append({"point":fail,"status":"ROLLBACK_PASS"})
root=fixture("success")
for action in ("Validate","Install","Verify","ValidateRollback","Rollback"):
    result=run(root,action)
    assert result.returncode==0, (action,result.stdout,result.stderr)
assert sha(root/"game"/script["path"])==script["before"]
assert json.loads((root/"backup/rollback_receipt.json").read_text())["status"]=="ROLLED_BACK"
assert all(sha(root/"game"/row["path"])==row["before"] for row in manifest["files"])
proof={"status":"PASS","interruptions":rows,"interruption_points":4,
       "install_verify_rollback":True,"installed_game_writes":0,
       "installer_sha256":sha(installer)}
target=P/"deployment_tests_01.json"
assert not target.exists()
target.write_text(json.dumps(proof,indent=2)+"\n",encoding="utf-8")
print(json.dumps(proof,indent=2))
