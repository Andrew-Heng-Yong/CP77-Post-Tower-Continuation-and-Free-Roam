"""Summarize embedded local gig phases in the expanded district roots; read-only."""
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research/gig_restoration"
SOURCES = BASE / "expanded_sources/json"
ANALYSIS = json.loads((BASE / "expanded_analysis/analysis.json").read_text(encoding="utf-8"))
TITLES = {q["id"]: q["title"] for q in json.loads(
    (BASE / "journal_titles.json").read_text(encoding="utf-8"))["quests"]}


def main():
    groups = defaultdict(lambda: {"phase_resources": [], "nodes": []})
    for path in SOURCES.rglob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        resource = str(path.relative_to(SOURCES))[:-5].replace("/", "\\")
        for index, embedded in enumerate(data["Data"].get("EmbeddedFiles", [])):
            phase = embedded["FileName"]["$value"]
            match = re.search(r"(sts_[a-z]{3}_[a-z]{3}_\d+)\\", phase)
            if not match:
                continue
            row = groups[match[1]]
            row["phase_resources"].append(phase)
            prefix = resource + "::Data.EmbeddedFiles." + str(index) + "."
            row["nodes"].extend(node for node in ANALYSIS["nodes"]
                                if node["graph"].startswith(prefix))
    out = []
    for gid, row in sorted(groups.items()):
        facts = sorted({value for node in row["nodes"] for key, value in node["details"].items()
                        if "factName" in key and isinstance(value, str)})
        scenes = sorted({value for node in row["nodes"] for key, value in node["details"].items()
                         if key == "sceneFile.DepotPath" and value != "0"})
        out.append({"id": gid, "title": TITLES.get(gid), "phases": row["phase_resources"],
                    "node_count": len(row["nodes"]), "facts": facts, "scenes": scenes,
                    "start_finish_failure_names": [name for name in facts
                                                    if any(part in name for part in ("start", "finish", "fail"))],
                    "external_story_facts": [name for name in facts if name.startswith(("q", "sq", "mq"))]})
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
