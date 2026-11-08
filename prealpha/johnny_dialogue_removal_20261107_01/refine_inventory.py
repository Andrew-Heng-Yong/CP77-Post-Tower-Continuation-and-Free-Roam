"""Reconcile structured XL bindings and resource literals with the initial census."""

import hashlib
import json
import re
from pathlib import Path


TASK = Path(__file__).resolve().parent
OUTPUT = TASK / "step1_01"
RESOURCE_LITERAL = re.compile(
    r"(?<![A-Za-z0-9_.\\-])"
    r"(?P<depot>(?:[A-Za-z0-9_.-]+\\)+[A-Za-z0-9_.-]+\."
    r"(?:questphase|scene|quest|gamedef|ent|app|streamingblock|streamingsector|workspot))"
    r"(?![A-Za-z0-9_.\\-])"
)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path, data):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, indent=2, ensure_ascii=False)
        stream.write("\n")


def main():
    entries = read_json(OUTPUT / "entry_sources.json")
    queries = read_json(OUTPUT / "queries.json")
    structured = read_json(OUTPUT / "registrations_structured.json")
    if structured["errors"]:
        raise SystemExit("Resolve structured registration errors before reconciliation")
    references = []
    for record in entries["source_files"]:
        path = Path(record["path"])
        with path.open("rb") as stream:
            actual_hash = hashlib.file_digest(stream, "sha256").hexdigest().upper()
        if actual_hash != record["sha256"]:
            raise SystemExit(f"Source changed during reconciliation {path}")
        for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
            for match in RESOURCE_LITERAL.finditer(line.replace("\\\\", "\\")):
                references.append({"path": str(path), "line": number, "depot": match["depot"]})

    initial_literals = {row["depot"] for row in entries["literal_resource_references"]}
    corrected_literals = {row["depot"] for row in references}
    registered_roots = {row["binding"]["path"] for row in structured["phase_bindings"]}
    parents = {row["binding"]["parent"] for row in structured["phase_bindings"]}
    wanted = (
        {row["depot"] for row in queries["private"]}
        | corrected_literals | registered_roots | parents
    )
    initial_wanted = set(queries["wanted"])
    initial_binding_keys = {
        (row["file"], row["path"], row["parent"], row["input_node"], row["source_socket"])
        for row in entries["xl_phase_bindings"]
    }
    structured_binding_keys = set()
    for row in structured["phase_bindings"]:
        binding = row["binding"]
        entry = binding.get("input", {})
        if isinstance(entry, dict) and "node" in entry and "socket" in entry:
            nodes = ", ".join(entry["node"])
            structured_binding_keys.add(
                (row["file"], binding["path"], binding["parent"], nodes, entry["socket"])
            )
    lost = sorted(initial_binding_keys - structured_binding_keys)
    if lost:
        raise SystemExit(f"Structured parser lost {len(lost)} previously parsed bindings")
    write_json(OUTPUT / "refinement.json", {
        "schema": 1,
        "status": "STRUCTURED_BINDINGS_AND_LITERAL_PATHS_RECONCILED",
        "initial_phase_bindings": len(entries["xl_phase_bindings"]),
        "structured_phase_bindings": len(structured["phase_bindings"]),
        "structured_phase_errors": structured["errors"],
        "initial_bindings_preserved": len(initial_binding_keys),
        "literal_resource_references": references,
        "wanted": sorted(wanted),
        "additional_queries": sorted(wanted - initial_wanted),
        "superseded_partial_literal_candidates": sorted(initial_literals - corrected_literals),
        "attachment_only_parents": sorted(parents),
        "reason": "The initial lexical pattern truncated paths with hyphenated directory names. Structured YAML also resolves connection-form phase registrations.",
    })
    print(json.dumps({
        "structured_bindings": len(structured["phase_bindings"]),
        "additional_queries": len(wanted - initial_wanted),
        "superseded_partial_candidates": len(initial_literals - corrected_literals),
        "initial_bindings_preserved": len(initial_binding_keys),
    }))


if __name__ == "__main__":
    main()
