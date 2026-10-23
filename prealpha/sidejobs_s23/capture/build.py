"""Build a manual, read-only CET progress capture for the entire R4 whitelist."""
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from catalog_activity_state_r3 import all_quests
from catalog_gig_rollout_r2 import walk


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def arrays(source, method):
    match = re.search(r"public static func " + re.escape(method) + r"\([^)]*\) -> array<String> \{(.*?)\n  \}", source, re.S)
    assert match, method
    return match.group(1)


def direct_array(source, method):
    body = arrays(source, method)
    match = re.search(r"return (\[.*?\]);", body, re.S)
    return json.loads(match.group(1)) if match else []


def indexed_arrays(source, method):
    body = arrays(source, method)
    return {int(i): json.loads(data) for i, data in re.findall(r"if i == (\d+) \{\s*return (\[.*?\]);\s*\}", body, re.S)}


def build(revision):
    assert re.fullmatch(r"capture_\d{2}", revision)
    out = HERE / "build" / revision
    assert not out.exists(), "Immutable build exists"
    donor = ROOT / "prealpha/sidejobs_s22/runtime_v2/SideJobsS2.reds"
    assert sha(donor) == "58F134FFE6CCD8DF0AF30FCCABBFD161BBBCC8AEF75E25C16D18303992134295"
    source = donor.read_text(encoding="utf-8-sig").split("public abstract class SideJobFailureDataS21 {")[1].split("public abstract class SideJobDataS2 {")[0]
    ids = direct_array(source, "IDs")
    titles = direct_array(source, "Titles")
    roots = direct_array(source, "Paths")
    paths = indexed_arrays(source, "DetailPaths")
    classes = indexed_arrays(source, "DetailClasses")
    inventory_path = ROOT / "research/sidejobs_s21_failed/inventory_02.json"
    inventory = read(inventory_path)["jobs"]
    assert ids == [j["id"] for j in inventory] and len(ids) == len(set(ids)) == 58
    assert len(titles) == len(roots) == 58
    supplement_path = ROOT / "research/sidejobs_s22/ep1_jobs/mq306_details_01.json"
    supplement = read(supplement_path)
    cooked_path = ROOT / "research/gig_restoration/journal_sources/json/base/journal/cooked_journal.journal.json"
    cooked = {j["id"]: j for j in all_quests(cooked_path, {})}
    missing_sources = list((ROOT / "research/sidejobs_s23/native_01/json/base/quest/minor_quests").rglob("*.json"))
    assert missing_sources, "Extract missing native sources first"
    extra_facts = {}
    for prefix in ["mq015", "mq026"]:
        related = [p for p in missing_sources if f"/{prefix}/" in str(p).replace("\\", "/")]
        assert related, prefix
        extra_facts[prefix] = sorted({obj["factName"] for p in related for obj in walk(read(p)) if isinstance(obj.get("factName"), str) and re.fullmatch(r"[A-Za-z0-9_]+", obj["factName"])})
    rows = []
    for i, ident in enumerate(ids):
        assert roots[i] == inventory[i]["journal_path"]
        entry_paths, entry_classes = paths.get(i, []), classes.get(i, [])
        assert len(entry_paths) == len(entry_classes)
        journals = dict(zip(entry_paths, entry_classes))
        journals[roots[i]] = "gameJournalQuest"
        facts = direct_array(source, "FactNames" + str(i)) if i < 55 else []
        if ident == "mq306_dumpster":
            journals.update({j["path"]: j["class"] for j in supplement["journals"]})
            facts = sorted(set(facts + supplement["fact_names"]))
        if ident in ["mq015_wizardbook", "mq026_conspiracy"]:
            assert cooked[ident]["journal_path"] == roots[i]
            journals.update({j["path"]: j["className"] for j in cooked[ident]["journal_entries"]})
            facts = extra_facts[ident.split("_")[0]]
        rows.append({"id": ident, "title": titles[i], "root": roots[i],
                     "journals": [{"path": p, "class": c} for p, c in sorted(journals.items())], "facts": facts,
                     "coverage": "root_only" if len(journals) == 1 else "catalogued_native_detail"})
    assert all(re.fullmatch(r"[A-Za-z0-9_]+", f) for row in rows for f in row["facts"])
    context = ["PostTowerFreeRoamActive", "PTFRPA2_Finished", "PTFRPA2_Fault", "PTFRP0_DR13", "q307_done", "q307_finished", "q307_2079", "q307_active", "q307_main_game_killed", "q307_ep1_killed", "PTFRU9_Support_Issued", "PTFRU9_Support_Fault", "PTFRS22_SQ025_SupportReady", "PTFRS22_SQ025_SupportIssued", "PTFRS22_SQ025_Entered"]
    data = {"schema": 1, "kind": "S23_READ_ONLY_WHITELIST_CAPTURE", "jobs": rows, "context_facts": context}
    out.mkdir(parents=True)
    (out / "data.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    shutil.copy2(HERE / "init.lua", out / "init.lua")
    pins = [Path(__file__), HERE / "init.lua", donor, inventory_path, supplement_path, cooked_path,
            ROOT / "tools/catalog_activity_state_r3.py", ROOT / "tools/catalog_gig_rollout_r2.py"] + missing_sources
    for name, expected in supplement["source_pins"].items():
        path = ROOT / name
        assert sha(path) == expected
        pins.append(path)
    manifest = {"status": "BUILT_READ_ONLY_CAPTURE_NOT_RESTORATION", "schema": 1,
                "jobs": len(rows), "journals": sum(len(r["journals"]) for r in rows), "facts": sum(len(r["facts"]) for r in rows),
                "root_only": [r["id"] for r in rows if r["coverage"] == "root_only"],
                "automatic_callbacks": 0, "native_writes": 0, "save_writes": 0,
                "files": {name: sha(out / name) for name in ["init.lua", "data.json"]},
                "source_pins": {str(p.relative_to(ROOT)).replace("\\", "/"): sha(p) for p in pins}}
    (out / "build.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: manifest[k] for k in ["status", "jobs", "journals", "facts", "root_only"]}))


if __name__ == "__main__":
    build(sys.argv[1])
