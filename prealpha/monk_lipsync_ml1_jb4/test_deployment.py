"""Exercise the exact ML1_JB4 one-archive installer against isolated fixture roots."""
from pathlib import Path
import copy
import json
import shutil
import subprocess

from prepare_deployment import ALLOWED, HERE, SOURCE_PACKAGE, TRANSACTION, checked, read, sha, write

PW = Path(r"C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe")
INSTALLER = HERE / "deploy_core.ps1"


def put(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)


def main():
    root = HERE / "fixtures/deployment_01"
    root.mkdir(parents=True)
    manifest_path = HERE / TRANSACTION
    base = read(manifest_path)
    review = read(HERE / "installer_review.json")
    checked(INSTALLER, review["installer_sha256"])
    checked(manifest_path, review["manifest_sha256"])
    original = SOURCE_PACKAGE
    actions = []

    def fixture(name, actual=False):
        location = root / name
        manifest = copy.deepcopy(base)
        game, saves, package = (location / name for name in ("game", "saves", "package"))
        manifest.update(game_root=str(game), save_root=str(saves), package_root=str(package),
                        zip="", zip_sha256=None, compile_inputs={}, proofs=[])
        for r in manifest["files"]:
            rel = r["path"]
            if actual:
                for source, dest, key in ((original, game, "before"), (Path(base["package_root"]), package, "after")):
                    p = dest / rel
                    p.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(checked(source / rel, r[key]), p)
            else:
                old = ("old " + rel).encode()
                new = ("new " + rel).encode() if rel in ALLOWED else old
                put(game / rel, old)
                put(package / rel, new)
                r.update(before=sha(game / rel), before_bytes=len(old), after=sha(package / rel), after_bytes=len(new))
        for rows, tree in ((manifest["required_files"], game), (manifest["protected_saves"] + manifest["working_save_files"], saves)):
            for r in rows:
                data = ("protected " + r["path"]).encode()
                put(tree / r["path"], data)
                r.update(bytes=len(data), sha256=sha(tree / r["path"]))
        put(saves / "OtherSave/sav.dat", b"Untouched extra save")
        put(game / "unknown_mod/keep.txt", b"Untouched external file")
        write(location / "manifest.json", manifest)
        return location, manifest

    def call(location, action, expected, *args):
        path = location / "manifest.json"
        command = [str(PW), "-NoProfile", "-File", str(INSTALLER), "-Action", action, "-FixtureRoot", str(location),
                   "-FixtureManifest", str(path), "-FixtureManifestSHA", sha(path), *args]
        p = subprocess.run(command, capture_output=True, text=True, timeout=60, creationflags=subprocess.CREATE_NO_WINDOW)
        actions.append({"fixture": location.name, "action": action, "exit": p.returncode,
                        "options": list(args), "output": p.stdout.strip(), "error": p.stderr.strip()})
        if isinstance(expected, int):
            assert p.returncode == expected, (location.name, action, p.stdout, p.stderr)
        else:
            assert p.returncode == 0 and json.loads(p.stdout)["status"] == expected, (location.name, action, p.stdout, p.stderr)

    def managed(location, manifest, side):
        for r in manifest["files"]:
            checked(location / "game" / r["path"], r[side])

    def protect(location, manifest):
        game, saves = location / "game", location / "saves"
        paths = {game / r["path"] for r in manifest["files"]}
        return {p.relative_to(location).as_posix(): sha(p)
                for p in list(game.rglob("*")) + list(saves.rglob("*")) if p.is_file() and p not in paths}

    def journal(location):
        return json.loads(read(location / "recovery/core/journal.json")["payload_json"])

    r, m = fixture("actual_Core51", actual=True)
    protected = protect(r, m)
    call(r, "Preflight", "PREFLIGHT_READY")
    assert not (r / "recovery").exists()
    call(r, "Install", "INSTALLED_VERIFIED")
    managed(r, m, "after")
    assert journal(r)["completed_paths"] == ALLOWED and protect(r, m) == protected
    for row in m["files"]:
        if row["path"] in ALLOWED:
            checked(r / "recovery/core/old" / row["path"], row["before"])
            checked(r / "recovery/core/new" / row["path"], row["after"])
    call(r, "Verify", "VERIFIED_AFTER")
    call(r, "ValidateRollback", "ROLLBACK_READY")
    call(r, "Rollback", "ROLLED_BACK_VERIFIED")
    call(r, "Verify", "VERIFIED_BEFORE", "-ExpectedState", "Before")
    managed(r, m, "before")
    assert protect(r, m) == protected

    for point in ("AfterFirstReplace", "BeforeReceipt", "CrashAfterFirstReplace", "CrashBeforeReceipt"):
        r, m = fixture(point)
        protected = protect(r, m)
        crashed = point.startswith("Crash")
        call(r, "Install", 72 if crashed else 1, "-FailurePoint", point)
        if crashed:
            call(r, "Recover", "RECOVERED_BEFORE")
        call(r, "Verify", "VERIFIED_BEFORE", "-ExpectedState", "Before")
        managed(r, m, "before")
        assert protect(r, m) == protected

    r, m = fixture("interrupted_rollback")
    protected = protect(r, m)
    call(r, "Install", "INSTALLED_VERIFIED")
    call(r, "Rollback", 72, "-FailurePoint", "CrashAfterFirstRollback")
    call(r, "Recover", "RECOVERED_AFTER")
    call(r, "Verify", "VERIFIED_AFTER")
    managed(r, m, "after")
    assert protect(r, m) == protected

    r, m = fixture("game_running")
    protected = protect(r, m)
    call(r, "Install", 1, "-FixtureProcesses", "Cyberpunk2077")
    managed(r, m, "before")
    assert not (r / "recovery").exists() and protect(r, m) == protected
    r, m = fixture("wrong_file")
    bad = r / "game" / ALLOWED[0]
    put(bad, b"Unexpected local edit")
    call(r, "Install", 1)
    assert bad.read_bytes() == b"Unexpected local edit" and not (r / "recovery").exists()

    output = HERE / "fixture_results.json"
    write(output, {"status": "PASS_ML1_JB4_ONE_ARCHIVE_DEPLOYMENT_FIXTURES", "installer_sha256": sha(INSTALLER),
                   "manifest_sha256": sha(manifest_path), "scope": str(root), "actions": actions,
                   "notes": "Exact full Core51 normal install and rollback. Other cases use synthetic fixture files."})
    write(HERE / "readiness.json", {
        "status": "READY_NOT_INSTALLED", "installer_sha256": sha(INSTALLER), "manifest_sha256": sha(manifest_path),
        "fixture_result": output.name, "fixture_result_sha256": sha(output),
        "independent_review": "installer_review.json", "independent_review_sha256": sha(HERE / "installer_review.json"),
    })
    print(f"PASS: {len(actions)} actions across eight isolated fixtures")


if __name__ == "__main__":
    main()
