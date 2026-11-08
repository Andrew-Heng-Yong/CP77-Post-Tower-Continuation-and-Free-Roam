"""Read-only final QR9 comparison against its captured immutable/external baseline."""
from pathlib import Path
import argparse
import concurrent.futures
import datetime
import hashlib
import subprocess
import sys

W = Path(__file__).resolve().parents[2]
H = Path(__file__).resolve().parent
sys.path.insert(0, str(W / "tools/parity_audit"))
from common import read, write, sha, tree_metadata


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True)
    a = ap.parse_args()
    out = (H / a.output).resolve()
    assert out.is_relative_to(H) and not out.exists(), "Fresh QR9 output required"
    out.mkdir(parents=True)
    base = read(H / "baseline.json")
    protected = read(H / "protection_before.json")
    assert sha(H / "protection_before.json") == base["protected_state"]["sha256"]

    def check(item):
        p, row = item
        actual = sha(p) if Path(p).is_file() else None
        return None if actual == row["sha256"] else {"path": p, "expected": row["sha256"], "actual": actual}

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        differences = [x for x in pool.map(check, protected["files"].items()) if x]

    def delta(before, after):
        return [{"path": p, "before": before.get(p), "after": after.get(p)}
                for p in sorted(set(before) | set(after)) if before.get(p) != after.get(p)]

    game = tree_metadata(base["game_root"])
    saves = tree_metadata(base["save_root"])
    gd = delta(protected["game_metadata"], game)
    sd = delta(protected["save_metadata"], saves)
    old = read(H / "workspace_before.json")
    git = ["git", "-c", "safe.directory=" + str(W).replace("\\", "/")]
    head = subprocess.check_output(git + ["rev-parse", "HEAD"], cwd=W, text=True).strip()
    branch = subprocess.check_output(git + ["branch", "--show-current"], cwd=W, text=True).strip()
    diff = hashlib.sha256(subprocess.check_output(git + ["diff", "--binary"], cwd=W)).hexdigest().upper()
    write(out / "discrepancies.json", {"protected_hashes": differences, "game_metadata": gd, "save_metadata": sd})
    result = {"status": "PASS" if not (differences or gd or sd) and head == old["head"] and branch == old["branch"] and diff == old["tracked_diff_sha256"] else "FAIL",
        "captured_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "protected_sha256_files": len(protected["files"]), "protected_hash_differences": len(differences),
        "whole_game_metadata_files": len(game), "whole_save_metadata_files": len(saves),
        "game_metadata_differences": len(gd), "save_metadata_differences": len(sd),
        "branch": branch, "head": head, "tracked_diff_unchanged": diff == old["tracked_diff_sha256"],
        "tracked_diff_sha256": diff, "source_epoch": "QR8:02 unchanged",
        "real_installs": 0, "real_rollbacks": 0, "game_launches": 0, "CUA_calls": 0, "save_writes": 0,
        "scope": "All named protected files SHA checked; complete game/save filenames, sizes and mtimes compared. Not a SHA of every unlisted multi-GB game file. QR9 fixture/addon source outputs are workspace-only."}
    write(out / "result.json", result)
    print({k: result[k] for k in ["status", "protected_sha256_files", "protected_hash_differences", "game_metadata_differences", "save_metadata_differences", "tracked_diff_unchanged"]})
    assert result["status"] == "PASS", result


if __name__ == "__main__":
    main()
