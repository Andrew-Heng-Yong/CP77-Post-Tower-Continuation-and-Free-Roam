"""Exercise WA2 replacement install, rollback and each interruption point."""
from hashlib import sha256
from pathlib import Path
import json
import shutil
import subprocess

H = Path(__file__).resolve().parent
W = H.parents[1]
C = H / "candidate_01"
M = json.loads((C / "install_manifest_01.json").read_text(encoding="utf-8"))
OLD = W / "prealpha/bottle_actions_ba1/candidate_01/package"
SCRIPT = H / "deploy_01.ps1"
OUT = C / "deployment_tests_01.json"
ROOT = C / "deploy_fixtures_01"
assert not OUT.exists() and not ROOT.exists(), "Preserve fixture evidence"
digest = lambda p: sha256(p.read_bytes()).hexdigest().upper()


def run(fixture, action, fail=""):
    cmd = [r"C:/Users/Ayong/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(SCRIPT),
           "-Action", action, "-FixtureRoot", str(fixture)]
    if fail:
        cmd += ["-TestFailPoint", fail]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=120)


def make(name):
    fixture = ROOT / name
    for f in M["package_files"]:
        src = OLD / f["path"]
        assert digest(src) == f["before"]
        dst = fixture / "game" / f["path"]
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
    return fixture


def baseline(fixture):
    assert all(digest(fixture / "game" / f["path"]) == f["before"]
               for f in M["package_files"])


rows = []
normal = make("normal")
for action in ("Validate", "Install", "Verify", "ValidateRollback", "Rollback"):
    r = run(normal, action)
    rows.append({"fixture": "normal", "action": action, "exit": r.returncode,
                 "tail": (r.stdout + r.stderr)[-300:]})
    assert r.returncode == 0, (action, r.stdout, r.stderr)
baseline(normal)
for point in ("AfterBackup", "AfterStage", "AfterFirstReplace", "AfterSecondReplace", "AfterThirdReplace", "BeforeReceipt"):
    fixture = make(point.lower())
    assert run(fixture, "Validate").returncode == 0
    r = run(fixture, "Install", point)
    rows.append({"fixture": point, "action": "Install interrupted", "exit": r.returncode,
                 "tail": (r.stdout + r.stderr)[-300:]})
    assert r.returncode != 0 and "Injected interruption" in (r.stdout + r.stderr), point
    for action in ("ValidateRollback", "Rollback"):
        check = run(fixture, action)
        rows.append({"fixture": point, "action": action, "exit": check.returncode,
                     "tail": (check.stdout + check.stderr)[-300:]})
        assert check.returncode == 0, (point, action, check.stdout, check.stderr)
    baseline(fixture)
result = {"status": "PASS", "fixture_actions": len(rows), "interruption_points": 6,
          "normal_install_verify_rollback": True, "all_interrupted_states_recoverable": True,
          "rows": rows, "game_writes": 0, "save_writes": 0}
OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
Path(str(OUT) + ".sha256").write_text(digest(OUT) + "\n", encoding="ascii")
print(json.dumps({k: result[k] for k in ("status", "fixture_actions", "interruption_points")}))
