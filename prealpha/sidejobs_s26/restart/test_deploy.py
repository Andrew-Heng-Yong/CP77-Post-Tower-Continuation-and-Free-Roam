"""Workspace-only tests of the real capture installer, including recovery."""
import datetime
import json
import shutil
import subprocess
import sys
from pathlib import Path
import hashlib
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
def read(path): return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def psquote(value):
    return "'" + str(value).replace("'", "''") + "'"


def main(revision):
    source = HERE / "build" / revision
    suite = HERE / "fixtures" / datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    suite.mkdir(parents=True, exist_ok=False)
    cases = []
    rel = Path("bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_SideJobsCaptureS26")

    def fixture(name):
        path = suite / name
        game, saves, build, recovery = [path / x for x in ["game", "saves", "build", "recovery"]]
        (game / rel.parent).mkdir(parents=True)
        saves.mkdir()
        shutil.copytree(source, build)
        for relative, text in [("r6/scripts/protected.reds", "untouched"), ("r6/cache/final.redscripts", "cache"), ("archive/pc/mod/protected.archive", "archive")]:
            p = game / relative; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text)
        (saves / "sav.dat").write_bytes(b"unchanged save fixture")
        return {"root": path, "game": game, "saves": saves, "build": build, "recovery": recovery}

    def invoke(f, mode="Validate", expected=True, busy=False, extra=None, **changes):
        args = {"Mode": mode, "Build": f["build"], "RecoveryRoot": f["recovery"], "GameRoot": f["game"], "SaveRoot": f["saves"]} | changes
        process = "[pscustomobject]@{Id=123;ProcessName='Cyberpunk2077'}" if busy else "return"
        command = "function Get-Process { param([string]$Name) " + process + " }; & " + psquote(HERE / "deploy.ps1")
        command += " -Fixture " + " ".join("-" + k + " " + psquote(v) for k, v in args.items())
        if extra: command += " " + extra
        result = subprocess.run(["pwsh", "-NoProfile", "-Command", command], capture_output=True, text=True, timeout=90)
        (f["root"] / (mode + "_" + str(len(list(f["root"].glob("*.log")))) + ".log")).write_text(result.stdout + result.stderr, encoding="utf-8")
        assert (result.returncode == 0) == expected, (f["root"].name, mode, result.stdout, result.stderr)
        assert (f["saves"] / "sav.dat").read_bytes() == b"unchanged save fixture"
        assert (f["game"] / "r6/scripts/protected.reds").read_text() == "untouched"
        assert (f["game"] / "r6/cache/final.redscripts").read_text() == "cache"
        return result

    def tamper(f, change):
        p = f["build"] / "build.json"; m = read(p); change(m); p.write_text(json.dumps(m))

    f = fixture("normal")
    invoke(f); assert not (f["game"] / rel).exists()
    invoke(f, "Install")
    for name in ["init.lua", "data.json"]: assert sha(f["game"] / rel / name) == sha(source / name)
    invoke(f, "ValidateRollback"); invoke(f, "Rollback")
    assert not (f["game"] / rel / "init.lua").exists()
    invoke(f, "Rollback", expected=False); cases.append("install_validate_recover_no_repeat")
    for name, mutate in [
        ("wrong_status", lambda m: m.update(status="RESTORE_ALL")),
        ("wrong_roster", lambda m: m.update(jobs=57)),
        ("wrong_detail", lambda m: m.update(journals=1)),
        ("writes", lambda m: m.update(native_writes=1)),
        ("save_writes", lambda m: m.update(save_writes=1)),
        ("polling", lambda m: m.update(automatic_callbacks=1)),
        ("extra_file", lambda m: m["files"].update({"other.lua": "0" * 64})),
        ("source_escape", lambda m: m["files"].update({"../init.lua": m["files"].pop("init.lua")})),
    ]:
        f = fixture(name); tamper(f, mutate); invoke(f, expected=False); cases.append(name)
    f = fixture("file_drift"); (f["build"] / "init.lua").write_text("different"); invoke(f, expected=False); cases.append("file_drift")
    f = fixture("proof_drift"); (f["build"] / "tests.json").write_text(json.dumps({"status":"FAIL"})); invoke(f, expected=False); cases.append("proof_drift")
    f = fixture("existing_target"); (f["game"] / rel).mkdir(); invoke(f, expected=False); cases.append("existing_target")
    f = fixture("busy"); invoke(f, expected=False, busy=True); cases.append("busy")
    f = fixture("relative_build"); invoke(f, expected=False, Build="build"); cases.append("relative_build")
    f = fixture("wrong_root"); invoke(f, expected=False, GameRoot=ROOT); cases.append("wrong_root")
    f = fixture("partial"); invoke(f, "Install", expected=False, extra="-FailAfterFirst"); invoke(f, "ValidateRollback"); invoke(f, "Rollback"); cases.append("partial_recovery")
    f = fixture("target_drift"); invoke(f, "Install"); (f["game"] / rel / "init.lua").write_text("user change"); invoke(f, "Rollback", expected=False); assert (f["game"] / rel / "init.lua").read_text() == "user change"; cases.append("target_drift")
    f = fixture("transaction_drift"); invoke(f, "Install"); (f["recovery"] / "transaction.json").write_text("{}"); invoke(f, "Rollback", expected=False); cases.append("transaction_drift")
    f = fixture("reports_preserved"); invoke(f, "Install"); report = f["game"] / rel / "capture_test.json"; report.write_text("user capture"); invoke(f, "Rollback"); assert report.read_text() == "user capture"; cases.append("reports_preserved")
    f = fixture("junction"); junction = f["root"] / "linked_game"
    result = subprocess.run(["pwsh", "-NoProfile", "-Command", "New-Item -ItemType Junction -Path " + psquote(junction) + " -Target " + psquote(f["game"]) + " | Out-Null"], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    invoke(f, expected=False, GameRoot=junction); cases.append("junction_refused")
    report = {"status": "PASS_WORKSPACE_FIXTURES_NOT_LIVE", "cases": len(cases), "case_names": cases,
              "build_sha256": sha(source / "build.json"), "installer_sha256": sha(HERE / "deploy.ps1"), "tester_sha256": sha(Path(__file__)), "game_writes": 0, "save_writes": 0}
    (suite / "results.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    main(sys.argv[1])
