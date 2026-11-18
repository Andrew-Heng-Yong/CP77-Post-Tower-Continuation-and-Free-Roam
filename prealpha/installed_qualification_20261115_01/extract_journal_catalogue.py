"""Extract selected quest roots and map-pin paths from exact installed PTFR sources."""

import hashlib
import json
import re
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parent.parent
MANIFEST = WORKSPACE / "prealpha/mid_quest_resume_retire_20261115_01/stage_08/deployment_01/installed_manifest_01.json"
KEEP_CLASSES = {"gameJournalQuest", "gameJournalQuestMapPin"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def installed_source(manifest: dict, relative: str) -> Path:
    matches = [row for row in manifest["core_files"] if row["path"] == relative]
    if len(matches) != 1:
        raise ValueError(f"Missing installed source: {relative}")
    path = Path(manifest["game_root"]) / relative
    if path.is_symlink() or not path.is_file() or digest(path) != matches[0]["sha256"]:
        raise ValueError(f"Installed source drift: {relative}")
    return path


def metadata_rows(source: str) -> list[dict]:
    expression = re.compile(r'private static func MetadataJSON\d+\(\) -> String \{ return "((?:\\.|[^"\\])*)"; \}')
    rows = [json.loads(json.loads('"' + match.group(1) + '"')) for match in expression.finditer(source)]
    if len(rows) != 158 or len({row["id"] for row in rows}) != 158:
        raise ValueError("Historical snapshot catalogue differs from 158 unique entries")
    return [
        {
            "id": row["id"],
            "title": row["title"],
            "source": "installed_history_snapshot",
            "journals": [{"path": path, "class": kind} for path, kind in row["journals"] if kind in KEEP_CLASSES],
        }
        for row in rows
    ]


def s30_rows(source: str) -> list[dict]:
    sections = source.split("public abstract class SideJobDataS30 {", 1)
    if len(sections) != 2:
        raise ValueError("Missing S30 data class")
    source = sections[1]
    names = [
        ("mq006_rollercoaster", "Love Rollercoaster"),
        ("mws_se5_07", "Shape of a Pony"),
        ("mws_wat_08_trauma_drama", "Career Opportunities"),
    ]
    rows = []
    for index, (identifier, title) in enumerate(names):
        arrays = []
        for method in ("Paths", "Classes"):
            expression = rf'public static func {method}{index}\(\) -> array<String> \{{ return (\[[^\n]*?\]); \}}'
            matches = re.findall(expression, source)
            if len(matches) != 1:
                raise ValueError(f"Missing S30 {method}{index}")
            arrays.append(json.loads(matches[0]))
        paths, classes = arrays
        if len(paths) != len(classes) or not paths[0].endswith("/" + identifier):
            raise ValueError(f"S30 path/class drift: {identifier}")
        rows.append(
            {
                "id": identifier,
                "title": title,
                "source": "installed_s30",
                "journals": [{"path": path, "class": kind} for path, kind in zip(paths, classes) if kind in KEEP_CLASSES],
            }
        )
    return rows


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: extract_journal_catalogue.py FRESH_OUTPUT_JSON")
    output = Path(sys.argv[1]).resolve()
    if output.exists() or HERE not in output.parents or not output.parent.is_dir():
        raise ValueError("Output must be a fresh file under this task directory")
    manifest = json.loads(MANIFEST.read_bytes())
    if manifest["core_epoch"] != "RD10_MID_QUEST_RESUME_RETIRED":
        raise ValueError("Wrong installed baseline")
    history = installed_source(manifest, "r6/scripts/PTFR_Consolidated/PTFR_HistorySnapshotHS1.reds")
    sidejobs = installed_source(manifest, "r6/scripts/PTFR_Consolidated/PTFR_SideJobsS29.reds")
    entries = metadata_rows(history.read_text(encoding="utf-8-sig")) + s30_rows(sidejobs.read_text(encoding="utf-8-sig"))
    if len(entries) != 161 or len({row["id"] for row in entries}) != 161:
        raise ValueError("Combined selected entry count drift")
    paths = {}
    for entry in entries:
        for row in entry["journals"]:
            previous = paths.setdefault(row["path"], row["class"])
            if previous != row["class"]:
                raise ValueError(f"Journal class conflict: {row['path']}")
    output.write_text(
        json.dumps(
            {
                "status": "EXACT_INSTALLED_SOURCE_CATALOGUE",
                "manifest_sha256": digest(MANIFEST),
                "history_sha256": digest(history),
                "sidejobs_sha256": digest(sidejobs),
                "entry_count": len(entries),
                "unique_journal_paths": len(paths),
                "map_pin_paths": sum(kind == "gameJournalQuestMapPin" for kind in paths.values()),
                "entries": entries,
                "limits": ["Selected entries only", "Journal path presence is not an executing owner or rendered map icon"],
            },
            indent=2,
            ensure_ascii=False,
        ) + "\n",
        encoding="utf-8",
    )
    print(f"Catalogued {len(entries)} entries and {sum(kind == 'gameJournalQuestMapPin' for kind in paths.values())} map-pin paths.")


if __name__ == "__main__":
    main()
